# Importa a biblioteca DDGS (DuckDuckGo Search) para realizar buscas
from ddgs import DDGS
# Importa a classe FastMCP para criar um servidor MCP
from mcp.server.fastmcp import FastMCP
# Importa o módulo json para manipulação de dados JSON
import json

# Cria uma instância do servidor FastMCP
# Este servidor irá expor a funcionalidade de busca como uma ferramenta
app = FastMCP()

# Define a ferramenta de busca como uma função do servidor
# O decorador @app.tool() registra esta função como uma ferramenta disponível no servidor
@app.tool()
def search(query: str) -> dict:
    """
    Realiza uma busca na web usando o mecanismo de busca DuckDuckGo.
    
    Esta função aceita uma string de consulta, realiza uma busca no DuckDuckGo
    e retorna os resultados em formato de dicionário.
    
    Args:
        query (str): A consulta de pesquisa que será enviada ao DuckDuckGo.
                     Exemplo: "notícias sobre inteligência artificial"
                     
    Returns:
        dict: Um dicionário contendo:
            - query: A consulta de pesquisa original
            - results: Lista de dicionários com os resultados da busca
            
    Raises:
        JsonRpcError: Se ocorrer um erro durante a comunicação com o servidor RPC.
        
    Exemplo de retorno:
        {
            "query": "python programming",
            "results": [
                {
                    "title": "Bem-vindo ao Python.org",
                    "link": "https://www.python.org/",
                    "snippet": "A linguagem de programação que coloca o poder nas suas mãos...",
                    ...
                },
                ...
            ]
        }
    """
    try:
        # Cria uma instância do cliente DuckDuckGo Search
        ddgs = DDGS()
        
        # Realiza a busca com a consulta fornecida
        # O parâmetro pages=10 limita a busca às 10 primeiras páginas de resultados
        results = ddgs.text(query, pages=10)
        
        # Formata a resposta em um dicionário estruturado
        response = {
            "query": query,    # Mantém a consulta original na resposta
            "results": results  # Inclui todos os resultados da busca
        }
        
        return response
        
    except json.JSONDecodeError as e:
        # Captura e registra erros de decodificação JSON
        print(f"Erro ao decodificar JSON: {e}")
        # Propaga a exceção para que o cliente seja notificado do erro
        raise

# Ponto de entrada principal do script
if __name__ == "__main__":
    # Inicia o servidor MCP
    # O servidor ficará em execução até ser interrompido (Ctrl+C)
    # Ele escutará por requisições via stdio (entrada/saída padrão)
    app.run()
