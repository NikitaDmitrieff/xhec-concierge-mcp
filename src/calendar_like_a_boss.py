from urllib.parse import quote_plus
from datetime import datetime, timedelta
import json
from mistralai import Mistral


def create_calendar_links(
    event_title, start_time, duration_hours, description, location
):
    """
    Génère des liens "Ajouter au calendrier" pour Google, Outlook et Yahoo.

    :param event_title: Titre de l'événement.
    :param start_time: Objet datetime pour le début de l'événement.
    :param duration_hours: Durée de l'événement en heures.
    :param description: Description de l'événement.
    :param location: Lieu de l'événement.
    """
    end_time = start_time + timedelta(hours=duration_hours)

    # --- Encodage pour les URL ---
    # S'assure que les caractères spéciaux (espaces, etc.) sont correctement formatés.
    title_encoded = quote_plus(event_title)
    description_encoded = quote_plus(description)
    location_encoded = quote_plus(location)

    # --- Formatage des dates ---
    # Google Calendar utilise le format YYYYMMDDTHHMMSSZ (UTC)
    start_utc = start_time.strftime("%Y%m%dT%H%M%SZ")
    end_utc = end_time.strftime("%Y%m%dT%H%M%SZ")
    # Google Calendar
    link = (
        f"https://www.google.com/calendar/render?action=TEMPLATE"
        f"&text={title_encoded}"
        f"&dates={start_utc}/{end_utc}"
        f"&details={description_encoded}"
        f"&location={location_encoded}"
    )

    return link


def extract_event_details(transcript: str):
    """
    This function takes a transcript, wraps it in an instruction for Mistral,
    and returns event details in JSON format.
    """
    # IMPORTANT: Replace with your actual Mistral AI API key.
    # It is recommended to use environment variables for security.
    api_key = "VrfSiwwufNdGz1b9ekZmBsWDf1yyqqDX"  # Replace with your key
    if api_key == "YOUR_MISTRAL_API_KEY":
        print(
            "Warning: Using dummy data. Please replace 'YOUR_MISTRAL_API_KEY' with a real key."
        )
        # Return dummy data for demonstration if no key is provided
        if "lunch" in transcript.lower():
            return json.dumps(
                {
                    "event_title": "Lunch with Client",
                    "start_time": "2025-10-05T12:30:00",
                    "location": "La Trattoria",
                    "description": "Build rapport and have an informal chat.",
                    "is_lunch": True,
                }
            )
        else:
            return json.dumps(
                {
                    "event_title": "Quarterly Results Meeting",
                    "start_time": "2025-09-21T14:00:00",
                    "location": "Conference Room B",
                    "description": "Discussing the results from the last quarter and planning our next steps.",
                    "is_lunch": False,
                }
            )

    model = "mistral-large-latest"
    client = Mistral(api_key=api_key)

    # This prompt instructs Mistral to extract event details.
    system_prompt = f"""
    You are an intelligent assistant that extracts event information from a text transcript.
    Your task is to analyze the following transcript and return a single JSON object with the event details.
    
    Transcript: '{transcript}'
    
    The result must be exclusively a valid JSON object, with no text before or after.
    The JSON object must include the following keys:
    - "event_title": The title of the event.
    - "start_time": The start time in strict ISO 8601 format (e.g., "YYYY-MM-DDTHH:MM:SS").
    - "location": The physical or virtual location of the event.
    - "description": A brief summary of the event's purpose.
    - "is_lunch": A boolean value (true or false) indicating if the event is a lunch.
    """

    # This API call structure matches the user's example.
    chat_response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": system_prompt}],
        response_format={"type": "json_object"},
    )

    return chat_response.choices[0].message.content


# --- Main Function to Fulfill the Request ---


def make_calendar_api_based_on_transcript(transcript: str):
    """
    Parses a text transcript using Mistral AI to create a Google Calendar event link.
    A lunch is automatically considered to last for 2 hours.
    """
    try:
        # 1. Call the Mistral API to get event details
        json_details_str = extract_event_details(transcript)
        event_details = json.loads(json_details_str)

        # 2. Extract and validate the details from the JSON
        event_title = event_details.get("event_title", "Event")
        start_time_str = event_details.get("start_time")
        location = event_details.get("location", "Not Specified")
        description = event_details.get("description", "")
        is_lunch = event_details.get("is_lunch", False)

        if not start_time_str:
            return (
                "Error: Could not determine the event start time from the transcript."
            )

        # 3. Process the details for the calendar function
        start_time = datetime.fromisoformat(start_time_str)

        # A lunch is considered to have a duration of 2 hours
        duration_hours = 2 if is_lunch else 1

        # 4. Generate and return the calendar link
        calendar_link = create_calendar_links(
            event_title, start_time, duration_hours, description, location
        )

        return calendar_link

    except json.JSONDecodeError:
        return "Error: Failed to parse the response from the AI model."
    except (ValueError, TypeError) as e:
        return f"Error processing event details: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


"""if __name__ == "__main__":
    # --- Utilisation ---
    event_details = {
    "event_title": "Dîner chez 'Le Grand Restaurant'",
    "start_time": datetime(2025, 10, 19, 19, 0, 0), # 19 Octobre 2025 à 19h00
    "duration_hours": 2,
    "description": "Réservation pour 2 personnes. Allergie au gluten à noter.",
    "location": "123 Rue de la Gastronomie, 75016 Paris, France"
}
    calendar_link = create_calendar_links(**event_details)

    print(f"Google: {calendar_link}")"""
