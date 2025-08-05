from typing import List
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
from dotenv import load_dotenv
import asyncio
 
# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
 
# Inicializa o cliente da API do Google Gemini com a chave da API
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
# Define o modelo a ser usado (Gemini 2.0 Flash)
model = "gemini-2.0-flash"
 
# Configuração dos parâmetros do servidor que será executado localmente
server_params = StdioServerParameters(
    command="uv",  # Executável que será usado
    args=[
        "run",
        "python",
        "tool_duckduckgo.py",  # Script do servidor
    ],
    env=None  # Variáveis de ambiente (opcional)
)
 
async def agent_loop(prompt: str, client: genai.Client, session: ClientSession):
    """
    Loop principal do agente que processa as requisições do usuário.
    
    Args:
        prompt: Texto de entrada do usuário
        client: Instância do cliente da API do Gemini
        session: Sessão do cliente MCP
    """
    # Inicializa a lista de conteúdos com a mensagem do usuário
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    
    # Inicializa a conexão com o servidor
    await session.initialize()
    
    # 1. Obtém as ferramentas disponíveis na sessão e converte para o formato do Gemini
    mcp_tools = await session.list_tools()
    tools = types.Tool(function_declarations=[
        {
            "name": tool.name,  # Nome da ferramenta
            "description": tool.description,  # Descrição da ferramenta
            "parameters": tool.inputSchema,  # Esquema de entrada da ferramenta
        }
        for tool in mcp_tools.tools  # Itera sobre todas as ferramentas disponíveis
    ])
    
    # 2. Faz a primeira requisição para a API do Gemini
    response = await client.aio.models.generate_content(
        model=model,  # Modelo a ser usado
        contents=contents,  # Conteúdo da conversa
        config=types.GenerateContentConfig(
            temperature=0,  # Controle de aleatoriedade (0 = mais determinístico)
            tools=[tools],  # Lista de ferramentas disponíveis
        ),
    )
    
    # 3. Adiciona a resposta inicial ao histórico da conversa
    contents.append(response.candidates[0].content)
 
    # 4. Loop de interação com as ferramentas
    turn_count = 0
    max_tool_turns = 5  # Número máximo de interações com ferramentas
    while response.function_calls and turn_count < max_tool_turns:
        turn_count += 1
        tool_response_parts: List[types.Part] = []
 
        # 4.1 Processa todas as chamadas de ferramentas na resposta
        for fc_part in response.function_calls:
            tool_name = fc_part.name  # Nome da ferramenta a ser chamada
            args = fc_part.args or {}  # Argumentos para a ferramenta
            print(f"Chamando ferramenta MCP: '{tool_name}' com argumentos: {args}")
 
            tool_response: dict
            try:
                # Chama a ferramenta através da sessão MCP
                tool_result = await session.call_tool(tool_name, args)
                print(f"Ferramenta MCP '{tool_name}' executada com sucesso.")
                
                # Formata a resposta baseado no resultado
                if tool_result.isError:
                    tool_response = {"error": tool_result.content[0].text if tool_result.content else "Erro desconhecido"}
                else:
                    tool_response = {"result": tool_result.content[0].text if tool_result.content else "Sucesso"}
                    
            except Exception as e:
                tool_response = {"error": f"Falha na execução da ferramenta: {type(e).__name__}: {e}"}
            
            # Prepara a resposta para ser enviada de volta ao modelo
            tool_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name, 
                    response=tool_response
                )
            )
 
        # 4.2 Adiciona as respostas das ferramentas ao histórico
        if tool_response_parts:
            contents.append(types.Content(role="user", parts=tool_response_parts))
            print(f"Adicionadas {len(tool_response_parts)} respostas de ferramentas ao histórico.")
 
        # 4.3 Faz uma nova chamada para o modelo com o histórico atualizado
        print("Fazendo nova chamada para a API com as respostas das ferramentas...")
        response = await client.aio.models.generate_content(
            model=model,
            contents=contents,  # Histórico atualizado
            config=types.GenerateContentConfig(
                temperature=1.0,  # Aumenta a criatividade para respostas finais
                tools=[tools],    # Mantém as mesmas ferramentas
            ),
        )
        contents.append(response.candidates[0].content)
 
    # Verifica se o limite máximo de interações foi atingido
    if turn_count >= max_tool_turns and response.function_calls:
        print(f"Limite máximo de interações ({max_tool_turns}) atingido. Encerrando loop.")
 
    print("Loop de ferramentas MCP finalizado. Retornando resposta final.")
    return response
        
async def run():
    """
    Função principal que gerencia a sessão de chat com o usuário.
    """
    # Inicia a conexão com o servidor MCP
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Iniciando conversa com o agente. Digite 'exit' ou 'quit' para sair.")
            print("Você pode me fazer perguntas ou usar as ferramentas disponíveis.")
            print("-" * 50)
            
            # Histórico da conversa
            conversation_history = []
            
            while True:
                # Obtém a entrada do usuário
                user_input = input("\nVocê: ").strip()
                
                # Verifica se o usuário quer sair
                if user_input.lower() in ('exit', 'quit'):
                    print("Até mais!")
                    break
                    
                if not user_input:
                    print("Por favor, digite uma mensagem.")
                    continue
                
                # Adiciona a mensagem do usuário ao histórico
                conversation_history.append({"role": "user", "content": user_input})
                
                try:
                    # Processa a mensagem usando o agente
                    print("\nAgente está pensando...")
                    response = await agent_loop(user_input, client, session)
                    
                    # Obtém a resposta do assistente
                    if response and hasattr(response, 'text'):
                        assistant_response = response.text
                    elif response and hasattr(response, 'candidates') and response.candidates:
                        assistant_response = response.candidates[0].content.parts[0].text
                    else:
                        assistant_response = "Desculpe, não consegui gerar uma resposta."
                    
                    # Adiciona a resposta ao histórico
                    conversation_history.append({"role": "assistant", "content": assistant_response})
                    
                    # Exibe a resposta
                    print(f"\nAssistente: {assistant_response}")
                    
                except Exception as e:
                    # Tratamento de erros
                    error_msg = f"Ocorreu um erro: {str(e)}"
                    print(f"\nErro: {error_msg}")
                    conversation_history.append({"role": "system", "content": error_msg})
            return response

async def main():
    """Função principal que inicia a execução do programa."""
    response = await run()
    if hasattr(response, 'text'):
        print(response.text)

if __name__ == "__main__":
    # Inicia o loop de eventos assíncrono
    asyncio.run(main())