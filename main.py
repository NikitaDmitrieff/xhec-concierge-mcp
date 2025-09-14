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
from src.calendar_like_a_boss import make_calendar_api_based_on_transcript
from src.caller import send_bland_pathway_call
from src.caller import task


load_dotenv()

mcp = FastMCP("X-HEC Concierge", port=3000, stateless_http=True, debug=True)


@mcp.tool(
    title="Generate a calendar link",
    description=(
        "Use this tool to generate a Google Calendar link for a meeting or reservation. "
        "You must provide the event details: title, start time (as a datetime), duration in hours (default is 2h), "
        "a description, and a location. If not enough info, ask for more to the user before calling the function"
    ),
)
def calendar(transcript: str) -> str:
    """
    Cette fonction prend les informations d’un événement et retourne un lien Google Calendar
    que l’utilisateur peut utiliser pour ajouter l’événement à son agenda.
    """
    return make_calendar_api_based_on_transcript(transcript)


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
    title="Call restaurant",
    description="Call the restaurant to book a table, you must provide the previous info if the previous research was sunsuccessful.",
)
def call_restaurant(
    phone_number: str,
    restaurant_name: str,
    number_of_people: int,
    date_of_reservation: str,
    time_of_reservation: str,
    reservation_name: str,
) -> str:
    """
    This function takes the user's prompt, and calls the restaurant to book a table.

    Arguments:
        phone_number: The phone number of the restaurant
        restaurant_name: The name of the restaurant
        number_of_people: The number of people in the reservation
        date_of_reservation: The date of the reservation
        time_of_reservation: The time of the reservation
        reservation_name: The name of the reservation
    Returns:
        The transcript of the call, or raises for HTTP errors.        The call_id on success, or raises for HTTP errors.
    """
    return send_bland_pathway_call(
        phone_number=phone_number,
        restaurant_name=restaurant_name,
        number_of_people=number_of_people,
        date_of_reservation=date_of_reservation,
        time_of_reservation=time_of_reservation,
        reservation_name=reservation_name,
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
