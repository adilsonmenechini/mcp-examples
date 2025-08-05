import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configuração dos parâmetros para executar o servidor FastMCP como um subprocesso
# O token de autenticação é passado através do dicionário 'env' para o servidor
server_params = StdioServerParameters(
    command="uv",  # Comando para executar o servidor (usando uv como gerenciador de pacotes)
    args=["run", "python", "tool_auth20.py"],  # Argumentos para executar o script do servidor
    env={"token": "secret-token-333"}  # Token de autenticação passado como variável de ambiente
)

async def run():
    """
    Função principal que estabelece a conexão com o servidor e executa a ferramenta de autenticação.
    
    Esta função demonstra como se conectar a um servidor MCP que requer autenticação
    e como chamar uma ferramenta protegida por autenticação.
    """
    print("Iniciando a conexão com o servidor...")
    try:
        # Inicia o servidor como um subprocesso e configura a comunicação via stdio (entrada/saída padrão)
        # 'read' e 'write' são funções para ler e escrever dados no processo do servidor
        async with stdio_client(server_params) as (read, write):
            # Cria uma sessão do cliente para se comunicar com o servidor
            async with ClientSession(read, write) as session:
                # Inicializa a conexão com o servidor
                await session.initialize()
                print("Conexão estabelecida com sucesso.")

                # Lista todas as ferramentas disponíveis no servidor
                # Isso é útil para verificar se a ferramenta 'auth_print' está disponível
                tools = await session.list_tools()
                print("\n=== Ferramentas Disponíveis ===")
                # Itera sobre as ferramentas disponíveis e exibe seus nomes
                for key, value in tools:
                    if key == "tools":  # Verifica se a chave é 'tools' que contém a lista de ferramentas
                        for tool in value:
                            # Obtém o nome da ferramenta ou usa 'Ferramenta sem nome' se não tiver nome
                            name = getattr(tool, 'name', 'Ferramenta sem nome')
                            print(f"- Nome: {name}")
                print("========================")

                # --- Chamada da ferramenta 'auth_print' ---
                # Esta chamada não requer o token como argumento, pois ele já foi passado nas configurações
                # do servidor através das variáveis de ambiente
                print("\nChamando a ferramenta 'auth_print'...")
                
                # Executa a ferramenta 'auth_print' no servidor
                result = await session.call_tool("auth_print")

                # Exibe o resultado da chamada da ferramenta
                print("\n=== Resultado da Autenticação ===")
                print(f"Resultado: {result}")
                print("==========================")

    except Exception as e:
        # Captura e exibe qualquer erro que ocorrer durante a execução
        print(f"Ocorreu um erro durante a execução: {e}")

# Ponto de entrada principal do programa
if __name__ == "__main__":
    # Executa a função assíncrona 'run' usando o loop de eventos do asyncio
    asyncio.run(run())
