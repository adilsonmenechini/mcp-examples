import json
import re
from typing import List, Dict, Any
from google.genai.types import Content, Part

def format_prompt(tools_description: str, query: str) -> List[Content]:
    prompt = f"""
Você é um assistente com acesso às ferramentas abaixo.

❗ IMPORTANTE: Para usar uma ferramenta, use **apenas** o seguinte formato (sem crase, sem markdown):

<tool_call>
{{
  "name": "tool_name",
  "input": {{
    "param1": "value1"
  }}
}}
</tool_call>

{tools_description}

Pergunta do usuário: {query}
"""
    return [Content(role="user", parts=[Part(text=prompt)])]


def extract_tool_calls(text: str) -> List[Dict[str, Any]]:
    tool_calls = []

    # Suporta dois padrões: XML-like e fallback com markdown
    patterns = [
        r"<tool_call>(.*?)</tool_call>",
        r"```tool_call(?:}|>)?\s*(\{.*?\})\s*```"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                tool_calls.append(json.loads(match.strip()))
            except Exception as e:
                print(f"⚠️ Falha ao interpretar tool_call: {match} -> {e}")
    return tool_calls