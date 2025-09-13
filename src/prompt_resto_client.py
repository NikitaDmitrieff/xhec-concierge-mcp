import json
import re
import os
from datetime import datetime
from mistralai import Mistral
import numpy as np

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
        if any(k in price_str.lower() for k in ['<', 'less', 'under', 'max', 'not more than']):
            price_data["max"] = numbers[0]
        elif any(k in price_str.lower() for k in ['>', 'more', 'over', 'min']):
            price_data["min"] = numbers[0]
        else:
            price_data["min"] = price_data["max"] = numbers[0]
    return price_data

def save_to_json_database(thread_id: str, new_info: dict) -> dict:
    database_file = "data/thread.json"
    try:
        with open(database_file, "r") as f:
            database = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        database = {"threads": []}

    thread_index = next((i for i, t in enumerate(database["threads"]) if t.get("id_thread") == thread_id), None)

    if thread_index is not None:
        # Merge new info into the existing thread, overwriting only if value not None
        for key, value in new_info.items():
            if value is not None:
                database["threads"][thread_index][key] = value
        merged_thread = database["threads"][thread_index]
        #print(f"Thread {thread_id} updated in {database_file}.")
    else:
        # Create a new thread structure
        merged_thread = {
            "id_thread": thread_id,
            "restaurant type": new_info.get("restaurant type"),
            "neighborhood": new_info.get("neighborhood"),
            "allergies": new_info.get("allergies"),
            "time": new_info.get("time"),
            "date": new_info.get("date"),
            "number of people": new_info.get("number of people"),
            "price": new_info.get("price"),
            "restaurant_found": new_info.get("restaurant_found")
        }
        database["threads"].append(merged_thread)
        #print(f"Thread {thread_id} created in {database_file}.")

    # Save updated database
    with open(database_file, "w") as f:
        json.dump(database, f, indent=4)

    return merged_thread
        
    

def find_restaurant(user_query: str, thread_id: str):
    if thread_id == "0":
        thread_id = str(np.random.randint(1000, 100000000))
        
    api_key = "Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI"
    extraction_model = "mistral-large-latest"
    agent_model = "mistral-large-latest"
    
    client = Mistral(api_key=api_key)

    extraction_prompt = f"""
    You are a restaurant booking assistant. Analyze the user's request and
    extract the following information into a strict JSON format.
    The keys must be: "restaurant type", "neighborhood", "allergies", "time",
    "date", "number of people", "price".
    If a piece of information is not available, the value must be null. except for alergies, where you put "no alergies"
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
        return f"Error during extraction API call: {e}"

    extracted_info['time'] = parse_time(extracted_info.get('time'))
    extracted_info['number of people'] = parse_people(extracted_info.get('number of people'))
    extracted_info['price'] = parse_price(extracted_info.get('price'))
    
    extracted_info = save_to_json_database(thread_id, extracted_info)


    missing_info = [key for key, value in extracted_info.items() if value is None and key != "restaurant_found"]
    final_output = ""

    if missing_info:
        message = "I have the following details: "
        for key, value in extracted_info.items():
            if value is not None:
                message += f"{key.replace('_', ' ')}: {value}, "
        message = message.strip(", ") + f". Could you please provide the missing information: {', '.join(missing_info)}?"
        final_output += message
        return final_output
    else:
        price_info = extracted_info.get('price')
        price_msg = "any price"
        if price_info:
            if price_info.get('min') and price_info.get('max') and price_info['min'] != price_info['max']:
                price_msg = f"between {price_info['min']}€ and {price_info['max']}€"
            elif price_info.get('max'):
                price_msg = f"up to {price_info['max']}€"
            elif price_info.get('min'):
                price_msg = f"starting from {price_info['min']}€"
        
        websearch_agent = None
        try:
            websearch_agent = client.beta.agents.create(
                model=agent_model,
                name="Web Search Restaurant Finder",
                description="Agent that finds real restaurants using web search.",
                instructions="You must use your web_search tool to find one single real restaurant matching the user's request. Your final answer must be ONLY a valid JSON object with the keys 'name', 'address', and 'website', 'phone number'. Do not include any other text.",
                tools=[{"type": "web_search"}],
            )
            
            search_prompt = f"""
            Find a single, real, and well-rated restaurant matching these criteria:
            - Cuisine: {extracted_info.get('restaurant type')}
            - Location/Neighborhood: {extracted_info.get('neighborhood')}
            - Price: {price_msg}
            - Allergies to note: {extracted_info.get('allergies', 'None')}
            """

            response = client.beta.conversations.start(
                agent_id=websearch_agent.id,
                inputs=search_prompt
            )
        

            
            final_message_content = next(
                (
                    output.content
                    for output in response.outputs
                    if hasattr(output, 'type') and output.type == 'message.output'
                ),
                None  
            )
            
            if not final_message_content:
                 raise ValueError("Agent did not return a final 'message.output' entry.")
            
            clean_json_str = re.sub(r'^```json\s*|\s*```$', '', final_message_content, flags=re.MULTILINE)
            restaurant_found_dict = json.loads(clean_json_str)

            name = restaurant_found_dict.get("name", "N/A")
            address = restaurant_found_dict.get("address", "N/A")
            
            search_result_message = (
                f"\nI found this restaurant: {name}, located at {address}. "
                f"Would you like me to make a reservation?"
            )
            final_output += search_result_message

            save_to_json_database(thread_id, {"restaurant_found": restaurant_found_dict})
            
        except Exception as e:
            final_output += f"\nError during agent conversation: {e}"
            
        return final_output + "thread_id: " + thread_id

# Create or clear the database file for a clean run
if os.path.exists("thread.json"):
    os.remove("thread.json")

#user_call_1 = " Ha oui désolé, je n'ai aucune alergies, je veux y aller le 12/11/2027 à 12H10, avec 2 personnes" 
#print(find_restaurant(user_call_1, "0"))


# print("\n" + "="*50 + "\n")

# user_call_2 = "I need a reservation for an Italian place in Paris 16 for 2 people on October 20th, 2025 at 8:00 PM. Price range is 20-50€. Please note a Gluten allergy."
# print(find_restaurant(user_call_2, "2345"))