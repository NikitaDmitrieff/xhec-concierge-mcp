"""
MCP Server Template
"""

from mcp.server.fastmcp import FastMCP
from pydantic import Field

import mcp.types as types
from mistralai import Mistral
from dotenv import load_dotenv
import os
from src.prompt_resto_client import find_restaurant


load_dotenv()

mcp = FastMCP("Echo Server", port=3000, stateless_http=True, debug=True)


@mcp.tool(
    title="Echo Tool",
    description="Echo the input text",
)
def echo(text: str = Field(description="The text to echo")) -> str:
    return text

@mcp.tool(
    title="Fetch restaurant suggestions",
    description="Fetch restaurant suggestions from Mistral, you must provide the user prompt and the thread ID (0 if no thread ID is known for the moment).",
)
def cherche_restaurant(prompt_utilisateur, thread_id = "0") -> str:
    """
    Cette fonction prend le prompt de l'utilisateur, l'enveloppe dans une instruction
    pour Mistral afin d'obtenir une liste de 5 restaurants au format JSON.
    """
    return find_restaurant(prompt_utilisateur, thread_id=thread_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")