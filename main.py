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
from calendar_like_a_boss import create_calendar_links


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

#@mcp.tool(
#    title="Create a calendar for the user after he successfully booked a restaurant",
#    description="Create a calendar link for Google Calendar (only)",
#)
#def calendar_links(event_title, start_time, duration_hours, description, location):
#    """ exemple usage : 
#    "event_title": "Dîner chez 'Le Grand Restaurant'",
#    "start_time": datetime(2025, 10, 19, 19, 0, 0), # 19 Octobre 2025 à 19h00
#    "duration_hours": 2,
#   "description": "Réservation pour 2 personnes. Allergie au gluten à noter.",
#    "location": "123 Rue de la Gastronomie, 75016 Paris, France" 
#   """
#    return create_calendar_links(event_title, start_time, duration_hours, description, location)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")