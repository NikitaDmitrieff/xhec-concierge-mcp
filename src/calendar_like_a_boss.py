from urllib.parse import quote_plus
from datetime import datetime, timedelta

def create_calendar_links(event_title, start_time, duration_hours, description, location):
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
    start_utc = start_time.strftime('%Y%m%dT%H%M%SZ')
    end_utc = end_time.strftime('%Y%m%dT%H%M%SZ')
    # Google Calendar
    link= (f"https://www.google.com/calendar/render?action=TEMPLATE"
                       f"&text={title_encoded}"
                       f"&dates={start_utc}/{end_utc}"
                       f"&details={description_encoded}"
                       f"&location={location_encoded}")

    return link


'''if __name__ == "__main__":
    # --- Utilisation ---
    event_details = {
    "event_title": "Dîner chez 'Le Grand Restaurant'",
    "start_time": datetime(2025, 10, 19, 19, 0, 0), # 19 Octobre 2025 à 19h00
    "duration_hours": 2,
    "description": "Réservation pour 2 personnes. Allergie au gluten à noter.",
    "location": "123 Rue de la Gastronomie, 75016 Paris, France"
}
    calendar_link = create_calendar_links(**event_details)

    print(f"Google: {calendar_link}")'''
