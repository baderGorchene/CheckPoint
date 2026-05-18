"""
Creates CheckPoint_DB and its core tables if they don't exist.
This mirrors the EF Core schema from the .NET backend,
allowing the chatbot to work independently.

Usage: python setup_db.py
"""

import pyodbc
from config import DB_SERVER, DB_DRIVER, DB_NAME


def get_master_conn():
    return pyodbc.connect(
        f"Driver={DB_DRIVER};Server={DB_SERVER};"
        f"Database=master;Trusted_Connection=yes;TrustServerCertificate=yes;",
        autocommit=True,
    )


def get_app_conn():
    return pyodbc.connect(
        f"Driver={DB_DRIVER};Server={DB_SERVER};"
        f"Database={DB_NAME};Trusted_Connection=yes;TrustServerCertificate=yes;"
    )


def create_database():
    conn = get_master_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT DB_ID('{DB_NAME}')")
    if cur.fetchone()[0] is None:
        cur.execute(f"CREATE DATABASE [{DB_NAME}]")
        print(f"  [+] Created database {DB_NAME}")
    else:
        print(f"  [=] Database {DB_NAME} already exists")
    conn.close()


def table_exists(cur, name: str) -> bool:
    cur.execute(
        "SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", name
    )
    return cur.fetchone() is not None


def create_tables():
    conn = get_app_conn()
    cur = conn.cursor()

    # ── Roles ──
    if not table_exists(cur, "Roles"):
        cur.execute("""
            CREATE TABLE Roles (
                Id   INT PRIMARY KEY,
                Name NVARCHAR(50)  NOT NULL,
                [Description] NVARCHAR(200)
            )
        """)
        cur.execute("""
            INSERT INTO Roles (Id, Name, [Description]) VALUES
            (1, 'Employee', 'Regular employee'),
            (2, 'Manager',  'Department manager'),
            (3, 'Admin',    'System administrator')
        """)
        print("  [+] Created Roles")
    else:
        print("  [=] Roles exists")

    # ── Departments ──
    if not table_exists(cur, "Departments"):
        cur.execute("""
            CREATE TABLE Departments (
                Id   INT IDENTITY(1,1) PRIMARY KEY,
                Name NVARCHAR(100) NOT NULL UNIQUE
            )
        """)
        cur.execute("""
            INSERT INTO Departments (Name) VALUES
            ('IT'), ('HR'), ('Finance'), ('Operations')
        """)
        print("  [+] Created Departments")
    else:
        print("  [=] Departments exists")

    # ── Users ──
    if not table_exists(cur, "Users"):
        cur.execute("""
            CREATE TABLE Users (
                Id              INT IDENTITY(1,1) PRIMARY KEY,
                FullName        NVARCHAR(200) NOT NULL,
                Email           NVARCHAR(255) NOT NULL UNIQUE,
                PhoneNumber     NVARCHAR(20),
                PasswordHash    NVARCHAR(500) NOT NULL,
                RoleId          INT NOT NULL DEFAULT 1,
                DepartmentId    INT NOT NULL,
                LeaveBalance    INT,
                YearlySalary    DECIMAL(18,2),
                CreatedAt       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                IsActive        BIT NOT NULL DEFAULT 0,
                ApprovedAt      DATETIME2,
                ApprovedByUserId INT,
                RejectedAt      DATETIME2,
                RejectedById    INT,
                RejectionReason NVARCHAR(MAX),
                CONSTRAINT FK_Users_Role FOREIGN KEY (RoleId) REFERENCES Roles(Id),
                CONSTRAINT FK_Users_Department FOREIGN KEY (DepartmentId) REFERENCES Departments(Id)
            )
        """)
        print("  [+] Created Users")
    else:
        print("  [=] Users exists")

    # ── Rooms ──
    if not table_exists(cur, "Rooms"):
        cur.execute("""
            CREATE TABLE Rooms (
                Id       INT IDENTITY(1,1) PRIMARY KEY,
                Name     NVARCHAR(100) NOT NULL UNIQUE,
                Type     INT NOT NULL,
                Capacity INT NOT NULL DEFAULT 10,
                IsActive BIT NOT NULL DEFAULT 1,
                QrData   NVARCHAR(MAX) NOT NULL DEFAULT ''
            )
        """)
        cur.execute("""
            INSERT INTO Rooms (Name, Type, Capacity, IsActive) VALUES
            ('Conference Room A', 2, 20, 1),
            ('Meeting Room B',    1, 10, 1),
            ('Training Room',     3, 30, 1)
        """)
        print("  [+] Created Rooms")
    else:
        print("  [=] Rooms exists")

    # ── OfficeTables ──
    if not table_exists(cur, "OfficeTables"):
        cur.execute("""
            CREATE TABLE OfficeTables (
                Id        INT IDENTITY(1,1) PRIMARY KEY,
                Name      NVARCHAR(100) NOT NULL,
                PositionX FLOAT NOT NULL,
                PositionY FLOAT NOT NULL,
                Width     FLOAT NOT NULL DEFAULT 100,
                Height    FLOAT NOT NULL DEFAULT 50
            )
        """)
        print("  [+] Created OfficeTables")
    else:
        print("  [=] OfficeTables exists")

    # ── Seats ──
    if not table_exists(cur, "Seats"):
        cur.execute("""
            CREATE TABLE Seats (
                Id            INT IDENTITY(1,1) PRIMARY KEY,
                OfficeTableId INT NOT NULL,
                PositionX     FLOAT NOT NULL,
                PositionY     FLOAT NOT NULL,
                Label         NVARCHAR(50) NOT NULL,
                IsActive      BIT NOT NULL DEFAULT 1,
                CONSTRAINT FK_Seats_OfficeTable FOREIGN KEY (OfficeTableId) REFERENCES OfficeTables(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created Seats")
    else:
        print("  [=] Seats exists")

    # ── SeatReservations ──
    if not table_exists(cur, "SeatReservations"):
        cur.execute("""
            CREATE TABLE SeatReservations (
                Id        INT IDENTITY(1,1) PRIMARY KEY,
                SeatId    INT NOT NULL,
                UserId    INT NOT NULL,
                Date      DATE NOT NULL,
                Status    INT NOT NULL DEFAULT 1,
                CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_SeatReservations_Seat FOREIGN KEY (SeatId) REFERENCES Seats(Id) ON DELETE CASCADE,
                CONSTRAINT FK_SeatReservations_User FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created SeatReservations")
    else:
        print("  [=] SeatReservations exists")

    # ── RoomReservations ──
    if not table_exists(cur, "RoomReservations"):
        cur.execute("""
            CREATE TABLE RoomReservations (
                Id            INT IDENTITY(1,1) PRIMARY KEY,
                RoomId        INT NOT NULL,
                UserId        INT NOT NULL,
                ManagerId     INT,
                CreatedById   INT,
                StartedById   INT,
                EndedById     INT,
                StartDateTime DATETIME2 NOT NULL,
                EndDateTime   DATETIME2 NOT NULL,
                Status        INT NOT NULL,
                CreatedAt     DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                Title         NVARCHAR(200),
                [Description] NVARCHAR(MAX),
                CONSTRAINT FK_RoomReservations_Room FOREIGN KEY (RoomId) REFERENCES Rooms(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created RoomReservations")
    else:
        print("  [=] RoomReservations exists")

    # ── Events ──
    if not table_exists(cur, "Events"):
        cur.execute("""
            CREATE TABLE Events (
                Id              INT IDENTITY(1,1) PRIMARY KEY,
                Title           NVARCHAR(200) NOT NULL,
                [Description]   NVARCHAR(MAX) NOT NULL DEFAULT '',
                Type            INT NOT NULL,
                RoomId          INT,
                StartDateTime   DATETIME2 NOT NULL,
                EndDateTime     DATETIME2 NOT NULL,
                CreatedByUserId INT NOT NULL,
                IsMandatory     BIT NOT NULL DEFAULT 0,
                RSVPEnabled     BIT NOT NULL DEFAULT 1,
                CreatedAt       DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_Events_Room FOREIGN KEY (RoomId) REFERENCES Rooms(Id),
                CONSTRAINT FK_Events_User FOREIGN KEY (CreatedByUserId) REFERENCES Users(Id)
            )
        """)
        print("  [+] Created Events")
    else:
        print("  [=] Events exists")

    # ── EventParticipants ──
    if not table_exists(cur, "EventParticipants"):
        cur.execute("""
            CREATE TABLE EventParticipants (
                Id        INT IDENTITY(1,1) PRIMARY KEY,
                EventId   INT NOT NULL,
                UserId    INT NOT NULL,
                Status    INT NOT NULL DEFAULT 1,
                CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_EventParticipants_Event FOREIGN KEY (EventId) REFERENCES Events(Id) ON DELETE CASCADE,
                CONSTRAINT FK_EventParticipants_User  FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created EventParticipants")
    else:
        print("  [=] EventParticipants exists")

    # ── LeaveRequests ──
    if not table_exists(cur, "LeaveRequests"):
        cur.execute("""
            CREATE TABLE LeaveRequests (
                Id                INT IDENTITY(1,1) PRIMARY KEY,
                UserId            INT NOT NULL,
                StartDate         DATE NOT NULL,
                EndDate           DATE NOT NULL,
                Type              INT NOT NULL,
                Status            INT NOT NULL DEFAULT 1,
                Reason            NVARCHAR(1000) NOT NULL,
                ManagerComment    NVARCHAR(1000),
                ReviewedAt        DATETIME2,
                AssignedManagerId INT,
                ReviewedById      INT,
                CreatedAt         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_LeaveRequests_User FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created LeaveRequests")
    else:
        print("  [=] LeaveRequests exists")

    # ── AbsenceRequests ──
    if not table_exists(cur, "AbsenceRequests"):
        cur.execute("""
            CREATE TABLE AbsenceRequests (
                Id        INT IDENTITY(1,1) PRIMARY KEY,
                UserId    INT NOT NULL,
                Date      DATE NOT NULL,
                Reason    NVARCHAR(1000) NOT NULL,
                Status    INT NOT NULL DEFAULT 1,
                ManagerId INT,
                CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_AbsenceRequests_User FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created AbsenceRequests")
    else:
        print("  [=] AbsenceRequests exists")

    # ── GeneralRequests ──
    if not table_exists(cur, "GeneralRequests"):
        cur.execute("""
            CREATE TABLE GeneralRequests (
                Id               INT IDENTITY(1,1) PRIMARY KEY,
                UserId           INT NOT NULL,
                Title            NVARCHAR(200) NOT NULL,
                [Description]    NVARCHAR(2000) NOT NULL,
                Category         INT NOT NULL,
                Status           INT NOT NULL DEFAULT 1,
                AdminComment     NVARCHAR(MAX),
                ResolvedAt       DATETIME2,
                AssignedToUserId INT,
                CreatedAt        DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_GeneralRequests_User FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created GeneralRequests")
    else:
        print("  [=] GeneralRequests exists")

    # ── Notifications ──
    if not table_exists(cur, "Notifications"):
        cur.execute("""
            CREATE TABLE Notifications (
                Id                INT IDENTITY(1,1) PRIMARY KEY,
                UserId            INT NOT NULL,
                Title             NVARCHAR(200) NOT NULL,
                Message           NVARCHAR(MAX) NOT NULL,
                Type              NVARCHAR(50) NOT NULL DEFAULT 'Info',
                RelatedEntityType NVARCHAR(100),
                RelatedEntityId   INT,
                IsRead            BIT NOT NULL DEFAULT 0,
                CreatedAt         DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_Notifications_User FOREIGN KEY (UserId) REFERENCES Users(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created Notifications")
    else:
        print("  [=] Notifications exists")

    # ── Announcements ──
    if not table_exists(cur, "Announcements"):
        cur.execute("""
            CREATE TABLE Announcements (
                Id          INT IDENTITY(1,1) PRIMARY KEY,
                Title       NVARCHAR(200) NOT NULL,
                Content     NVARCHAR(MAX) NOT NULL,
                CreatedAt   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                UpdatedAt   DATETIME2,
                PublishAt   DATETIME2,
                ExpiresAt   DATETIME2,
                IsActive    BIT NOT NULL DEFAULT 1,
                CreatedById INT NOT NULL,
                ImageUrl    NVARCHAR(MAX),
                CONSTRAINT FK_Announcements_User FOREIGN KEY (CreatedById) REFERENCES Users(Id)
            )
        """)
        print("  [+] Created Announcements")
    else:
        print("  [=] Announcements exists")

    # ── InternalRequests ──
    if not table_exists(cur, "InternalRequests"):
        cur.execute("""
            CREATE TABLE InternalRequests (
                Id          INT IDENTITY(1,1) PRIMARY KEY,
                UserId      INT NOT NULL,
                Title       NVARCHAR(200) NOT NULL,
                Content     NVARCHAR(MAX) NOT NULL,
                Status      INT NOT NULL DEFAULT 1,
                CreatedAt   DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_InternalRequests_User FOREIGN KEY (UserId) REFERENCES Users(Id)
            )
        """)
        print("  [+] Created InternalRequests")
    else:
        print("  [=] InternalRequests exists")

    # ── DepartmentChannelMessages ──
    if not table_exists(cur, "DepartmentChannelMessages"):
        cur.execute("""
            CREATE TABLE DepartmentChannelMessages (
                Id           INT IDENTITY(1,1) PRIMARY KEY,
                DepartmentId INT NOT NULL,
                SenderId     INT NOT NULL,
                Content      NVARCHAR(2000),
                MessageType  NVARCHAR(50) NOT NULL,
                CreatedAt    DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_DCM_Department FOREIGN KEY (DepartmentId) REFERENCES Departments(Id),
                CONSTRAINT FK_DCM_Sender     FOREIGN KEY (SenderId) REFERENCES Users(Id)
            )
        """)
        print("  [+] Created DepartmentChannelMessages")
    else:
        print("  [=] DepartmentChannelMessages exists")

    # ── DepartmentChannelReadStates ──
    if not table_exists(cur, "DepartmentChannelReadStates"):
        cur.execute("""
            CREATE TABLE DepartmentChannelReadStates (
                Id            INT IDENTITY(1,1) PRIMARY KEY,
                DepartmentId  INT NOT NULL,
                UserId        INT NOT NULL,
                LastReadAt    DATETIME2,
                CONSTRAINT FK_DCRS_Department FOREIGN KEY (DepartmentId) REFERENCES Departments(Id),
                CONSTRAINT FK_DCRS_User       FOREIGN KEY (UserId) REFERENCES Users(Id)
            )
        """)
        print("  [+] Created DepartmentChannelReadStates")
    else:
        print("  [=] DepartmentChannelReadStates exists")

    # ── DepartmentPolls ──
    if not table_exists(cur, "DepartmentPolls"):
        cur.execute("""
            CREATE TABLE DepartmentPolls (
                Id        INT IDENTITY(1,1) PRIMARY KEY,
                MessageId INT NOT NULL,
                Question  NVARCHAR(500) NOT NULL,
                CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_DP_Message FOREIGN KEY (MessageId) REFERENCES DepartmentChannelMessages(Id)
            )
        """)
        print("  [+] Created DepartmentPolls")
    else:
        print("  [=] DepartmentPolls exists")

    # ── DepartmentPollOptions ──
    if not table_exists(cur, "DepartmentPollOptions"):
        cur.execute("""
            CREATE TABLE DepartmentPollOptions (
                Id     INT IDENTITY(1,1) PRIMARY KEY,
                PollId INT NOT NULL,
                [Text] NVARCHAR(300) NOT NULL,
                CONSTRAINT FK_DPO_Poll FOREIGN KEY (PollId) REFERENCES DepartmentPolls(Id) ON DELETE CASCADE
            )
        """)
        print("  [+] Created DepartmentPollOptions")
    else:
        print("  [=] DepartmentPollOptions exists")

    # ── DepartmentPollVotes ──
    if not table_exists(cur, "DepartmentPollVotes"):
        cur.execute("""
            CREATE TABLE DepartmentPollVotes (
                Id           INT IDENTITY(1,1) PRIMARY KEY,
                PollId       INT NOT NULL,
                UserId       INT NOT NULL,
                PollOptionId INT NOT NULL,
                VotedAt      DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                CONSTRAINT FK_DPV_Poll   FOREIGN KEY (PollId) REFERENCES DepartmentPolls(Id) ON DELETE CASCADE,
                CONSTRAINT FK_DPV_User   FOREIGN KEY (UserId) REFERENCES Users(Id),
                CONSTRAINT FK_DPV_Option FOREIGN KEY (PollOptionId) REFERENCES DepartmentPollOptions(Id)
            )
        """)
        print("  [+] Created DepartmentPollVotes")
    else:
        print("  [=] DepartmentPollVotes exists")

    conn.commit()
    conn.close()
    print("  --- All tables ready ---")


def main():
    print("== CheckPoint DB Setup ==")
    create_database()
    create_tables()
    print("== Done ==")


if __name__ == "__main__":
    main()
