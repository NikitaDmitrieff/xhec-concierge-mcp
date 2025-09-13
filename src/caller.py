import requests
import os
import dotenv

dotenv.load_dotenv()


task = f"""
You're Jean, a concierge at X-HEC Concierge.  
You're calling a restaurant named {{restaurant_name}} to book a table for {{number_of_people}} people {{date_of_reservation}} at {{time_of_reservation}}.  
If neither works, ask the restaurant what time they can do.  
Confirm the reservation name and close politely.

EXAMPLE 1:
Person (Restaurant): Hello?
You (Jean): I would like to book a table for 2 people tonight at 8:00 PM.?
Person (Restaurant): Yes we have a table for you, what should i put the reservation name as?
You (Jean): Mr Dupont, please.
Person (Restaurant): Ok, noted! Thank you!
You (Jean): Thank you, have a great evening! Goodbye.

EXAMPLE 2:
Person (Restaurant): Hello?
You (Jean): I would like to book a table for 2 people tonight at 8:00 PM.?
Person (Restaurant): No, sorry, we don't have any availability for tonight at all.
You (Jean): Ok no worries, thanks a lot!
Person (Restaurant): Have a great evening! Goodbye.
"""


def send_bland_pathway_call(
    phone_number: str,
    restaurant_name: str,
    number_of_people: int,
    date_of_reservation: str,
    time_of_reservation: str,
) -> str:
    """
    Starts a Bland AI call that uses an existing conversational pathway.
    Returns the call_id on success, or raises for HTTP errors.
    Arguments:
        phone_number: The phone number of the restaurant
        restaurant_name: The name of the restaurant
        number_of_people: The number of people in the reservation
        date_of_reservation: The date of the reservation
        time_of_reservation: The time of the reservation
    Returns:
        The call_id on success, or raises for HTTP errors.
    """

    api_key = os.getenv("BLAND_API_KEY")

    url = "https://api.bland.ai/v1/calls"
    headers = {
        "Authorization": f"Bearer {api_key}",  # API key auth
        "Content-Type": "application/json",
    }
    payload = {
        "phone_number": phone_number,
        "task": task.format(
            restaurant_name=restaurant_name,
            number_of_people=number_of_people,
            date_of_reservation=date_of_reservation,
            time_of_reservation=time_of_reservation,
        ),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Bland API error: {data}")
    return data["call_id"]


if __name__ == "__main__":

    phone_number = "+33601420712"
    send_bland_pathway_call(
        phone_number=phone_number,
        restaurant_name="Restaurant Dupont",
        number_of_people=2,
        date_of_reservation="tonight",
        time_of_reservation="8:00 PM",
    )
