from mistralai import Mistral


def find_restaurants(user_prompt):
    """
    This function takes the user's prompt, wraps it in an instruction for Mistral,
    and returns a list of 5 restaurants in JSON format.
    """
    api_key = (
        "Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI"  # Make sure to handle this key securely
    )
    model = "mistral-large-latest"

    client = Mistral(api_key=api_key)

    # This is where the magic happens: we "wrap" your request.
    system_prompt = f"""
    You are a restaurant search assistant.
    Your task is to return a list of 5 restaurants that match the following request: '{user_prompt}'.
    The result must be exclusively a valid JSON object, with no text before or after.
    Each restaurant in the list must include the following keys:
    - "name": The name of the restaurant.
    - "precise_location": The full address of the restaurant.
    - "restaurant_link": The URL of the restaurant's website or Google Maps page.
    - "cuisine_type": The type of cuisine offered.
    - "price_range_per_dish": An estimate of the average price of a main dish (e.g., "15-25€").
    """

    chat_response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": system_prompt}],
        response_format={
            "type": "json_object"
        },  # This option forces Mistral to return valid JSON
    )

    return chat_response.choices[0].message.content


# Example usage with your search prompt
search_prompt = "I'm looking for a good, affordable Italian restaurant in Paris."
json_result = find_restaurants(search_prompt)
print(json_result)
