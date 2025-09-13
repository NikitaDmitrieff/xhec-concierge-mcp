import json
import re
from datetime import datetime
from mistralai import Mistral
from dotenv import load_dotenv
import os

# --- Load API key from .env ---
load_dotenv()
API_KEY = os.getenv("MISTRAL_API_KEY")

if not API_KEY:
    raise ValueError("⚠️ Missing MISTRAL_API_KEY in .env")

# --- Helpers ---
def parse_time(time_str: str | None) -> str | None:
    if not time_str:
        return None
    formats_to_try = ['%I:%M %p', '%H:%M', '%I %p']
    for fmt in formats_to_try:
        try:
            return datetime.strptime(time_str, fmt).strftime('%H:%M')
        except ValueError:
            continue
    return time_str

def parse_people(people_str: str | None) -> int | None:
    if not people_str:
        return None
    try:
        found_digits = re.findall(r'\d+', str(people_str))
        if found_digits:
            return int(found_digits[0])
    except (ValueError, TypeError):
        return None
    return None


# --- Core Logic ---
def find_sports_wellness(user_query: str) -> str:
    """
    Analyze user request for a sports activity, then suggest a matching wellness activity.
    Returns JSON with both.
    """
    client = Mistral(api_key=API_KEY)
    extraction_model = "mistral-large-latest"
    agent_model = "mistral-large-latest"

    # Step 1: Extract information
    extraction_prompt = f"""
    You are a sports and wellness booking assistant. Analyze the user's request and
    extract the following information into a strict JSON format.
    Keys must be:
      "sport_type", "location", "date", "time", "number_of_people", "price", "reservation_name", "time_flexibility".
    If info is missing, use null.
    User request: "{user_query}"
    """

    try:
        extraction_response = client.chat.complete(
            model=extraction_model,
            messages=[{"role": "user", "content": extraction_prompt}],
            response_format={"type": "json_object"}
        )
        extracted_info = json.loads(extraction_response.choices[0].message.content)
    except Exception as e:
        return f"Error: Could not extract details. {e}"

    # Clean extracted info
    extracted_info['time'] = parse_time(extracted_info.get('time'))
    extracted_info['number_of_people'] = parse_people(extracted_info.get('number_of_people'))

    # Step 2: Check if enough info to proceed
    required_fields = ["sport_type", "location", "date", "time", "number_of_people"]
    missing_info = [f for f in required_fields if extracted_info.get(f) is None]

    if missing_info:
        found_details = {k: v for k, v in extracted_info.items() if v is not None}
        return json.dumps({
            "status": "missing_info",
            "message": f"Missing details: {', '.join(missing_info)}",
            "understood": found_details
        }, indent=2)

    # Step 3: Web search agent to find a sports activity
    try:
        websearch_agent = client.beta.agents.create(
            model=agent_model,
            name="Web Search Sport Finder",
            description="Finds real sports venues (tennis, padel, gym, etc.)",
            instructions="Use your web_search tool to find one real sports venue matching the request. \
                          Return JSON: {'name','address','phone_number'} only.",
            tools=[{"type": "web_search"}],
        )

        search_prompt = f"""
        Find one sports venue for:
        - Sport: {extracted_info.get('sport_type')}
        - Location: {extracted_info.get('location')}
        - Date: {extracted_info.get('date')}
        - Time: {extracted_info.get('time')}
        - People: {extracted_info.get('number_of_people')}
        """

        response = client.beta.conversations.start(
            agent_id=websearch_agent.id,
            inputs=search_prompt
        )

        final_message_content = next(
            (o.content for o in response.outputs if hasattr(o, 'type') and o.type == 'message.output'),
            None
        )

        clean_json_str = re.sub(r'^```json\s*|\s*```$', '', final_message_content, flags=re.MULTILINE)
        sport_found = json.loads(clean_json_str)

    except Exception as e:
        return f"Error during sport search: {e}"

    # Step 4: Map sport -> muscles -> wellness recommendation
    mapping = {
        "tennis": "Massage dos et épaules",
        "padel": "Massage dos et bras",
        "fitness": "Massage jambes ou full body",
        "running": "Massage jambes",
        "escalade": "Massage avant-bras et dos"
    }
    wellness = mapping.get(extracted_info.get("sport_type", "").lower(), "Massage récupération générale")

    # Step 5: Return combined JSON
    return json.dumps({
        "status": "success",
        "sport_booking": {
            "venue": sport_found,
            "details": extracted_info
        },
        "wellness_suggestion": {
            "type": wellness,
            "note": f"Recommended after {extracted_info.get('sport_type')}"
        }
    }, indent=2)


# --- Example Usage ---
if __name__ == "__main__":
    user_call = "I want to play tennis in Paris 15th tomorrow for 2 people, then book a recovery massage."
    print(find_sports_wellness(user_call))
