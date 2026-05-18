using Microsoft.Extensions.AI;
using OllamaSharp;
using PFE.Infrastructure.Data;

namespace PFE.Chatbot;

public class ChatbotAgent
{
    private readonly IChatClient _client;
    private readonly ChatOptions _chatOptions;
    private readonly List<ChatMessage> _history;

    public ChatbotAgent(string ollamaUrl, string modelName, ApplicationDbContext dbContext)
    {
        Console.WriteLine($"🤖 Initializing ChatClient with Ollama model '{modelName}' at '{ollamaUrl}'...");

        // Initialize Ollama client
        var ollamaClient = new OllamaApiClient(new Uri(ollamaUrl), modelName);

        // Define database tools
        var dbTools = new DatabaseTools(dbContext);

        // Wrap Ollama client with function invocation middleware
        _client = new ChatClientBuilder(ollamaClient)
            .UseFunctionInvocation()
            .Build();

        // Create AI functions from our DatabaseTools class
        var tools = new List<AIFunction>
        {
            AIFunctionFactory.Create(dbTools.GetDepartmentsAsync, "GetDepartments", "Get all departments with their employee counts."),
            AIFunctionFactory.Create(dbTools.GetEmployeesAsync, "GetEmployees", "Get employees, optionally filtered by department name. Pass an empty string to get all employees."),
            AIFunctionFactory.Create(dbTools.GetEmployeeDetailsAsync, "GetEmployeeDetails", "Get detailed information about a specific employee by name (partial match)."),
            AIFunctionFactory.Create(dbTools.GetLeaveRequestsAsync, "GetLeaveRequests", "Get leave requests, optionally filtered by status (Pending, Approved, Rejected)."),
            AIFunctionFactory.Create(dbTools.GetEventsAsync, "GetEvents", "Get all upcoming company events."),
            AIFunctionFactory.Create(dbTools.GetRoomsAsync, "GetRooms", "Get all conference, meeting, and training rooms."),
            AIFunctionFactory.Create(dbTools.GetAnnouncementsAsync, "GetAnnouncements", "Get all active company announcements."),
            AIFunctionFactory.Create(dbTools.GetGeneralRequestsAsync, "GetGeneralRequests", "Get general support requests, optionally filtered by status (Pending, Approved, Rejected, InProgress, Resolved)."),
            AIFunctionFactory.Create(dbTools.GetStatisticsAsync, "GetStatistics", "Get overall company statistics.")
        };

        // Configure chat options with tools
        _chatOptions = new ChatOptions
        {
            Tools = tools
        };

        // Setup conversational history with a system message
        _history = new List<ChatMessage>
        {
            new(ChatRole.System, 
                "You are CheckPoint AI Chatbot, an expert corporate assistant for CheckPoint company. " +
                "You have direct access to the CheckPoint database via tools. " +
                "When asked about employees, departments, leave requests, company events, rooms, announcements, " +
                "support requests, or company statistics, always use your tools first to get the most accurate, " +
                "real-time data from the database before responding. " +
                "Format your responses in clean, highly structured Markdown. " +
                "If you cannot find the requested information after calling the tools, explain clearly what you searched for. " +
                "Be precise, professional, helpful, and concise.")
        };
    }

    public async Task<string> SendMessageAsync(string userMessage)
    {
        // Add user message to history
        _history.Add(new ChatMessage(ChatRole.User, userMessage));

        try
        {
            // Execute the chat request (function calling is handled automatically by middleware)
            var response = await _client.CompleteAsync(_history, _chatOptions);

            // Add assistant's response to history
            if (response.Message != null)
            {
                _history.Add(response.Message);
                return response.Message.Text ?? "No text response received.";
            }

            return "Error: Empty response from AI model.";
        }
        catch (Exception ex)
        {
            return $"❌ Error during AI generation: {ex.Message}\n\nStack Trace:\n{ex.StackTrace}";
        }
    }

    public void ClearHistory()
    {
        var systemMsg = _history.FirstOrDefault(m => m.Role == ChatRole.System);
        _history.Clear();
        if (systemMsg != null)
        {
            _history.Add(systemMsg);
        }
    }
}
