def select_agent(input_text: str) -> str:
    if "passo a passo" in input_text or "como" in input_text:
        return "cot-agent"
    elif "estrutura" in input_text:
        return "sot-agent"
    return "ollama-agent"
