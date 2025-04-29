from mcp.server.fastmcp import FastMCP
from core.router import Router
from pydantic import BaseModel

mcp = FastMCP("RouterAgent")
router = Router()


class ProblemModel(BaseModel):
    problem_description: str


@mcp.tool(
    name="diagnose_problem", description="Diagnostica e agrupa problemas do Kubernetes"
)
async def diagnose_problem(data: ProblemModel):
    return await router.handle_problem(data.problem_description)


if __name__ == "__main__":
    mcp.run()
