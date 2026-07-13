from fastmcp import FastMCP

from tools import (
    recommend_crop,
    seasonal_crop,
    crop_tips,
    available_soils
)

# Create MCP Server
mcp = FastMCP("Crop Advisor MCP")


# ----------------------------
# Tool 1
# ----------------------------
@mcp.tool
def recommend_crop_tool(soil_type: str):
    """
    Recommend crops based on soil type.
    """
    return recommend_crop(soil_type)


# ----------------------------
# Tool 2
# ----------------------------
@mcp.tool
def seasonal_crop_tool(season: str):
    """
    Recommend crops based on season.
    """
    return seasonal_crop(season)


# ----------------------------
# Tool 3
# ----------------------------
@mcp.tool
def crop_tips_tool(crop_name: str):
    """
    Return farming tips for a crop.
    """
    return crop_tips(crop_name)


# ----------------------------
# Tool 4
# ----------------------------
@mcp.tool
def available_soils_tool():
    """
    Return all supported soil types.
    """
    return available_soils()


# ----------------------------
# Start MCP Server
# ----------------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8001
    )