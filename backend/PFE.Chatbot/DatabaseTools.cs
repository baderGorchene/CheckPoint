using System.ComponentModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.EntityFrameworkCore;
using PFE.Domain.Entities;
using PFE.Domain.Enums;
using PFE.Infrastructure.Data;

namespace PFE.Chatbot;

public class DatabaseTools
{
    private readonly ApplicationDbContext _context;
    private readonly JsonSerializerOptions _jsonOptions;

    public DatabaseTools(ApplicationDbContext context)
    {
        _context = context;
        _jsonOptions = new JsonSerializerOptions
        {
            WriteIndented = true,
            ReferenceHandler = ReferenceHandler.IgnoreCycles,
            Converters = { new JsonStringEnumConverter() }
        };
    }

    [Description("Get all departments with their active employee counts.")]
    public async Task<string> GetDepartmentsAsync()
    {
        var result = await _context.Departments
            .Select(d => new
            {
                d.Id,
                d.Name,
                EmployeeCount = _context.Users.Count(u => u.DepartmentId == d.Id && u.IsActive)
            })
            .OrderBy(d => d.Name)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get employees, optionally filtered by department name. Pass an empty string or omit to get all active employees.")]
    public async Task<string> GetEmployeesAsync(
        [Description("The name of the department to filter by (partial match). Pass empty string to skip filtering.")] string departmentName = "")
    {
        var query = _context.Users
            .Include(u => u.Role)
            .Include(u => u.Department)
            .Where(u => u.IsActive);

        if (!string.IsNullOrWhiteSpace(departmentName))
        {
            query = query.Where(u => u.Department.Name.Contains(departmentName));
        }

        var result = await query
            .Select(u => new
            {
                u.Id,
                u.FullName,
                u.Email,
                u.PhoneNumber,
                Role = u.Role.Name,
                Department = u.Department.Name,
                u.LeaveBalance,
                u.IsActive
            })
            .OrderBy(u => u.FullName)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get detailed information about a specific employee by name (partial match).")]
    public async Task<string> GetEmployeeDetailsAsync(
        [Description("The name of the employee to search for (partial match).")] string employeeName)
    {
        var result = await _context.Users
            .Include(u => u.Role)
            .Include(u => u.Department)
            .Where(u => u.FullName.Contains(employeeName))
            .Select(u => new
            {
                u.Id,
                u.FullName,
                u.Email,
                u.PhoneNumber,
                Role = u.Role.Name,
                Department = u.Department.Name,
                u.LeaveBalance,
                u.IsActive,
                u.CreatedAt
            })
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get leave requests. Optionally filter by status: Pending, Approved, Rejected.")]
    public async Task<string> GetLeaveRequestsAsync(
        [Description("Leave status filter: Pending, Approved, Rejected. Pass empty string to skip filtering.")] string status = "")
    {
        var query = _context.LeaveRequests
            .Include(lr => lr.User)
            .ThenInclude(u => u.Department)
            .Include(lr => lr.AssignedManager)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(status))
        {
            if (Enum.TryParse<RequestStatus>(status, true, out var statusEnum))
            {
                query = query.Where(lr => lr.Status == statusEnum);
            }
        }

        var result = await query
            .Select(lr => new
            {
                lr.Id,
                Employee = lr.User.FullName,
                Department = lr.User.Department.Name,
                lr.StartDate,
                lr.EndDate,
                LeaveType = lr.Type.ToString(),
                Status = lr.Status.ToString(),
                lr.Reason,
                AssignedManager = lr.AssignedManager != null ? lr.AssignedManager.FullName : "None"
            })
            .OrderByDescending(lr => lr.Id)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get all upcoming company events.")]
    public async Task<string> GetEventsAsync()
    {
        var result = await _context.Events
            .Include(e => e.Room)
            .Include(e => e.CreatedByUser)
            .Select(e => new
            {
                e.Id,
                e.Title,
                e.Description,
                EventType = e.Type.ToString(),
                RoomName = e.Room != null ? e.Room.Name : "Remote/None",
                e.StartDateTime,
                e.EndDateTime,
                CreatedBy = e.CreatedByUser.FullName,
                e.IsMandatory,
                e.RSVPEnabled
            })
            .OrderBy(e => e.StartDateTime)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get all conference, meeting, and training rooms.")]
    public async Task<string> GetRoomsAsync()
    {
        var result = await _context.Rooms
            .Select(r => new
            {
                r.Id,
                r.Name,
                RoomType = r.Type.ToString(),
                r.Capacity,
                r.IsActive
            })
            .OrderBy(r => r.Name)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get all active company announcements.")]
    public async Task<string> GetAnnouncementsAsync()
    {
        var result = await _context.Announcements
            .Include(a => a.CreatedBy)
            .Where(a => a.IsActive)
            .Select(a => new
            {
                a.Id,
                a.Title,
                a.Content,
                CreatedBy = a.CreatedBy.FullName,
                a.CreatedAt,
                a.IsActive
            })
            .OrderByDescending(a => a.CreatedAt)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get general support requests. Optionally filter by status: Pending, Approved, Rejected, InProgress, Resolved.")]
    public async Task<string> GetGeneralRequestsAsync(
        [Description("Request status filter: Pending, Approved, Rejected, InProgress, Resolved. Pass empty string to skip filtering.")] string status = "")
    {
        var query = _context.GeneralRequests
            .Include(gr => gr.User)
            .Include(gr => gr.AssignedTo)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(status))
        {
            if (Enum.TryParse<RequestStatus>(status, true, out var statusEnum))
            {
                query = query.Where(gr => gr.Status == statusEnum);
            }
        }

        var result = await query
            .Select(gr => new
            {
                gr.Id,
                RequestedBy = gr.User.FullName,
                gr.Title,
                gr.Description,
                Category = gr.Category.ToString(),
                Status = gr.Status.ToString(),
                AssignedTo = gr.AssignedTo != null ? gr.AssignedTo.FullName : "None",
                gr.CreatedAt
            })
            .OrderByDescending(gr => gr.CreatedAt)
            .ToListAsync();

        return JsonSerializer.Serialize(result, _jsonOptions);
    }

    [Description("Get overall company statistics: active employee count, department count, room count, event count, pending requests, active announcements.")]
    public async Task<string> GetStatisticsAsync()
    {
        var totalActiveEmployees = await _context.Users.CountAsync(u => u.IsActive);
        var totalDepartments = await _context.Departments.CountAsync();
        var totalActiveRooms = await _context.Rooms.CountAsync(r => r.IsActive);
        var totalEvents = await _context.Events.CountAsync();
        var pendingLeaveRequests = await _context.LeaveRequests.CountAsync(lr => lr.Status == RequestStatus.Pending);
        var pendingGeneralRequests = await _context.GeneralRequests.CountAsync(gr => gr.Status == RequestStatus.Pending);
        var activeAnnouncements = await _context.Announcements.CountAsync(a => a.IsActive);

        var stats = new
        {
            total_active_employees = totalActiveEmployees,
            total_departments = totalDepartments,
            total_active_rooms = totalActiveRooms,
            total_events = totalEvents,
            pending_leave_requests = pendingLeaveRequests,
            pending_general_requests = pendingGeneralRequests,
            active_announcements = activeAnnouncements
        };

        return JsonSerializer.Serialize(stats, _jsonOptions);
    }
}
