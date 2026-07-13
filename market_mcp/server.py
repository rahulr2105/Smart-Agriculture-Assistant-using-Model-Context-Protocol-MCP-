from mcp.server.fastmcp import FastMCP

from tools import (
    market_price,
    government_scheme,
    best_selling_crop,
    profit_calculator
)

mcp = FastMCP("Market MCP", host="0.0.0.0", port=8004)


@mcp.tool()
def get_market_price(crop_name: str):
    return market_price(crop_name)


@mcp.tool()
def get_government_scheme(farmer_type: str):
    return government_scheme(farmer_type)


@mcp.tool()
def get_best_selling_crop():
    return best_selling_crop()


@mcp.tool()
def calculate_profit(crop_name: str, quantity: int):
    return profit_calculator(crop_name, quantity)

# ----------------------------
# Start MCP Server
# ----------------------------
if __name__ == "__main__":
    mcp.run(transport="streamable-http")