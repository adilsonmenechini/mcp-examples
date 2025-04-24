def validate(output: str, context: dict) -> dict:
    issues = []
    if "passo" not in output:
        issues.append("Resposta parece não conter raciocínio lógico")
    return {"valid": len(issues) == 0, "issues": issues}
