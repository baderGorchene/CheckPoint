"""
Seed mock data into CheckPoint_DB.
Run AFTER the .NET app has created the database schema (via EnsureCreatedAsync).
Usage: python seed_data.py
"""

import pyodbc
import bcrypt
from datetime import datetime, timedelta
from config import get_connection_string


def get_connection():
    return pyodbc.connect(get_connection_string())


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=11)).decode()


def seed_users(cursor):
    cursor.execute("SELECT COUNT(*) FROM Users")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  Users already exist. Skipping.")
        return

    pw = hash_password("Password123!")
    users = [
        # (FullName, Email, Phone, PasswordHash, RoleId, DeptId, LeaveBalance, IsActive)
        ("Mouayad Admin",       "admin@checkpoint.com",           "+213555000001", pw, 3, 1, 30, True),
        ("Sarah Bencherif",     "sarah.bencherif@checkpoint.com", "+213555000002", pw, 2, 2, 25, True),
        ("Ahmed Benali",        "ahmed.benali@checkpoint.com",    "+213555000003", pw, 2, 1, 25, True),
        ("Fatima Zahra",        "fatima.zahra@checkpoint.com",    "+213555000004", pw, 1, 1, 20, True),
        ("Youssef Amrani",      "youssef.amrani@checkpoint.com",  "+213555000005", pw, 1, 2, 18, True),
        ("Nadia Boudiaf",       "nadia.boudiaf@checkpoint.com",   "+213555000006", pw, 1, 3, 22, True),
        ("Karim Hadj",          "karim.hadj@checkpoint.com",      "+213555000007", pw, 1, 4, 15, True),
        ("Amina Khelifi",       "amina.khelifi@checkpoint.com",   "+213555000008", pw, 1, 1, 20, True),
        ("Omar Benmoussa",      "omar.benmoussa@checkpoint.com",  "+213555000009", pw, 1, 3, 12, True),
        ("Lina Cherif",         "lina.cherif@checkpoint.com",     "+213555000010", pw, 1, 2, 19, True),
    ]

    for u in users:
        cursor.execute(
            """INSERT INTO Users
               (FullName, Email, PhoneNumber, PasswordHash, RoleId, DepartmentId, LeaveBalance, IsActive, CreatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE())""",
            u,
        )
    print(f"  ✅ Seeded {len(users)} users.")


def seed_events(cursor):
    cursor.execute("SELECT COUNT(*) FROM Events")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  Events already exist. Skipping.")
        return

    cursor.execute("SELECT TOP 3 Id FROM Rooms ORDER BY Id")
    room_ids = [r[0] for r in cursor.fetchall()]
    r1 = room_ids[0] if len(room_ids) > 0 else None
    r2 = room_ids[1] if len(room_ids) > 1 else None
    r3 = room_ids[2] if len(room_ids) > 2 else None

    # (Title, Desc, Type, RoomId, Start, End, CreatedByUserId, IsMandatory, RSVPEnabled)
    events = [
        ("Q3 Planning Meeting",    "Quarterly planning session for department heads.",         1, r1, "2026-06-01 09:00", "2026-06-01 11:00", 1, 1, 1),
        ("Cybersecurity Workshop", "Mandatory security awareness training for all employees.", 3, r3, "2026-06-05 14:00", "2026-06-05 16:00", 3, 1, 0),
        ("Team Building Lunch",    "Monthly social lunch — all are welcome!",                 5, r2, "2026-06-10 12:00", "2026-06-10 14:00", 1, 0, 1),
        ("New Hire Onboarding",    "Onboarding for June 2026 hires.",                         2, r3, "2026-06-15 09:00", "2026-06-15 17:00", 2, 1, 0),
        ("Year-End Review Prep",   "Preparation meeting for annual performance reviews.",     1, r1, "2026-06-20 10:00", "2026-06-20 12:00", 3, 0, 1),
    ]

    for ev in events:
        cursor.execute(
            """INSERT INTO Events
               (Title, [Description], Type, RoomId, StartDateTime, EndDateTime,
                CreatedByUserId, IsMandatory, RSVPEnabled, CreatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE())""",
            ev,
        )
    print(f"  ✅ Seeded {len(events)} events.")


def seed_leave_requests(cursor):
    cursor.execute("SELECT COUNT(*) FROM LeaveRequests")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  LeaveRequests already exist. Skipping.")
        return

    # (UserId, StartDate, EndDate, Type, Status, Reason, AssignedManagerId)
    leaves = [
        (4, "2026-05-20", "2026-05-22", 1, 2, "Family vacation trip.",              3),
        (5, "2026-05-25", "2026-05-25", 2, 1, "Feeling unwell, need rest.",         2),
        (6, "2026-06-01", "2026-06-05", 1, 1, "Summer holiday planned in advance.", 3),
        (7, "2026-05-18", "2026-05-19", 3, 3, "Personal errand.",                   3),
        (8, "2026-06-10", "2026-06-12", 1, 2, "Wedding attendance.",                3),
        (9, "2026-05-28", "2026-05-30", 2, 1, "Doctor appointment + recovery.",     3),
    ]

    for lv in leaves:
        cursor.execute(
            """INSERT INTO LeaveRequests
               (UserId, StartDate, EndDate, Type, Status, Reason, AssignedManagerId, CreatedAt)
               VALUES (?, ?, ?, ?, ?, ?, ?, GETUTCDATE())""",
            lv,
        )
    print(f"  ✅ Seeded {len(leaves)} leave requests.")


def seed_announcements(cursor):
    cursor.execute("SELECT COUNT(*) FROM Announcements")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  Announcements already exist. Skipping.")
        return

    announcements = [
        ("Office Renovation Notice",
         "Floors 2-3 will undergo renovation from June 15-30. Please use Floor 1 facilities.",
         1, True),
        ("New Parking Policy",
         "Starting July 1, all employees must register their vehicles via the internal portal.",
         1, True),
        ("Ramadan Schedule Update",
         "During Ramadan, working hours will be 9:00 AM – 3:00 PM.",
         2, True),
    ]

    for ann in announcements:
        cursor.execute(
            """INSERT INTO Announcements
               (Title, Content, CreatedById, IsActive, CreatedAt)
               VALUES (?, ?, ?, ?, GETUTCDATE())""",
            ann,
        )
    print(f"  ✅ Seeded {len(announcements)} announcements.")


def seed_general_requests(cursor):
    cursor.execute("SELECT COUNT(*) FROM GeneralRequests")
    if cursor.fetchone()[0] > 0:
        print("  ⏭  GeneralRequests already exist. Skipping.")
        return

    # (UserId, Title, Description, Category, Status, AssignedToUserId)
    requests = [
        (4, "Laptop replacement",     "My laptop battery drains in 2 hours.",      2, 4, 3),
        (5, "Access card not working", "Badge doesn't open Floor 3 door.",          5, 1, 1),
        (7, "Salary slip missing",     "April 2026 pay slip not available online.", 4, 2, 2),
        (6, "Office chair broken",     "Armrest fell off, need replacement.",       5, 1, 1),
    ]

    for req in requests:
        cursor.execute(
            """INSERT INTO GeneralRequests
               (UserId, Title, [Description], Category, Status, AssignedToUserId, CreatedAt)
               VALUES (?, ?, ?, ?, ?, ?, GETUTCDATE())""",
            req,
        )
    print(f"  ✅ Seeded {len(requests)} general requests.")


def main():
    print("🌱 CheckPoint Mock Data Seeder")
    print("=" * 40)

    try:
        conn = get_connection()
    except pyodbc.Error as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure the .NET app has run at least once to create the schema.")
        return

    cursor = conn.cursor()

    try:
        seed_users(cursor)
        seed_events(cursor)
        seed_leave_requests(cursor)
        seed_announcements(cursor)
        seed_general_requests(cursor)
        conn.commit()
        print("\n🎉 All mock data seeded successfully!")
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Seeding failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
