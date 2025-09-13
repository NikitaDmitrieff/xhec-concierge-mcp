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
from src.prompt_sport_wellness import find_sports_wellness


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
    description="Fetch restaurant suggestions from Mistral, you must provide the previous info if the previous research was sunsuccessful.",
)
def cherche_restaurant(prompt_utilisateur) -> str:
    """
    Cette fonction prend le prompt de l'utilisateur, l'enveloppe dans une instruction
    pour Mistral afin d'obtenir une liste de 5 restaurants au format JSON.
    """
    return find_restaurant(prompt_utilisateur)

@mcp.tool(
    title="Fetch sports activities suggestions and wellness",
    description=(
        "Analyze the user's request to book a sports activity and suggest a matching wellness option. "
        "The assistant must extract: sport_type, location, date, time, number_of_people, price, reservation_name, time_flexibility. "
        "If one or more required fields are missing, the tool must return a JSON with status='missing_info' "
        "and explicitly list the missing fields, asking the user to provide them. "
        "Once all required fields are present, return a JSON with status='success' containing the sports venue found and the wellness suggestion."
    )
)
def cherche_sports_wellness(prompt_utilisateur) -> str:
    """
    XXXX
    """
    return find_sports_wellness(prompt_utilisateur)



if __name__ == "__main__":
    mcp.run(transport="streamable-http")