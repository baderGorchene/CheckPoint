"""
CheckPoint Chatbot — Interactive assistant using Ollama + MCP.

Flow:
  1. Starts mcp_db_server.py as a subprocess (stdio transport)
  2. Discovers available MCP tools
  3. Converts them to Ollama tool-calling format
  4. Runs an interactive chat loop:
       user message → Ollama → tool_calls → MCP server → Ollama → response
"""

import asyncio
import json
import sys
import os

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import OLLAMA_MODEL

SYSTEM_PROMPT = """\
You are CheckPoint Assistant, an AI helper for the CheckPoint workplace management system.
You have access to tools that query the company database. Use them to answer questions about:
  • Employees and departments
  • Leave requests and their status
  • Room bookings and availability
  • Company events
  • Announcements
  • General / support requests
  • Overall statistics

Rules:
1. ALWAYS call the appropriate tool(s) before answering data questions.
2. Present data in a clear, readable format.
3. If no results are found, say so honestly.
4. Be concise and helpful.
"""


def mcp_tools_to_ollama(mcp_tools) -> list[dict]:
    """Convert MCP tool definitions → Ollama tool format."""
    result = []
    for t in mcp_tools:
        schema = t.inputSchema or {"type": "object", "properties": {}}
        result.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": schema,
            },
        })
    return result


async def run_chatbot():
    # Locate mcp_db_server.py next to this file
    server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_db_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
    )

    print("\n⏳ Starting MCP database server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Discover tools
            tools_response = await session.list_tools()
            ollama_tools = mcp_tools_to_ollama(tools_response.tools)
            tool_names = [t["function"]["name"] for t in ollama_tools]

            print(f"✅ MCP server connected — {len(tool_names)} tools available:")
            for name in tool_names:
                print(f"   • {name}")

            print("\n" + "=" * 55)
            print("🤖  CheckPoint Assistant")
            print("=" * 55)
            print("Ask about employees, departments, events, leaves, etc.")
            print("Type 'quit' to exit.\n")

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                messages.append({"role": "user", "content": user_input})

                # ── Ask Ollama (with tools) ──
                response = ollama.chat(
                    model=OLLAMA_MODEL,
                    messages=messages,
                    tools=ollama_tools,
                )

                # ── Handle tool call loop ──
                while response.message.tool_calls:
                    messages.append(response.message)

                    for tc in response.message.tool_calls:
                        fn_name = tc.function.name
                        fn_args = tc.function.arguments or {}

                        print(f"  🔧 {fn_name}({json.dumps(fn_args)})")

                        try:
                            mcp_result = await session.call_tool(fn_name, fn_args)
                            content = (
                                mcp_result.content[0].text
                                if mcp_result.content
                                else "No results."
                            )
                        except Exception as e:
                            content = f"Tool error: {e}"

                        messages.append({"role": "tool", "content": content})

                    # Send tool results back to Ollama
                    response = ollama.chat(
                        model=OLLAMA_MODEL,
                        messages=messages,
                        tools=ollama_tools,
                    )

                # ── Print assistant reply ──
                answer = response.message.content
                messages.append({"role": "assistant", "content": answer})
                print(f"\n🤖 {answer}\n")


def main():
    asyncio.run(run_chatbot())


if __name__ == "__main__":
    main()
