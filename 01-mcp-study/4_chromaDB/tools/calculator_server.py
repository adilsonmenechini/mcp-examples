from mcp.server.fastmcp import FastMCP

# Create the server
server = FastMCP("My Calculator Server")

# Define the calculator tool
@server.tool()
def evaluate_expression(expression: str) -> float:
    """Evaluates a mathematical expression and returns the result.
    
    Args:
        expression: A string containing a mathematical expression (e.g., "5 * 7").

    Returns:
        The result of the evaluated expression.
    """
    try:
        # Warning: eval() is unsafe for untrusted input; use a proper parser in production
        result = eval(expression, {"__builtins__": {}}, {"sum": sum})
        return result
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

# Run the server over stdio
if __name__ == "__main__":
    server.run()