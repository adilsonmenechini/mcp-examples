# Importa a classe FastMCP do módulo mcp.server.fastmcp
# Esta classe permite criar um servidor MCP (Model Control Protocol)
from mcp.server.fastmcp import FastMCP

# Cria uma instância do servidor com o nome "Meu Servidor de Calculadora"
# Este nome será usado para identificar o servidor
server = FastMCP("Meu Servidor de Calculadora")

# Define a ferramenta de avaliação de expressões matemáticas
# O decorador @server.tool() registra esta função como uma ferramenta disponível no servidor
@server.tool()
def evaluate_expression(expression: str) -> float:
    """
    Avalia uma expressão matemática e retorna o resultado.
    
    Esta função aceita uma string contendo uma expressão matemática (como "5 * 7")
    e retorna o resultado da avaliação da expressão.
    
    Args:
        expression: Uma string contendo uma expressão matemática (ex: "5 * 7", "2 + 3 * 4").

    Returns:
        float: O resultado da expressão avaliada.
        
    Raises:
        ValueError: Se a expressão for inválida ou não puder ser avaliada.
        
    Exemplos:
        >>> evaluate_expression("2 + 2")
        4.0
        >>> evaluate_expression("10 / 2 * (3 + 2)")
        25.0
    """
    try:
        # AVISO: O uso de eval() é inseguro para entradas não confiáveis
        # Em produção, considere usar uma biblioteca de análise matemática segura
        # como 'ast.literal_eval' ou 'numexpr' para avaliação segura de expressões
        
        # O dicionário vazio "__builtins__": {} limita o acesso a funções embutidas
        # para aumentar a segurança, e o dicionário vazio final impede o acesso a variáveis locais
        # A função sum() é explicitamente permitida para uso em expressões
        result = eval(expression, {"__builtins__": {}}, {"sum": sum})
        return float(result)  # Garante que o resultado seja retornado como float
    except Exception as e:
        # Em caso de erro na avaliação, levanta uma exceção com uma mensagem descritiva
        raise ValueError(f"Expressão inválida: {e}")

# Ponto de entrada principal do script
if __name__ == "__main__":
    # Inicia o servidor para comunicação via entrada/saída padrão (stdio)
    # Isso permite que o servidor seja controlado por um processo pai
    # O servidor ficará em execução até ser interrompido (Ctrl+C)
    server.run()