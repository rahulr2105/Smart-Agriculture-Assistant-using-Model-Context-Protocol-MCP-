from mcp.server.fastmcp import FastMCP
from tools import get_weather, irrigation_advice

mcp = FastMCP("Weather MCP",
        host="0.0.0.0",
        port=8003)


@mcp.tool()
def get_weather_tool(city: str):
    return get_weather(city)


@mcp.tool()
def irrigation_advice_tool(weather: str):
    return irrigation_advice(weather)


if __name__ == "__main__":
    mcp.run( transport="streamable-http")