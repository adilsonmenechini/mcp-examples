import asyncio
import json
import sys
from src.client.client import MCPClient
from mcp import StdioServerParameters


def load_config(path: str = "servers_config.json") -> dict[str, StdioServerParameters]:
    """
    Carrega a configuração dos servidores a partir de um arquivo JSON.
    
    Args:
        path: Caminho para o arquivo de configuração
        
    Returns:
        Dicionário com os parâmetros de inicialização dos servidores
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)

        server_entries = data.get("mcpServers", {})
        config = {}

        for name, server in server_entries.items():
            print(f"🔧 Configurando servidor: {name}")
            print(f"   Comando: {server.get('command')}")
            print(f"   Argumentos: {', '.join(server.get('args', []))}")
            
            config[name] = StdioServerParameters(
                command=server["command"],
                args=server["args"],
                env=server.get("env")
            )
            
        return config
        
    except FileNotFoundError:
        print(f"❌ Arquivo de configuração não encontrado: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar o arquivo de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao carregar a configuração: {e}")
        sys.exit(1)


async def main():
    """
    Função principal que inicia o cliente MCP e o loop de chat.
    """
    print("🚀 Iniciando MCP Client...")
    
    try:
        # Carrega a configuração dos servidores
        print("\n📋 Carregando configurações...")
        server_config = load_config()
        
        if not server_config:
            print("⚠️ Nenhum servidor configurado. Verifique o arquivo de configuração.")
            return
            
        # Inicializa o cliente
        client = MCPClient()
        
        # Conecta aos servidores
        print("\n🔌 Conectando aos servidores MCP...")
        await client.connect_all_servers(server_config)
        
        if not client.tool_map:
            print("\n⚠️ Nenhuma ferramenta disponível. Verifique se os servidores estão funcionando corretamente.")
            return
            
        # Inicia o loop de chat
        print("\n💡 Digite 'quit' ou 'sair' a qualquer momento para encerrar.")
        await client.chat_loop()
        
    except KeyboardInterrupt:
        print("\n👋 Encerrando a aplicação...")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Garante que os recursos sejam liberados corretamente
        print("\n🧹 Encerrando conexões...")
        try:
            await client.cleanup()
        except Exception as e:
            print(f"⚠️ Erro ao encerrar conexões: {e}")
        
        print("✅ Aplicação encerrada com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())