import os
import httpx
import json # Importe a biblioteca json para manipular a resposta JSON
from functools import wraps
from typing import Any, Callable, Tuple
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Cria uma instância do servidor FastMCP
server = FastMCP("tool auth")

# --- Lógica de Autenticação com Serviço Externo ---
async def autenticar_usuario_externo(username: str, password: str) -> Tuple[str, str]:
    """
    Verifica as credenciais fazendo uma requisição a um serviço de login externo.
    
    Args:
        username: Nome de usuário para autenticação.
        password: Senha para autenticação.
        
    Returns:
        Tuple[str, str]: Uma tupla contendo o ID do usuário e o token.
        
    Raises:
        ValueError: Se a requisição falhar ou as credenciais forem inválidas.
    """
    login_url = "http://127.0.0.1:5000/login"
    
    auth_data = {"username": username, "password": password}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(login_url, json=auth_data)
        
        if response.status_code == 200:
            response_data = response.json()
            
            # --- CORREÇÃO AQUI ---
            # O servidor de login retorna 'access_token', então precisamos pegar essa chave
            token = response_data.get("access_token") 
            
            # Para simplificar, vamos assumir que o nome de usuário é o 'user_id'
            user_id = username
            
            if user_id and token:
                return user_id, token
            else:
                raise ValueError("Resposta do servidor de login inválida: 'access_token' não encontrado.")
        else:
            # Tratamento de erro aprimorado para mostrar a mensagem do servidor de login, se houver
            error_message = response.json().get("error", "Erro desconhecido")
            raise ValueError(f"Falha na autenticação: {error_message} (Código HTTP: {response.status_code})")
            
    except httpx.RequestError as e:
        raise ValueError(f"Erro ao conectar-se ao serviço de login: {e}")
    except json.JSONDecodeError:
        raise ValueError("Resposta do servidor de login não é um JSON válido.")

# --- Decorador de Autenticação com Usuário e Senha ---
def auth_necessaria(func: Callable) -> Callable:
    """
    Decorador que verifica a autenticação usando o serviço externo antes de executar a função.
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        username = os.getenv("username")
        password = os.getenv("password")
        
        try:
            # A função de autenticação agora retorna uma tupla (user_id, token)
            user_id, token = await autenticar_usuario_externo(username, password)
            print(f"Usuário '{user_id}' autenticado com sucesso via serviço externo. Token obtido.")
            
            # Você pode armazenar o token em uma variável de ambiente temporária para uso na ferramenta
            os.environ["AUTH_TOKEN"] = token
            
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"Erro de autenticação: {e}")
            return f"Erro de autenticação: {e}"
    
    return wrapper

# --- Ferramenta com Autenticação ---
@server.tool()
@auth_necessaria
def auth_print() -> str:
    """
    Ferramenta de exemplo que só pode ser acessada com um usuário e senha válidos.
    A mensagem de sucesso agora inclui o token.
    """
    # --- CORREÇÃO AQUI ---
    # A variável 'token' foi recuperada do ambiente na linha anterior
    token = os.getenv("AUTH_TOKEN")
    return f"Autenticado com sucesso! token: {token}"


# Ponto de entrada principal
if __name__ == "__main__":
    load_dotenv()
    server.run()