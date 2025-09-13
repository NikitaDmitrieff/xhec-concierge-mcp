import json
import re
import os
from datetime import datetime
# Corrected import to use the new, non-deprecated client
from mistralai import Mistral

# --- Helper Functions for Data Standardization (No changes here) ---

def parse_time(time_str: str | None) -> str | None:
    """Converts various time formats into a standard HH:MM format."""
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
    """Converts the number of people string to an integer."""
    if not people_str:
        return None
    try:
        found_digits = re.findall(r'\d+', str(people_str))
        if found_digits:
            return int(found_digits[0])
    except (ValueError, TypeError):
        return None
    return None

def parse_price(price_str: str | None) -> dict | None:
    """Parses a price string into a min/max dictionary."""
    if not price_str:
        return None
    numbers = [int(n) for n in re.findall(r'\d+', price_str)]
    if not numbers:
        return None
    price_data = {"min": None, "max": None}
    if len(numbers) >= 2:
        price_data["min"], price_data["max"] = min(numbers), max(numbers)
    elif len(numbers) == 1:
        if any(k in price_str.lower() for k in ['<', 'less', 'under', 'max', 'not more than']):
            price_data["max"] = numbers[0]
        elif any(k in price_str.lower() for k in ['>', 'more', 'over', 'min']):
            price_data["min"] = numbers[0]
        else:
            price_data["min"] = price_data["max"] = numbers[0]
    return price_data

# --- Main Function ---

def find_restaurant(user_query: str):
    """
    Uses Mistral AI to first extract reservation details and then find a restaurant.
    """
    # IMPORTANT: It is highly recommended to use environment variables for API keys.
    # For example: api_key = os.environ.get("MISTRAL_API_KEY")
    api_key = "Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI"  # <--- PLACE YOUR API KEY HERE
    model = "mistral-large-latest"

    if api_key == "YOUR_MISTRAL_API_KEY" or not api_key:
        return "Error: Please replace 'YOUR_MISTRAL_API_KEY' with your actual Mistral API key."

    # Use the new Mistral class for the client
    client = Mistral(api_key=api_key)

    # --- STEP 1: Extract Information from User Query ---
    extraction_prompt = f"""
    You are a restaurant booking assistant. Analyze the user's request and
    extract the following information into a strict JSON format.
    The keys must be: "restaurant type", "neighborhood", "allergies", "time",
    "date", "number of people", "price".
    If a piece of information is not available, the value must be null.
    Do not add any text before or after the JSON object.

    User request: "{user_query}"
    """
    try:
        # Use the new client.chat.complete method
        extraction_response = client.chat.complete(
            model=model,
            messages=[{"role": "user", "content": extraction_prompt}],
            response_format={"type": "json_object"}
        )
        extracted_info = json.loads(extraction_response.choices[0].message.content)
    except Exception as e:
        return f"Error during extraction API call: {e}"

    # --- STEP 2: Standardize the Extracted Data ---
    extracted_info['time'] = parse_time(extracted_info.get('time'))
    extracted_info['number of people'] = parse_people(extracted_info.get('number of people'))
    extracted_info['price'] = parse_price(extracted_info.get('price'))

    # --- STEP 3: Check for Missing Information ---
    missing_info = [key for key, value in extracted_info.items() if value is None]
    final_output = "json: " + json.dumps(extracted_info, indent=4) + "\n"

    if missing_info:
        message = "message: I have the following details: "
        for key, value in extracted_info.items():
            if value is not None:
                message += f"{key.replace('_', ' ')}: {value}, "
        message = message.strip(", ") + f". Could you please provide the missing information: {', '.join(missing_info)}?"
        final_output += message
        return final_output
    else:
        # --- STEP 4: All Info Present, Now Search for a Restaurant ---
        price_info = extracted_info.get('price')
        price_msg = "any price"
        if price_info:
            if price_info.get('min') and price_info.get('max') and price_info['min'] != price_info['max']:
                price_msg = f"between {price_info['min']}€ and {price_info['max']}€"
            elif price_info.get('max'):
                price_msg = f"up to {price_info['max']}€"
            elif price_info.get('min'):
                price_msg = f"starting from {price_info['min']}€"

        confirmation_message = (
            f"message: Great! I have all the details. I am now searching for a "
            f"{extracted_info.get('restaurant type')} restaurant in "
            f"{extracted_info.get('neighborhood')} for "
            f"{extracted_info.get('number of people')} people on "
            f"{extracted_info.get('date')} at {extracted_info.get('time')} "
            f"with a budget {price_msg} and noting allergies: {extracted_info.get('allergies', 'None')}."
        )
        final_output += confirmation_message

        search_prompt = f"""
        You are a restaurant search engine. Your task is to find 3 REAL restaurant. MAKE SURE THE RESATURANTs EXIST AND THE LINK IS VALID, iterate until you find one.
        that best matches the user's criteria listed below. Once you have 3, find the one that exist 100% sure and provide it.
        The result must be exclusively a valid JSON object with the keys "name", "address".
        Do not add any text before or after the JSON object. 

        Criteria:
        - Cuisine: {extracted_info.get('restaurant type')}
        - Location/Neighborhood: {extracted_info.get('neighborhood')}
        - Price: {price_msg}
        - Allergies to note: {extracted_info.get('allergies', 'None')}
        """

        try:
            # Use the new client.chat.complete method for the search as well
            search_response = client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": search_prompt}],
                response_format={"type": "json_object"}
            )
            restaurant_found = json.loads(search_response.choices[0].message.content)
            final_output += "\n--- Search Result ---"
            final_output += f"\nI have found a matching restaurant: {json.dumps(restaurant_found, indent=4)}"
            final_output += "\nWould you like me to book it?"
        except Exception as e:
            final_output += f"\nError during search API call: {e}"

        return final_output

# --- EXAMPLES ---

# Example 1: User provides partial information
user_call_1 = "find me a restaurant close to Montparnasse, a Chinese one, not more than 30€, I have no alergies"
print(find_restaurant(user_call_1))

print("\n" + "="*50 + "\n")

# Example 2: User provides all necessary information
user_call_2 = "I need a reservation for an Italian place in Paris 16 for 2 people on October 20th, 2025 at 8:00 PM. Price range is 20-50€. Please note a Gluten allergy."
print(find_restaurant(user_call_2))