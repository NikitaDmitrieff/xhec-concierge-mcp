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
# Le nom du fichier est une supposition, adaptez si besoin
from calendar_like_a_boss import create_calendar_links
# --- AJOUT IMPORTANT ---
from datetime import datetime


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
    title="Create a calendar for the user after he successfully booked a restaurant",
    description="Create a calendar link for Google Calendar (only)",
)
# --- MODIFICATION 1 : Le type hint de start_time est maintenant `str` ---
def calendar_links(
    event_title: str,
    duration_hours: int,
    description: str,
    location: str,
    start_time: str = Field(description="Start time in ISO format, e.g., '2025-10-19T19:00:00'"),
):
    """ exemple d'appel de l'API :
    {
        "event_title": "Dîner chez 'Le Grand Restaurant'",
        "start_time": "2025-10-19T19:00:00",
        "duration_hours": 2,
        "description": "Réservation pour 2 personnes. Allergie au gluten à noter.",
        "location": "123 Rue de la Gastronomie, 75016 Paris, France"
    }
    """
    try:
        # --- MODIFICATION 2 : On convertit la chaîne en objet datetime ---
        start_time_dt = datetime.fromisoformat(start_time)
        
        # --- MODIFICATION 3 : On passe l'objet datetime à la fonction ---
        return create_calendar_links(
            event_title,
            start_time_dt, # On utilise la variable convertie
            duration_hours,
            description,
            location
        )
    except ValueError as e:
        return f"Erreur : le format de la date '{start_time}' est incorrect. Utilisez le format ISO YYYY-MM-DDTHH:MM:SS. Erreur : {e}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")