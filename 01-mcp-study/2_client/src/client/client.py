from src.chatbot.interaction import format_prompt, extract_tool_calls
from src.llm.gemini import GeminiClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
from contextlib import AsyncExitStack
from typing import Dict, Tuple

class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map = {}
        self.llm = GeminiClient()

    async def connect_all_servers(self, server_params_map: Dict[str, StdioServerParameters]):
        for name, params in server_params_map.items():
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[name] = session

            tool_response = await session.list_tools()
            for tool in tool_response.tools:
                self.tool_map[tool.name] = (session, {
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                    "source": name
                })
            print(f"✅ {name}:")
            for tool in tool_response.tools:
                print(f"  - {tool.name}: {tool.description}")

    async def chat_loop(self):
        print("\n🤖 Digite sua pergunta. Digite 'quit' para sair.")
        while True:
            user_input = input("\nUser: ").strip()
            if user_input.lower() in {"quit", "exit"}:
                break
            await self.handle_input(user_input)

    async def handle_input(self, query: str):
        prompt = format_prompt(self.describe_tools(), query)
        raw_response = await self.llm.generate(prompt)
        tool_calls = extract_tool_calls(raw_response)

        if not tool_calls:
            print("⚠️ Nenhuma chamada de ferramenta detectada.\n")
            print(raw_response)
            return

        for call in tool_calls:
            tool_name = call["name"]
            args = call["input"]

            if tool_name not in self.tool_map:
                print(f"❌ Ferramenta '{tool_name}' não está registrada.")
                continue

            session, _ = self.tool_map[tool_name]

            try:
                result = await session.call_tool(tool_name, args)

                # Captura conteúdo da ferramenta (TextContent.text ou output)
                if hasattr(result, "content") and hasattr(result.content, "text"):
                    tool_output = result.content.text
                elif hasattr(result, "output"):
                    tool_output = result.output
                else:
                    tool_output = str(result)

                # Gera nova resposta com base no output da ferramenta
                final_prompt = f"""
Você usou a ferramenta '{tool_name}' para responder à pergunta: {query}

A ferramenta retornou: {tool_output}

Com base nisso, forneça uma resposta natural e útil ao usuário.
"""
                final_response = await self.llm.generate([
                    {"role": "user", "parts": [{"text": final_prompt}]}
                ])
                print("\n🧠", final_response)

            except Exception as e:
                print(f"❌ Erro ao chamar a ferramenta '{tool_name}': {e}")

    def describe_tools(self) -> str:
        description = ""
        for name, (_, meta) in self.tool_map.items():
            description += f"- {name} ({meta['source']}): {meta['description']}\n"
        return description

    async def cleanup(self):
        await self.exit_stack.aclose()