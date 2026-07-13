from mcp.server.fastmcp import FastMCP
from tools import detect_disease
import inspect


mcp = FastMCP(
    "Disease MCP Server",
    host="0.0.0.0",
    port=8002
)

@mcp.tool()
def disease_detection(symptom: str) -> dict:
    return detect_disease(symptom)

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http" )