import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Load environment variables from .env file
load_dotenv()


def load_mcp_server_configs(json_path: str) -> Dict[str, StdioServerParameters]:
    """
    Load MCP server configurations from a JSON file.
    
    Args:
        json_path: Path to the JSON configuration file
        
    Returns:
        Dictionary mapping server names to their connection parameters
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    server_entries = data.get("mcpServers", {})
    mcp_server_parameters = {}

    for name, config in server_entries.items():
        params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
            env=config.get("env")
        )
        mcp_server_parameters[name] = params

    return mcp_server_parameters


class MCPClient:
    """
    Main client class for interacting with MCP servers and processing natural language queries.
    Uses Google's Gemini model for natural language understanding and tool orchestration.
    """
    def __init__(self):
        """Initialize the MCP client with empty sessions and tool mappings."""
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map: Dict[str, Tuple[ClientSession, Dict[str, Any]]] = {}
        self.conversation_history: List[Dict[str, str]] = []
        self.max_tool_turns = 5  # Maximum number of tool interaction turns per query

        # Initialize Gemini client with API key from environment variables
        self.genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.0-flash"
        self.generate_config = types.GenerateContentConfig(
            temperature=0.7,    # Controls randomness (0.0 to 1.0)
            top_p=0.95,        # Nucleus sampling parameter
            max_output_tokens=8192,  # Maximum length of the generated response
        )

    async def connect_all_servers(self, server_params_map: Dict[str, StdioServerParameters]):
        """
        Connect to all MCP servers and register their available tools.
        
        Args:
            server_params_map: Dictionary mapping server names to their connection parameters
        """
        print("\n🚀 Conectando a todos os MCPs...\n")
        for name, params in server_params_map.items():
            try:
                # Establish connection to the MCP server
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                self.sessions[name] = session

                # List and register all available tools from this server
                tool_response = await session.list_tools()
                print(f"\n✅ {name}:")
                for tool in tool_response.tools:
                    self.tool_map[tool.name] = (session, {
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "source": name
                    })
                    print(f"  - {tool.name}: {tool.description}")
                print(f"✅ {name}: {len(tool_response.tools)} ferramentas registradas.")
            except Exception as e:
                print(f"❌ Falha ao conectar com {name}: {e}")

    def _get_tools_declaration(self) -> types.Tool:
        """
        Convert registered tools to the format expected by Gemini API.
        
        Returns:
            types.Tool: Tool definition formatted for Gemini API
        """
        return types.Tool(
            function_declarations=[
                {
                    "name": name,
                    "description": meta["description"],
                    "parameters": meta["input_schema"]
                }
                for name, (_, meta) in self.tool_map.items()
            ]
        )

    async def process_query(self, query: str) -> str:
        """
        Process a user query using Gemini with tool calling capabilities.
        
        Args:
            query: The user's natural language query
            
        Returns:
            str: The assistant's response to the query
        """
        # Add user message to conversation history for context
        self.conversation_history.append({"role": "user", "content": query})
        
        # Format conversation history for the model
        contents = [
            types.Content(
                role="user" if msg["role"] == "user" else "model",
                parts=[types.Part(text=msg["content"])]
            )
            for msg in self.conversation_history
        ]

        # Get tools declaration for tool calling
        tools = self._get_tools_declaration()
        
        # Initial API call to Gemini
        response = await self._generate_content(contents, tools)
        contents.append(response.candidates[0].content)

        # Tool calling loop - handles multiple tool interactions
        turn_count = 0
        while response.function_calls and turn_count < self.max_tool_turns:
            turn_count += 1
            tool_response_parts = []

            # Process all function calls in the response
            for fc_part in response.function_calls:
                tool_name = fc_part.name
                tool_args = fc_part.args or {}
                
                if tool_name not in self.tool_map:
                    error_msg = f"Ferramenta '{tool_name}' não encontrada."
                    tool_response_parts.append(types.Part(text=error_msg))
                    continue

                try:
                    # Execute the requested tool
                    session, _ = self.tool_map[tool_name]
                    tool_result = await session.call_tool(tool_name, tool_args)
                    
                    # Format the tool response
                    if tool_result.isError:
                        tool_response = {"error": tool_result.content[0].text if tool_result.content else "Erro desconhecido"}
                    else:
                        tool_response = {"result": tool_result.content[0].text if tool_result.content else "Sucesso"}
                    
                    tool_response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=tool_response
                        )
                    )
                except Exception as e:
                    error_msg = f"Erro ao executar a ferramenta '{tool_name}': {str(e)}"
                    tool_response_parts.append(types.Part(text=error_msg))

            # Add tool responses to conversation and get model's next response
            if tool_response_parts:
                contents.append(types.Content(role="user", parts=tool_response_parts))
                response = await self._generate_content(contents, tools)
                contents.append(response.candidates[0].content)

        # Process and return the final response
        if response and hasattr(response, 'text'):
            assistant_response = response.text
        elif response and hasattr(response, 'candidates') and response.candidates:
            assistant_response = response.candidates[0].content.parts[0].text
        else:
            assistant_response = "Desculpe, não consegui gerar uma resposta."
        
        # Update conversation history with the assistant's response
        self.conversation_history.append({"role": "assistant", "content": assistant_response})
        return assistant_response

    async def _generate_content(self, contents: List[types.Content], tools: Optional[types.Tool] = None) -> Any:
        """
        Generate content using the Gemini API with error handling.
        
        Args:
            contents: List of conversation messages
            tools: Tools available for the model to use
            
        Returns:
            The response from the Gemini API
        """
        # Create a copy of the config to avoid modifying the original
        config = self.generate_config.model_copy()
        
        # Add tools to the configuration if provided
        if tools:
            config.tools = [tools]
        
        try:
            # Make the API call to Gemini
            return await self.genai_client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config
            )
        except Exception as e:
            print(f"❌ Erro na API do Gemini: {str(e)}")
            raise

    async def chat_loop(self):
        """Main chat loop for user interaction."""
        print("\n🤖 Digite sua pergunta. Digite 'sair' para encerrar.")
        while True:
            try:
                query = input("\nVocê: ").strip()
                if query.lower() in ('sair', 'exit', 'quit'):
                    break
                    
                if not query:
                    continue
                    
                # Process the query and get the response
                response = await self.process_query(query)
                print(f"\n🤖: {response}")
                
            except KeyboardInterrupt:
                print("\nEncerrando...")
                break
            except Exception as e:
                print(f"\n❌ Ocorreu um erro: {str(e)}")


async def main():
    """Main entry point for the MCP client."""
    # Check if config file is provided as command line argument
    if len(sys.argv) < 2:
        print("Uso: python 4_chatbot.py <caminho_para_config.json>")
        sys.exit(1)
        
    config_path = sys.argv[1]
    
    # Load server configurations and initialize client
    server_configs = load_mcp_server_configs(config_path)
    client = MCPClient()
    
    try:
        # Connect to all servers and start chat loop
        await client.connect_all_servers(server_configs)
        await client.chat_loop()
    finally:
        # Clean up resources
        await client.exit_stack.aclose()


if __name__ == "__main__":
    asyncio.run(main())