"""
MCP Server exposing CheckPoint database query tools.
Runs over stdio transport — launched as a subprocess by chatbot.py.
"""

import json
import pyodbc
from mcp.server.fastmcp import FastMCP
from config import get_connection_string

mcp = FastMCP("checkpoint-db")


def _conn():
    return pyodbc.connect(get_connection_string())


def _rows_to_dicts(cursor) -> list[dict]:
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _serialize(rows: list[dict]) -> str:
    """JSON-serialize rows, converting non-serializable types."""
    def default(obj):
        from datetime import datetime, date
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)
    return json.dumps(rows, indent=2, default=default)


# ── Tools ─────────────────────────────────────────────────


@mcp.tool()
def get_departments() -> str:
    """Get all departments with employee counts."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.Id, d.Name,
               COUNT(u.Id) AS EmployeeCount
        FROM Departments d
        LEFT JOIN Users u ON u.DepartmentId = d.Id AND u.IsActive = 1
        GROUP BY d.Id, d.Name
        ORDER BY d.Name
    """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_employees(department_name: str = "") -> str:
    """Get employees, optionally filtered by department name.
    Pass an empty string or omit to get all employees."""
    conn = _conn()
    cur = conn.cursor()
    if department_name:
        cur.execute("""
            SELECT u.Id, u.FullName, u.Email, u.PhoneNumber,
                   r.Name AS Role, d.Name AS Department,
                   u.LeaveBalance, u.IsActive
            FROM Users u
            JOIN Roles r ON r.Id = u.RoleId
            JOIN Departments d ON d.Id = u.DepartmentId
            WHERE d.Name LIKE ? AND u.IsActive = 1
            ORDER BY u.FullName
        """, f"%{department_name}%")
    else:
        cur.execute("""
            SELECT u.Id, u.FullName, u.Email, u.PhoneNumber,
                   r.Name AS Role, d.Name AS Department,
                   u.LeaveBalance, u.IsActive
            FROM Users u
            JOIN Roles r ON r.Id = u.RoleId
            JOIN Departments d ON d.Id = u.DepartmentId
            WHERE u.IsActive = 1
            ORDER BY u.FullName
        """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_employee_details(employee_name: str) -> str:
    """Get detailed information about a specific employee by name (partial match)."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.Id, u.FullName, u.Email, u.PhoneNumber,
               r.Name AS Role, d.Name AS Department,
               u.LeaveBalance, u.IsActive, u.CreatedAt
        FROM Users u
        JOIN Roles r ON r.Id = u.RoleId
        JOIN Departments d ON d.Id = u.DepartmentId
        WHERE u.FullName LIKE ?
    """, f"%{employee_name}%")
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_leave_requests(status: str = "") -> str:
    """Get leave requests. Optionally filter by status: Pending, Approved, Rejected."""
    conn = _conn()
    cur = conn.cursor()
    status_map = {"pending": 1, "approved": 2, "rejected": 3}
    status_val = status_map.get(status.lower()) if status else None

    if status_val:
        cur.execute("""
            SELECT lr.Id, u.FullName AS Employee, d.Name AS Department,
                   lr.StartDate, lr.EndDate,
                   CASE lr.Type WHEN 1 THEN 'Vacation' WHEN 2 THEN 'Sick'
                        WHEN 3 THEN 'Personal' WHEN 4 THEN 'Maternity'
                        WHEN 5 THEN 'Paternity' WHEN 6 THEN 'Unpaid' END AS LeaveType,
                   CASE lr.Status WHEN 1 THEN 'Pending' WHEN 2 THEN 'Approved'
                        WHEN 3 THEN 'Rejected' END AS Status,
                   lr.Reason, m.FullName AS AssignedManager
            FROM LeaveRequests lr
            JOIN Users u ON u.Id = lr.UserId
            JOIN Departments d ON d.Id = u.DepartmentId
            LEFT JOIN Users m ON m.Id = lr.AssignedManagerId
            WHERE lr.Status = ?
            ORDER BY lr.CreatedAt DESC
        """, status_val)
    else:
        cur.execute("""
            SELECT lr.Id, u.FullName AS Employee, d.Name AS Department,
                   lr.StartDate, lr.EndDate,
                   CASE lr.Type WHEN 1 THEN 'Vacation' WHEN 2 THEN 'Sick'
                        WHEN 3 THEN 'Personal' WHEN 4 THEN 'Maternity'
                        WHEN 5 THEN 'Paternity' WHEN 6 THEN 'Unpaid' END AS LeaveType,
                   CASE lr.Status WHEN 1 THEN 'Pending' WHEN 2 THEN 'Approved'
                        WHEN 3 THEN 'Rejected' END AS Status,
                   lr.Reason, m.FullName AS AssignedManager
            FROM LeaveRequests lr
            JOIN Users u ON u.Id = lr.UserId
            JOIN Departments d ON d.Id = u.DepartmentId
            LEFT JOIN Users m ON m.Id = lr.AssignedManagerId
            ORDER BY lr.CreatedAt DESC
        """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_events() -> str:
    """Get all upcoming company events."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.Id, e.Title, e.[Description],
               CASE e.Type WHEN 1 THEN 'Meeting' WHEN 2 THEN 'Training'
                    WHEN 3 THEN 'Workshop' WHEN 4 THEN 'Conference'
                    WHEN 5 THEN 'Social' WHEN 6 THEN 'Announcement'
                    WHEN 7 THEN 'Other' END AS EventType,
               r.Name AS RoomName, e.StartDateTime, e.EndDateTime,
               u.FullName AS CreatedBy, e.IsMandatory, e.RSVPEnabled
        FROM Events e
        LEFT JOIN Rooms r ON r.Id = e.RoomId
        JOIN Users u ON u.Id = e.CreatedByUserId
        ORDER BY e.StartDateTime
    """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_rooms() -> str:
    """Get all rooms with their type and capacity."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.Id, r.Name,
               CASE r.Type WHEN 1 THEN 'Meeting' WHEN 2 THEN 'Conference'
                    WHEN 3 THEN 'Training' WHEN 4 THEN 'Break'
                    WHEN 5 THEN 'Office' WHEN 6 THEN 'Other' END AS RoomType,
               r.Capacity, r.IsActive
        FROM Rooms r
        ORDER BY r.Name
    """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_announcements() -> str:
    """Get all active company announcements."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.Id, a.Title, a.Content,
               u.FullName AS CreatedBy, a.CreatedAt, a.IsActive
        FROM Announcements a
        JOIN Users u ON u.Id = a.CreatedById
        WHERE a.IsActive = 1
        ORDER BY a.CreatedAt DESC
    """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_general_requests(status: str = "") -> str:
    """Get general/support requests. Optionally filter by status: Pending, Approved, Rejected, InProgress, Resolved."""
    conn = _conn()
    cur = conn.cursor()
    status_map = {"pending": 1, "approved": 2, "rejected": 3, "inprogress": 4, "resolved": 5}
    status_val = status_map.get(status.lower().replace(" ", "")) if status else None

    if status_val:
        cur.execute("""
            SELECT gr.Id, u.FullName AS RequestedBy, gr.Title, gr.[Description],
                   CASE gr.Category WHEN 1 THEN 'HR' WHEN 2 THEN 'IT' WHEN 3 THEN 'Admin'
                        WHEN 4 THEN 'Finance' WHEN 5 THEN 'Facilities'
                        WHEN 6 THEN 'Other' END AS Category,
                   CASE gr.Status WHEN 1 THEN 'Pending' WHEN 2 THEN 'Approved'
                        WHEN 3 THEN 'Rejected' WHEN 4 THEN 'InProgress'
                        WHEN 5 THEN 'Resolved' END AS Status,
                   a.FullName AS AssignedTo, gr.CreatedAt
            FROM GeneralRequests gr
            JOIN Users u ON u.Id = gr.UserId
            LEFT JOIN Users a ON a.Id = gr.AssignedToUserId
            WHERE gr.Status = ?
            ORDER BY gr.CreatedAt DESC
        """, status_val)
    else:
        cur.execute("""
            SELECT gr.Id, u.FullName AS RequestedBy, gr.Title, gr.[Description],
                   CASE gr.Category WHEN 1 THEN 'HR' WHEN 2 THEN 'IT' WHEN 3 THEN 'Admin'
                        WHEN 4 THEN 'Finance' WHEN 5 THEN 'Facilities'
                        WHEN 6 THEN 'Other' END AS Category,
                   CASE gr.Status WHEN 1 THEN 'Pending' WHEN 2 THEN 'Approved'
                        WHEN 3 THEN 'Rejected' WHEN 4 THEN 'InProgress'
                        WHEN 5 THEN 'Resolved' END AS Status,
                   a.FullName AS AssignedTo, gr.CreatedAt
            FROM GeneralRequests gr
            JOIN Users u ON u.Id = gr.UserId
            LEFT JOIN Users a ON a.Id = gr.AssignedToUserId
            ORDER BY gr.CreatedAt DESC
        """)
    result = _serialize(_rows_to_dicts(cur))
    conn.close()
    return result


@mcp.tool()
def get_statistics() -> str:
    """Get overall company statistics: user counts, request counts, event counts, etc."""
    conn = _conn()
    cur = conn.cursor()

    stats = {}
    cur.execute("SELECT COUNT(*) FROM Users WHERE IsActive = 1")
    stats["total_active_employees"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Departments")
    stats["total_departments"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Rooms WHERE IsActive = 1")
    stats["total_active_rooms"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Events")
    stats["total_events"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM LeaveRequests WHERE Status = 1")
    stats["pending_leave_requests"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM GeneralRequests WHERE Status = 1")
    stats["pending_general_requests"] = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Announcements WHERE IsActive = 1")
    stats["active_announcements"] = cur.fetchone()[0]

    conn.close()
    return json.dumps(stats, indent=2)


if __name__ == "__main__":
    mcp.run()
