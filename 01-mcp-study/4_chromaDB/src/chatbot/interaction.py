import re
import json
from typing import Any, Dict, List

# Importa funções de log
from src.utils.logger import log_error

def format_prompt(tools_description: str, query: str) -> str:
    """
    Formata o prompt para o modelo de linguagem, incluindo instruções sobre como usar ferramentas.
    
    Args:
        tools_description: Descrição das ferramentas disponíveis
        query: Consulta do usuário
        
    Returns:
        str: Prompt formatado para o modelo
    """
    return f"""Você é um assistente que pode usar ferramentas para responder perguntas. 

Para usar uma ferramenta, você DEVE responder APENAS com um JSON válido no seguinte formato:

{{"name": "nome_da_ferramenta", "input": {{"parametro1": "valor1"}}}}

INSTRUÇÕES IMPORTANTES:
1. Responda APENAS com o JSON, sem texto adicional, markdown ou comentários
2. Use APENAS aspas duplas para strings e nomes de campos
3. Não use quebras de linha ou formatação no JSON
4. Certifique-se de que o JSON está completo e bem formado

Ferramentas disponíveis:
{tools_description}

Exemplo de uso:
Usuário: calcule 5 * 3
Resposta: {{"name": "evaluate_expression", "input": {{"expression": "5 * 3"}}}}

Agora responda à pergunta abaixo:

Usuário: {query}
Resposta: """

def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    """
    Extrai chamadas de ferramentas no formato ... 
    Retorna uma lista de dicionários com nome e parâmetros da ferramenta.
    
    Args:
        text: Texto contendo as chamadas de ferramentas
        
    Returns:
        List[Dict[str, Any]]: Lista de chamadas de ferramentas extraídas
    """
    tool_calls = []

    # Expressão regular que busca JSON dentro das tags ... 
    pattern = r" ... \s*({.*?})\s* ... "
    matches = re.findall(pattern, text, re.DOTALL)

    for raw_json in matches:
        try:
            # Tenta interpretar o conteúdo como JSON
            tool_call = json.loads(raw_json.strip())
            tool_calls.append(tool_call)
        except json.JSONDecodeError as e:
            error_msg = f"Erro ao interpretar tool_call: {e}\nConteúdo: {raw_json}"
            log_error(error_msg)

    return tool_calls