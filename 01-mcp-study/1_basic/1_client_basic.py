# Importações necessárias para o funcionamento do cliente MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

# Configuração dos parâmetros do servidor que será executado localmente
# command: comando para executar o servidor (neste caso, 'uv' que é o gerenciador de pacotes do Python)
# args: argumentos para o comando, incluindo o script Python a ser executado
# env: variáveis de ambiente (opcional, neste caso não há nenhuma)
server_params = StdioServerParameters(
    command="uv",              # Executável que será usado para rodar o servidor
    args=["run", "python", "tool_duckduckgo.py"],  # Script do servidor
    env=None                   # Variáveis de ambiente (opcional)
)

async def run():
    """
    Função principal que inicia o cliente e se comunica com o servidor.
    """
    # Inicia o servidor como um subprocesso e configura a comunicação via stdio
    # 'read' e 'write' são funções para ler e escrever dados no processo do servidor
    async with stdio_client(server_params) as (read, write):
        # Cria uma sessão de cliente para se comunicar com o servidor
        async with ClientSession(read, write) as session:
            # Inicializa a conexão com o servidor
            await session.initialize()

            # Lista as ferramentas disponíveis no servidor
            tools = await session.list_tools()
            print("\n=== Ferramentas Disponíveis ===")
            # Itera sobre as ferramentas disponíveis e exibe seus nomes e descrições
            for key, value in tools:
                if key == "tools":
                    for tool in value:
                        # Obtém o nome da ferramenta ou usa 'Unnamed Tool' se não tiver nome
                        name = getattr(tool, 'name', None) or getattr(tool, 'title', 'Ferramenta sem nome')
                        # Obtém a descrição da ferramenta ou uma mensagem padrão
                        description = getattr(tool, 'description', 'Nenhuma descrição disponível.')
                        print(f"- Nome: {name}\n  Descrição: {description}")    
            print("========================\n")

            # Solicita uma expressão matemática ao usuário
            expression = input("Digite uma expressão matemática (ex: 2+2): ")

            # Chama a ferramenta 'evaluate_expression' no servidor com a expressão fornecida
            result = await session.call_tool(
                "evaluate_expression",  # Nome da ferramenta a ser chamada
                arguments={"expression": expression}  # Argumentos para a ferramenta
            )
            
            # Exibe o resultado da operação
            print("\n=== Resultado do Cálculo ===")
            print(f"Expressão: {expression}")
            print(f"Resultado: {result}")
            print("==========================\n")

# Ponto de entrada principal do programa
if __name__ == "__main__":
    # Executa a função assíncrona 'run' usando o loop de eventos do asyncio
    asyncio.run(run())