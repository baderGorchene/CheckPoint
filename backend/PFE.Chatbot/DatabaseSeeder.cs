using Microsoft.EntityFrameworkCore;
using PFE.Domain.Entities;
using PFE.Domain.Enums;
using PFE.Infrastructure.Data;

namespace PFE.Chatbot;

public static class DatabaseSeeder
{
    private static string HashPassword(string password)
    {
        return BCrypt.Net.BCrypt.HashPassword(password, workFactor: 11);
    }

    public static async Task SeedAllAsync(ApplicationDbContext context)
    {
        Console.WriteLine("🌱 Seeding Database...");

        // Ensure database exists and schema is updated
        await context.Database.EnsureCreatedAsync();

        // 1. Seed Departments if empty (fall back if DbSeeder didn't run)
        if (!await context.Departments.AnyAsync())
        {
            var depts = new List<Department>
            {
                new() { Name = "IT" },
                new() { Name = "HR" },
                new() { Name = "Finance" },
                new() { Name = "Operations" }
            };
            await context.Departments.AddRangeAsync(depts);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded Departments.");
        }

        // Get departments dictionary for mapping
        var departments = await context.Departments.ToDictionaryAsync(d => d.Name, d => d.Id);
        int itId = departments["IT"];
        int hrId = departments["HR"];
        int financeId = departments["Finance"];
        int opsId = departments["Operations"];

        // 2. Seed Rooms if empty
        if (!await context.Rooms.AnyAsync())
        {
            var rooms = new List<Room>
            {
                new() { Name = "Conference Room A", Type = RoomType.Conference, Capacity = 20, IsActive = true },
                new() { Name = "Meeting Room B", Type = RoomType.Meeting, Capacity = 10, IsActive = true },
                new() { Name = "Training Room", Type = RoomType.Training, Capacity = 30, IsActive = true }
            };
            await context.Rooms.AddRangeAsync(rooms);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded Rooms.");
        }

        var roomDict = await context.Rooms.ToDictionaryAsync(r => r.Name, r => r.Id);

        // 3. Seed Users
        if (!await context.Users.AnyAsync())
        {
            string pw = HashPassword("Password123!");
            var users = new List<User>
            {
                new() { FullName = "Mouayad Admin", Email = "admin@checkpoint.com", PhoneNumber = "+213555000001", PasswordHash = pw, RoleId = 3, DepartmentId = itId, LeaveBalance = 30, IsActive = true },
                new() { FullName = "Sarah Bencherif", Email = "sarah.bencherif@checkpoint.com", PhoneNumber = "+213555000002", PasswordHash = pw, RoleId = 2, DepartmentId = hrId, LeaveBalance = 25, IsActive = true },
                new() { FullName = "Ahmed Benali", Email = "ahmed.benali@checkpoint.com", PhoneNumber = "+213555000003", PasswordHash = pw, RoleId = 2, DepartmentId = itId, LeaveBalance = 25, IsActive = true },
                new() { FullName = "Fatima Zahra", Email = "fatima.zahra@checkpoint.com", PhoneNumber = "+213555000004", PasswordHash = pw, RoleId = 1, DepartmentId = itId, LeaveBalance = 20, IsActive = true },
                new() { FullName = "Youssef Amrani", Email = "youssef.amrani@checkpoint.com", PhoneNumber = "+213555000005", PasswordHash = pw, RoleId = 1, DepartmentId = hrId, LeaveBalance = 18, IsActive = true },
                new() { FullName = "Nadia Boudiaf", Email = "nadia.boudiaf@checkpoint.com", PhoneNumber = "+213555000006", PasswordHash = pw, RoleId = 1, DepartmentId = financeId, LeaveBalance = 22, IsActive = true },
                new() { FullName = "Karim Hadj", Email = "karim.hadj@checkpoint.com", PhoneNumber = "+213555000007", PasswordHash = pw, RoleId = 1, DepartmentId = opsId, LeaveBalance = 15, IsActive = true },
                new() { FullName = "Amina Khelifi", Email = "amina.khelifi@checkpoint.com", PhoneNumber = "+213555000008", PasswordHash = pw, RoleId = 1, DepartmentId = itId, LeaveBalance = 20, IsActive = true },
                new() { FullName = "Omar Benmoussa", Email = "omar.benmoussa@checkpoint.com", PhoneNumber = "+213555000009", PasswordHash = pw, RoleId = 1, DepartmentId = financeId, LeaveBalance = 12, IsActive = true },
                new() { FullName = "Lina Cherif", Email = "lina.cherif@checkpoint.com", PhoneNumber = "+213555000010", PasswordHash = pw, RoleId = 1, DepartmentId = hrId, LeaveBalance = 19, IsActive = true }
            };

            await context.Users.AddRangeAsync(users);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded Users.");
        }

        var usersDict = await context.Users.ToDictionaryAsync(u => u.FullName, u => u.Id);
        int adminId = usersDict["Mouayad Admin"];
        int sarahId = usersDict["Sarah Bencherif"];
        int ahmedId = usersDict["Ahmed Benali"];

        // 4. Seed Events
        if (!await context.Events.AnyAsync())
        {
            var r1 = roomDict["Conference Room A"];
            var r2 = roomDict["Meeting Room B"];
            var r3 = roomDict["Training Room"];

            var events = new List<Event>
            {
                new() { Title = "Q3 Planning Meeting", Description = "Quarterly planning session for department heads.", Type = EventType.Meeting, RoomId = r1, StartDateTime = DateTime.UtcNow.AddDays(14).Date.AddHours(9), EndDateTime = DateTime.UtcNow.AddDays(14).Date.AddHours(11), CreatedByUserId = adminId, IsMandatory = true, RSVPEnabled = true },
                new() { Title = "Cybersecurity Workshop", Description = "Mandatory security awareness training for all employees.", Type = EventType.Workshop, RoomId = r3, StartDateTime = DateTime.UtcNow.AddDays(18).Date.AddHours(14), EndDateTime = DateTime.UtcNow.AddDays(18).Date.AddHours(16), CreatedByUserId = ahmedId, IsMandatory = true, RSVPEnabled = false },
                new() { Title = "Team Building Lunch", Description = "Monthly social lunch — all are welcome!", Type = EventType.Social, RoomId = r2, StartDateTime = DateTime.UtcNow.AddDays(23).Date.AddHours(12), EndDateTime = DateTime.UtcNow.AddDays(23).Date.AddHours(14), CreatedByUserId = adminId, IsMandatory = false, RSVPEnabled = true },
                new() { Title = "New Hire Onboarding", Description = "Onboarding for June 2026 hires.", Type = EventType.Training, RoomId = r3, StartDateTime = DateTime.UtcNow.AddDays(28).Date.AddHours(9), EndDateTime = DateTime.UtcNow.AddDays(28).Date.AddHours(17), CreatedByUserId = sarahId, IsMandatory = true, RSVPEnabled = false },
                new() { Title = "Year-End Review Prep", Description = "Preparation meeting for annual performance reviews.", Type = EventType.Meeting, RoomId = r1, StartDateTime = DateTime.UtcNow.AddDays(33).Date.AddHours(10), EndDateTime = DateTime.UtcNow.AddDays(33).Date.AddHours(12), CreatedByUserId = ahmedId, IsMandatory = false, RSVPEnabled = true }
            };

            await context.Events.AddRangeAsync(events);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded Events.");
        }

        // 5. Seed LeaveRequests
        if (!await context.LeaveRequests.AnyAsync())
        {
            var leaves = new List<LeaveRequest>
            {
                new() { UserId = usersDict["Fatima Zahra"], StartDate = DateTime.UtcNow.AddDays(2).Date, EndDate = DateTime.UtcNow.AddDays(4).Date, Type = LeaveType.Vacation, Status = RequestStatus.Approved, Reason = "Family vacation trip.", AssignedManagerId = ahmedId },
                new() { UserId = usersDict["Youssef Amrani"], StartDate = DateTime.UtcNow.AddDays(7).Date, EndDate = DateTime.UtcNow.AddDays(7).Date, Type = LeaveType.Sick, Status = RequestStatus.Pending, Reason = "Feeling unwell, need rest.", AssignedManagerId = sarahId },
                new() { UserId = usersDict["Nadia Boudiaf"], StartDate = DateTime.UtcNow.AddDays(14).Date, EndDate = DateTime.UtcNow.AddDays(18).Date, Type = LeaveType.Vacation, Status = RequestStatus.Pending, Reason = "Summer holiday planned in advance.", AssignedManagerId = ahmedId },
                new() { UserId = usersDict["Karim Hadj"], StartDate = DateTime.UtcNow.AddDays(-1).Date, EndDate = DateTime.UtcNow.AddDays(0).Date, Type = LeaveType.Personal, Status = RequestStatus.Rejected, Reason = "Personal errand.", AssignedManagerId = ahmedId },
                new() { UserId = usersDict["Amina Khelifi"], StartDate = DateTime.UtcNow.AddDays(23).Date, EndDate = DateTime.UtcNow.AddDays(25).Date, Type = LeaveType.Vacation, Status = RequestStatus.Approved, Reason = "Wedding attendance.", AssignedManagerId = ahmedId },
                new() { UserId = usersDict["Omar Benmoussa"], StartDate = DateTime.UtcNow.AddDays(10).Date, EndDate = DateTime.UtcNow.AddDays(12).Date, Type = LeaveType.Sick, Status = RequestStatus.Pending, Reason = "Doctor appointment + recovery.", AssignedManagerId = ahmedId }
            };

            await context.LeaveRequests.AddRangeAsync(leaves);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded LeaveRequests.");
        }

        // 6. Seed Announcements
        if (!await context.Announcements.AnyAsync())
        {
            var announcements = new List<Announcement>
            {
                new() { Title = "Office Renovation Notice", Content = "Floors 2-3 will undergo renovation from June 15-30. Please use Floor 1 facilities.", CreatedById = sarahId, IsActive = true },
                new() { Title = "New Parking Policy", Content = "Starting July 1, all employees must register their vehicles via the internal portal.", CreatedById = sarahId, IsActive = true },
                new() { Title = "Ramadan Schedule Update", Content = "During Ramadan, working hours will be 9:00 AM – 3:00 PM.", CreatedById = sarahId, IsActive = true }
            };

            await context.Announcements.AddRangeAsync(announcements);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded Announcements.");
        }

        // 7. Seed GeneralRequests
        if (!await context.GeneralRequests.AnyAsync())
        {
            var requests = new List<GeneralRequest>
            {
                new() { UserId = usersDict["Fatima Zahra"], Title = "Laptop replacement", Description = "My laptop battery drains in 2 hours.", Category = RequestCategory.IT, Status = RequestStatus.InProgress, AssignedToUserId = ahmedId },
                new() { UserId = usersDict["Youssef Amrani"], Title = "Access card not working", Description = "Badge doesn't open Floor 3 door.", Category = RequestCategory.Facilities, Status = RequestStatus.Pending, AssignedToUserId = adminId },
                new() { UserId = usersDict["Amina Khelifi"], Title = "Salary slip missing", Description = "April 2026 pay slip not available online.", Category = RequestCategory.Finance, Status = RequestStatus.Approved, AssignedToUserId = sarahId },
                new() { UserId = usersDict["Nadia Boudiaf"], Title = "Office chair broken", Description = "Armrest fell off, need replacement.", Category = RequestCategory.Facilities, Status = RequestStatus.Pending, AssignedToUserId = adminId }
            };

            await context.GeneralRequests.AddRangeAsync(requests);
            await context.SaveChangesAsync();
            Console.WriteLine("  ✅ Seeded GeneralRequests.");
        }

        Console.WriteLine("🎉 Database Seeding Completed!");
    }
}
