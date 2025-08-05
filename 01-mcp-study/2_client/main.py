# Importa os módulos necessários
import asyncio
import json
from typing import Dict

# Importa a classe MCPClient do módulo local
from src.client.client import MCPClient
# Importa a classe StdioServerParameters do módulo mcp
from mcp import StdioServerParameters


def load_config(path: str = "servers_config.json") -> Dict[str, StdioServerParameters]:
    """
    Carrega a configuração dos servidores MCP a partir de um arquivo JSON.
    
    Args:
        path (str, opcional): Caminho para o arquivo de configuração JSON.
                             Padrão: "servers_config.json"
    
    Returns:
        Dict[str, StdioServerParameters]: Um dicionário onde as chaves são nomes de servidores
                                         e os valores são objetos StdioServerParameters configurados.
    
    O arquivo de configuração deve ter o seguinte formato:
    {
        "mcpServers": {
            "nome_do_servidor_1": {
                "command": "comando_para_iniciar_servidor",
                "args": ["arg1", "arg2", ...],
                "env": {"VARIAVEL_AMBIENTE": "valor"}
            },
            "nome_do_servidor_2": { ... }
        }
    }
    """
    # Abre o arquivo de configuração no modo leitura
    with open(path, "r") as f:
        # Carrega o conteúdo do arquivo JSON
        data = json.load(f)

    # Obtém o dicionário de servidores da configuração
    # Se a chave "mcpServers" não existir, usa um dicionário vazio
    server_entries = data.get("mcpServers", {})
    config = {}

    # Itera sobre cada servidor na configuração e cria os parâmetros necessários
    for name, server in server_entries.items():
        config[name] = StdioServerParameters(
            command=server["command"],  # Comando para iniciar o servidor
            args=server["args"],        # Argumentos para o comando
            env=server.get("env")      # Variáveis de ambiente (opcional)
        )
    return config


async def main():
    """
    Função principal que inicia o cliente MCP e inicia o loop de chat.
    
    Esta função:
    1. Cria uma instância do MCPClient
    2. Conecta-se a todos os servidores especificados no arquivo de configuração
    3. Inicia o loop de chat para interação com o usuário
    4. Realiza a limpeza dos recursos quando o loop de chat é encerrado
    """
    # Cria uma instância do cliente MCP
    client = MCPClient()
    
    # Carrega a configuração e conecta-se a todos os servidores especificados
    await client.connect_all_servers(load_config())
    
    # Inicia o loop de chat para interação com o usuário
    await client.chat_loop()
    
    # Realiza a limpeza dos recursos (fecha conexões, etc.)
    await client.cleanup()


# Ponto de entrada principal do script
if __name__ == "__main__":
    # Executa a função main() de forma assíncrona
    asyncio.run(main())