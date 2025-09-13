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
from src.calendar_like_a_boss import create_calendar_links


load_dotenv()

mcp = FastMCP("Echo Server", port=3000, stateless_http=True, debug=True)


@mcp.tool(
    title="Echo Tool",
    description="Echo the input text",
)
def echo(text: str = Field(description="The text to echo")) -> str:
    return text

@mcp.tool(
    title="Generate a calendar link",
    description="given some information on the meeting, this tool can generate a calendar link to give to the user"
)
def calendar(event_title, start_time, duration_hours, description, location):
    """
    Cette fonction prend des informatiuons sur un évenement, et retourne un lien Google Calendar
    """
    return create_calendar_links(event_title, start_time, duration_hours, description, location)



if __name__ == "__main__":
    mcp.run(transport="streamable-http")