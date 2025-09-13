"""
MCP Server Template
"""

from mcp.server.fastmcp import FastMCP
import os
from pydantic import Field
from src.prompt_resto_client import find_restaurant

import mcp.types as types

mcp = FastMCP("Echo Server", port=3000, stateless_http=True, debug=True)


@mcp.tool(
    title="Echo Tool",
    description="Echo the input text",
)
def echo(text: str = Field(description="The text to echo")) -> str:
    return text

@mcp.tool(
    title="Fetch restaurant suggestions",
    description="Fetch restaurant suggestions from Mistral",
)
def fetch_restaurant_suggestions(prompt: str = Field(description="The prompt to fetch restaurant suggestions")) -> str:
    return find_restaurant(prompt)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

