def apply_policy(prompt: str, context: dict) -> str:
    if "confidencial" in context.get("tags", []):
        return "Por segurança, essa informação não pode ser exibida."
    return prompt
