from mcp.server.fastmcp import FastMCP
from core.llm_agent import LLM_Agent
from pydantic import BaseModel

mcp = FastMCP("OllamaAgent")
agent = LLM_Agent()


class PromptModel(BaseModel):
    prompt: str
    max_tokens: int = 100


@mcp.tool(name="generate_text", description="Gera texto usando modelo Ollama")
def generate_text(data: PromptModel):
    try:
        text = agent.generate(data.prompt, data.max_tokens)
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Iniciando Ollama MCP Server")
    mcp.run()
