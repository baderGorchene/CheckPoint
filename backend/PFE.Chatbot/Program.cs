using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using PFE.Infrastructure.Data;

namespace PFE.Chatbot;

public class Program
{
    public static async Task Main(string[] args)
    {
        Console.OutputEncoding = System.Text.Encoding.UTF8;
        Console.ForegroundColor = ConsoleColor.Cyan;
        Console.WriteLine("==================================================");
        Console.WriteLine("🌐 CheckPoint AI Chatbot - .NET Edition (MAF/Ollama) 🌐");
        Console.WriteLine("==================================================");
        Console.ResetColor();

        // 1. Build configuration to read connection string from PFE.API/appsettings.json
        string apiPath = Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "PFE.API");
        if (!Directory.Exists(apiPath))
        {
            // Fallback for production execution folder
            apiPath = AppContext.BaseDirectory;
        }

        var configBuilder = new ConfigurationBuilder()
            .SetBasePath(Directory.Exists(apiPath) ? apiPath : AppContext.BaseDirectory)
            .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);

        var configuration = configBuilder.Build();
        
        string? connectionString = configuration.GetConnectionString("DefaultConnection");
        if (string.IsNullOrEmpty(connectionString))
        {
            // Direct hardcoded fallback to the verified database instance
            connectionString = "Server=BUNSHEE\\SQLEXPRESS;Database=CheckPoint_DB;Trusted_Connection=True;MultipleActiveResultSets=true;TrustServerCertificate=True";
            Console.WriteLine("⚠️ Could not load appsettings.json. Using verified connection string fallback.");
        }
        else
        {
            Console.WriteLine($"✅ Loaded connection string pointing to SQL Server instance.");
        }

        // 2. Set up ApplicationDbContext
        var optionsBuilder = new DbContextOptionsBuilder<ApplicationDbContext>();
        optionsBuilder.UseSqlServer(connectionString);

        using var dbContext = new ApplicationDbContext(optionsBuilder.Options);

        // 3. Ask to seed mock data
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.Write("\n❓ Do you want to seed/re-seed the SQL Server CheckPoint_DB database? (y/n): ");
        Console.ResetColor();
        string? seedInput = Console.ReadLine();

        if (seedInput?.Trim().ToLower() == "y")
        {
            try
            {
                await DatabaseSeeder.SeedAllAsync(dbContext);
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"❌ Error during seeding: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                Console.ResetColor();
            }
        }

        // 4. Initialize Chatbot Agent
        string ollamaUrl = "http://localhost:11434";
        string modelName = "gemma4:e4b";

        ChatbotAgent agent;
        try
        {
            agent = new ChatbotAgent(ollamaUrl, modelName, dbContext);
        }
        catch (Exception ex)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine($"❌ Failed to initialize Chatbot: {ex.Message}");
            Console.ResetColor();
            return;
        }

        // 5. Chat loop
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine("\n💬 Chatbot is ready! Ask your questions.");
        Console.WriteLine("   Commands: '/clear' to reset chat, '/exit' to exit.\n");
        Console.ResetColor();

        while (true)
        {
            Console.ForegroundColor = ConsoleColor.Blue;
            Console.Write("👤 User: ");
            Console.ResetColor();
            
            string? prompt = Console.ReadLine();
            if (string.IsNullOrWhiteSpace(prompt)) continue;

            if (prompt.Trim().ToLower() == "/exit")
            {
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("👋 Goodbye!");
                Console.ResetColor();
                break;
            }

            if (prompt.Trim().ToLower() == "/clear")
            {
                agent.ClearHistory();
                Console.ForegroundColor = ConsoleColor.Yellow;
                Console.WriteLine("🧹 Conversation history cleared!");
                Console.ResetColor();
                continue;
            }

            Console.ForegroundColor = ConsoleColor.Magenta;
            Console.Write("🤖 Chatbot: Thinking...");
            Console.ResetColor();

            // Clear the "Thinking..." line and output response
            string response = await agent.SendMessageAsync(prompt);
            
            // Backspace/delete the "Thinking..." text (20 chars)
            Console.Write("\r" + new string(' ', 30) + "\r");

            Console.ForegroundColor = ConsoleColor.Magenta;
            Console.WriteLine("🤖 Chatbot:");
            Console.ResetColor();
            Console.WriteLine(response);
            Console.WriteLine(new string('-', 50));
        }
    }
}
