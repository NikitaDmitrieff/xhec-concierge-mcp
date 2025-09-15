import requests
import os
import dotenv
import time

dotenv.load_dotenv()


task = f"""
You are Paige, a concierge at X-HEC Concierge, calling {{restaurant_name}} to book a table.
Ask for a table for {{number_of_people}} people. On {{date_of_reservation}} at {{time_of_reservation}}. Under the name {{reservation_name}}. If that time isn’t available, ask the closest time they can do.
Confirm the reservation name and close politely.

Example:
Restaurant: Hello?
Paige (AI): Hi, I’d like to book a table for 2 at your reastaurant. 
Restaurant: Yes sure, when would that be ?
Paige (AI): On the 15th of september at 8:00 PM. Under the name Nikita. Do you have any availability?
Restaurant: We have a table at 8:00 PM. I will book it under Nikita.
Paige (AI): Perfect, thank you very much. Have a great evening—goodbye.
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
        reservation_name: The name of the reservation
    Returns:
        The call_id on success, or raises for HTTP errors.
    """

    api_key = os.getenv("BLAND_API_KEY")

    url = "https://api.bland.ai/v1/calls"
    headers = {
        "Authorization": f"Bearer {api_key}",  # API key auth
        "Content-Type": "application/json",
    }

    first_sentence = f"""Hi, I’d like to book a table at your restaurant for {{number_of_people}}. Would that be possible ?"""

    payload = {
        "phone_number": phone_number,
        "voice": "paige",
        "task": task.format(
            restaurant_name=restaurant_name,
            number_of_people=number_of_people,
            date_of_reservation=date_of_reservation,
            time_of_reservation=time_of_reservation,
            reservation_name=reservation_name,
        ),
        "first_sentence": first_sentence.format(
            number_of_people=number_of_people,
            date_of_reservation=date_of_reservation,
            time_of_reservation=time_of_reservation,
            reservation_name=reservation_name,
        ),
        "language": "en",
        "wait_for_greeting": True,
        "interruption_threshold": 90,
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "success":
        raise RuntimeError(f"Bland API error: {data}")
    call_id = data["call_id"]
    print(f"Call started. Check back on the {call_id=} to get the transcript.")
    return f"Call started. Check back on the {call_id=} to get the transcript."


def get_call_transcript(call_id: str) -> str:
    """
    Gets the transcript of a call.
    Arguments:
        call_id: The id of the call
    Returns:
        The transcript of the call, or raises for HTTP errors.
    """
    # --- Wait for the call to complete ---
    status_url = f"https://api.bland.ai/v1/calls/{call_id}"
    deadline = time.time() + 300
    last = None
    while True:
        api_key = os.getenv("BLAND_API_KEY")

        headers = {
            "Authorization": f"Bearer {api_key}",  # API key auth
            "Content-Type": "application/json",
        }
        r = requests.get(status_url, headers=headers, timeout=15)
        r.raise_for_status()
        last = r.json()
        # Prefer the 'completed' boolean; 'status' may also be "completed"
        if last.get("completed") or last.get("status") == "success":
            break
        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for the call to complete.")
        time.sleep(2)

    summary= last["summary"] if last["summary"] else last["concatenated_transcript"]
    print(summary)
    try:
        corr = requests.get(f"{status_url}/correct", headers=headers, timeout=15)
        corr.raise_for_status()
        corrected = corr.json().get("corrected") or []
        if corrected:
            transcript = " ".join(
                seg.get("text", "").strip() for seg in corrected
            ).strip()
    except requests.RequestException:
        pass

    return f"Based on this summary of the transcript, create a google calendar link for the event if successful. Otherwise explain to the user the situation. \n\summary of the transcript: {summary}"


if __name__ == "__main__":

    phone_number = "+33601420712"

    transcript = send_bland_pathway_call(
        phone_number=phone_number,
        restaurant_name="Restaurant La Rotonde",
        number_of_people=2,
        date_of_reservation="tonight",
        time_of_reservation="8:25 PM",
        reservation_name="Mr Alexis",
    )

    call_id = transcript.split("call_id=", 1)[1].split()[0].strip("'\"")
    print(f"call_id: {call_id}")
    print(get_call_transcript(call_id))
