import json
import re
import os
from datetime import datetime
from mistralai import Mistral
import numpy as np

API_KEY = "VrfSiwwufNdGz1b9ekZmBsWDf1yyqqDX"
#"Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI"


def parse_time(time_str: str | None) -> str | None:
    if not time_str:
        return None
    # Tries to parse several common time formats
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
        # Finds all digits in the string and takes the first one
        found_digits = re.findall(r'\d+', str(people_str))
        if found_digits:
            return int(found_digits[0])
    except (ValueError, TypeError):
        return None
    return None

def parse_price(price_str: str | None) -> dict | None:
    if not price_str:
        return None
    numbers = [int(n) for n in re.findall(r'\d+', price_str)]
    if not numbers:
        return None
    price_data = {"min": None, "max": None}
    if len(numbers) >= 2:
        price_data["min"], price_data["max"] = min(numbers), max(numbers)
    elif len(numbers) == 1:
        # Interprets the price based on keywords present in the string
        if any(k in price_str.lower() for k in ['<', 'less', 'under', 'max', 'not more than']):
            price_data["max"] = numbers[0]
        elif any(k in price_str.lower() for k in ['>', 'more', 'over', 'min']):
            price_data["min"] = numbers[0]
        else:
            price_data["min"] = price_data["max"] = numbers[0]
    return price_data
    
def find_restaurant(user_query: str) -> str:
    """
    Analyzes a user's request for a restaurant.

    If the query has enough information, it performs a web search.
    If not, it requests the missing information.
    Once a restaurant is found, it asks for a name and time flexibility for the reservation.
    """
    api_key = API_KEY
    
    extraction_model = "mistral-large-latest"
    agent_model = "mistral-large-latest"
    
    client = Mistral(api_key=api_key)

    # Step 1: Extract information from the user query
    extraction_prompt = f"""
    You are a restaurant booking assistant. Analyze the user's request and
    extract the following information into a strict JSON format.
    The keys must be: "restaurant_type", "neighborhood", "allergies", "time",
    "date", "number_of_people", "price", "reservation_name", "time_flexibility".
    If a piece of information is not available, the value must be null. For allergies, use "no allergies" if none are mentioned.
    Do not add any text before or after the JSON object.
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
        return f"Error: Could not extract details from your request. {e}"

    # Step 2: Parse and clean the extracted data
    extracted_info['time'] = parse_time(extracted_info.get('time'))
    extracted_info['number_of_people'] = parse_people(extracted_info.get('number_of_people'))
    extracted_info['price'] = parse_price(extracted_info.get('price'))

    # Step 3: Check if all information required for the search is present
    required_fields_for_search = ["restaurant_type", "neighborhood", "date", "time", "number_of_people"]
    missing_info = [field for field in required_fields_for_search if extracted_info.get(field) is None]

    if missing_info:
        # If information is missing, ask the user for it
        message = "I have some details, but I need more information to find a restaurant. "
        
        found_details = {k.replace('_', ' '): v for k, v in extracted_info.items() if v is not None}
        if found_details:
             message += f"Here's what I understood: {json.dumps(found_details)}. "
             
        message += f"Please provide the missing details: {', '.join(missing_info).replace('_', ' ')}. Try sending all the information in one message."
        return message
    else:
        # If all search information is present, proceed with the web search
        price_info = extracted_info.get('price')
        price_msg = "any price"
        if price_info:
            if price_info.get('min') and price_info.get('max') and price_info['min'] != price_info['max']:
                price_msg = f"between {price_info['min']}€ and {price_info['max']}€"
            elif price_info.get('max'):
                price_msg = f"up to {price_info['max']}€"
            elif price_info.get('min'):
                price_msg = f"starting from {price_info['min']}€"
        
        try:
            # Create a web search agent to find a real restaurant
            websearch_agent = client.beta.agents.create(
                model=agent_model,
                name="Web Search Restaurant Finder",
                description="Agent that finds real restaurants using web search.",
                instructions="You must use your web_search tool to find one single real restaurant matching the user's request. Your final answer must be ONLY a valid JSON object with the keys 'name' and 'address' and 'phone_number'. Do not include any other text.",
                tools=[{"type": "web_search"}],
            )
            
            search_prompt = f"""
            Find a single, real, and well-rated restaurant matching these criteria:
            - Cuisine: {extracted_info.get('restaurant_type')}
            - Location/Neighborhood: {extracted_info.get('neighborhood')}
            - Price: {price_msg}
            - Note: This is a booking for {extracted_info.get('number_of_people')} people on {extracted_info.get('date')} at {extracted_info.get('time')}, try making sure there is room at this time for those persons.
            - Allergies to note: {extracted_info.get('allergies', 'None')}
            """

            response = client.beta.conversations.start(
                agent_id=websearch_agent.id,
                inputs=search_prompt
            )
        
            final_message_content = next(
                (output.content for output in response.outputs if hasattr(output, 'type') and output.type == 'message.output'),
                None  
            )
            
            if not final_message_content:
                 raise ValueError("The search agent did not return a final answer.")
            
            clean_json_str = re.sub(r'^```json\s*|\s*```$', '', final_message_content, flags=re.MULTILINE)
            restaurant_found_dict = json.loads(clean_json_str)

            name = restaurant_found_dict.get("name", "N/A")
            address = restaurant_found_dict.get("address", "N/A")
            phone_number = restaurant_found_dict.get("phone_number", "N/A")
            
            # Step 4: Check if booking information is missing
            required_fields_for_booking = ["reservation_name", "time_flexibility"]
            missing_booking_info = [field for field in required_fields_for_booking if not extracted_info.get(field)]

            if missing_booking_info:
                # If name or flexibility are missing, ask for them
                fields_to_ask = ' and '.join(missing_booking_info).replace('_', ' ')
                return (f"I found this restaurant for you: {name}, located at {address}. "
                        f"The phone number is: {phone_number}. To finalize the reservation, "
                        f"please provide your {fields_to_ask}.")
            else:
                # If all information is present, confirm the booking
                reservation_name = extracted_info.get('reservation_name')
                time_flexibility = extracted_info.get('time_flexibility')
                return (f"Thank you, {reservation_name}. Would you like me to make the reservation at {name} "
                        f"({address}, {phone_number}) for {extracted_info.get('number_of_people')} people "
                        f"on {extracted_info.get('date')} at {extracted_info.get('time')}, "
                        f"noting your time flexibility of '{time_flexibility}'?")
            
        except Exception as e:
            return f"Error: I had trouble searching for a restaurant. {e}"


'''# --- Example Usage ---

# Example 1: Initial call without booking details.
# The function should find a restaurant and then ask for the name and flexibility.
user_call_1 = "I need a reservation for an Italian place in Paris 16 for 2 people on October 19th, 2025 at 7:00 PM. Price range is 20-50€. Please note a Gluten allergy."
print("--- First Call ---")
print(find_restaurant(user_call_1))

print("\n" + "="*50 + "\n")

# Example 2: Follow-up call providing all necessary details from the start.
# The function should find a restaurant and confirm the booking directly.
user_call_2 = "I need a reservation for an Italian place in Paris 16 for 2 people on October 19th, 2025 at 7:00 PM. Price range is 20-50€, with a gluten allergy. The reservation is for Smith, and we are flexible by plus or minus 30 minutes."
print("--- Second Call (with all details) ---")
print(find_restaurant(user_call_2))'''