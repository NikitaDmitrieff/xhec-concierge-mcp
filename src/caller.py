import requests
import os
import dotenv
import time

dotenv.load_dotenv()


task = f"""
You're Jean, a concierge at X-HEC Concierge.  
You're calling a restaurant named {{restaurant_name}} to book a table for {{number_of_people}} people {{date_of_reservation}} at {{time_of_reservation}}.  
Ask to mark the reservation name as {{reservation_name}}. If neither works, ask the restaurant what time they can do.  
Confirm the reservation name and close politely.

EXAMPLE 1:
Person (Restaurant): Hello?
You (Jean): I would like to book a table for 2 people tonight at 8:00 PM.?
Person (Restaurant): Yes we have a table for you.
You (Jean): Great, you can note it as "Mr Dupont", please.
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
    reservation_name: str,
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
            reservation_name=reservation_name,
        ),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Bland API error: {data}")

    print(data)

    call_id = data["call_id"]
    # --- Wait for the call to complete ---
    status_url = f"https://api.bland.ai/v1/calls/{call_id}"
    deadline = time.time() + 100
    last = None
    while True:
        r = requests.get(status_url, headers=headers, timeout=15)
        r.raise_for_status()
        last = r.json()
        # Prefer the 'completed' boolean; 'status' may also be "completed"
        if last.get("completed") or last.get("status") == "completed":
            break
        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for the call to complete.")
        time.sleep(2)

    # --- Fetch transcript: prefer corrected transcript, then fall back ---
    transcript = (last.get("concatenated_transcript") or "").strip()
    try:
        corr = requests.get(f"{status_url}/correct", headers=headers, timeout=15)
        corr.raise_for_status()
        corrected = corr.json().get("corrected") or []
        if corrected:
            transcript = " ".join(seg.get("text", "").strip() for seg in corrected).strip()
    except requests.RequestException:
        pass

    return transcript


if __name__ == "__main__":

    phone_number = "+33601420712"
    transcript = send_bland_pathway_call(
        phone_number=phone_number,
        restaurant_name="Restaurant Dupont",
        number_of_people=2,
        date_of_reservation="tonight",
        time_of_reservation="8:00 PM",
        reservation_name="Mr Dupont",
    )

    print(transcript)
