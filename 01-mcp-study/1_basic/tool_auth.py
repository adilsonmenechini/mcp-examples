import os
from functools import wraps
from typing import Any, Callable
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Cria uma instância do servidor FastMCP com o nome "tool auth"
server = FastMCP("tool auth")

# --- Lógica de Autenticação ---
def autenticar_usuario(token: str) -> str:
    """
    Verifica se o token de autenticação é válido.
    
    Args:
        token: String contendo o token de autenticação
        
    Returns:
        str: ID do usuário se a autenticação for bem-sucedida
        
    Raises:
        ValueError: Se o token for inválido ou não estiver configurado
    """
    if token == os.getenv("TOKEN_AUTH"):
        return "adilson.menechini"
    raise ValueError("Token de autenticação inválido ou ausente.")


# --- Decorador de Autenticação ---
def auth_necessaria(func: Callable) -> Callable:
    """
    Decorador que verifica a autenticação antes de executar uma função.
    
    Este decorador é usado para envolver funções que requerem autenticação.
    Ele verifica o token nas variáveis de ambiente e chama a função original
    apenas se a autenticação for bem-sucedida.
    
    Args:
        func: Função a ser decorada
        
    Returns:
        Callable: Função decorada que verifica autenticação
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Obtém o token das variáveis de ambiente do processo
        # O token é definido no cliente que inicia este servidor
        token = os.getenv("token")
        
        try:
            # Tenta autenticar o usuário com o token fornecido
            user_id = autenticar_usuario(token)
            print(f"Usuário '{user_id}' autenticado com sucesso.")
            
            # Se a autenticação for bem-sucedida, chama a função original
            return func(*args, **kwargs)
        except ValueError as e:
            # Em caso de falha na autenticação, retorna uma mensagem de erro
            print(f"Erro de autenticação: {e}")
            return f"Erro de autenticação: {e}"
    
    return wrapper


# --- Ferramenta com Autenticação ---
@server.tool()  # Registra a função como uma ferramenta disponível no servidor
@auth_necessaria  # Aplica o decorador de autenticação
# O token não é mais um parâmetro da função, pois é obtido das variáveis de ambiente
def auth_print() -> str:
    """
    Ferramenta de exemplo que requer autenticação para ser acessada.
    
    Esta função só pode ser executada se um token de autenticação válido
    for fornecido nas variáveis de ambiente do processo.
    
    Returns:
        str: Mensagem de confirmação de autenticação bem-sucedida
    """
    return "Autenticado com sucesso!"


# Ponto de entrada principal do script
if __name__ == "__main__":
    # Carrega variáveis de ambiente de um arquivo .env, se existir
    # Útil para testes locais sem precisar configurar variáveis de ambiente no sistema
    load_dotenv()
    
    # Inicia o servidor para comunicação via entrada/saída padrão (stdio)
    # Isso permite que o servidor seja controlado por um processo pai
    server.run()
