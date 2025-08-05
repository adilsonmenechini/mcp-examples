import os
from functools import wraps
from typing import Any, Callable
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Cria uma instância do servidor FastMCP
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
    # Compara o token fornecido com o TOKEN_AUTH armazenado no .env
    if token == os.getenv("TOKEN_AUTH"):
        return "adilson.menechini"
    raise ValueError("Token de autenticação inválido ou ausente.")


# --- Decorador de Autenticação ---
def auth_necessaria(func: Callable) -> Callable:
    """
    Decorador que verifica a autenticação antes de executar uma função.
    
    Este decorador é usado para envolver funções que requerem autenticação,
    garantindo que um token válido seja fornecido através das variáveis de ambiente.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Pega o token da variável de ambiente 'token'
        token = os.getenv("token")
        
        try:
            # Tenta autenticar o usuário
            user_id = autenticar_usuario(token)
            print(f"Usuário '{user_id}' autenticado com sucesso.")
            
            # Se a autenticação passar, executa a função original
            return func(*args, **kwargs)
        except ValueError as e:
            # Em caso de falha, retorna uma mensagem de erro
            print(f"Erro de autenticação: {e}")
            return f"Erro de autenticação: {e}"
    
    return wrapper


# --- Ferramenta com Autenticação ---
@server.tool()  # Registra como uma ferramenta do FastMCP
@auth_necessaria  # Aplica o decorador de autenticação para protegê-la
def auth_print() -> str:
    """
    Ferramenta de exemplo que só pode ser acessada com um token válido.
    
    A autenticação é feita pelo decorador 'auth_necessaria' antes de
    esta função ser chamada.
    """
    return "Autenticado com sucesso! user: " + autenticar_usuario(os.getenv("token"))


# Ponto de entrada principal
if __name__ == "__main__":
    # Carrega as variáveis do arquivo .env
    load_dotenv()
    
    # Inicia o servidor FastMCP
    server.run()