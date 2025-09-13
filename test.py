# Ne rajoute pas d'import de modules pour le moment
from mistralai import Mistral

def trouver_restaurants(prompt_utilisateur):
    """
    Cette fonction prend le prompt de l'utilisateur, l'enveloppe dans une instruction
    pour Mistral afin d'obtenir une liste de 5 restaurants au format JSON.
    """
    api_key = "Ry2yuGs2RqXlNWnxJDvtBK8xQjBIv9lI"  # Pense à gérer cette clé de manière sécurisée
    model = "mistral-large-latest"

    client = Mistral(api_key=api_key)

    # C'est ici que la magie opère : on "enveloppe" ta demande.
    prompt_systeme = f"""
    Tu es un assistant de recherche de restaurants.
    Ta mission est de me retourner une liste de 5 restaurants qui correspondent à la demande suivante : '{prompt_utilisateur}'.
    Le résultat doit être exclusivement un objet JSON valide, sans aucun texte avant ou après.
    Chaque restaurant dans la liste doit contenir les clés suivantes :
    - "nom": Le nom du restaurant.
    - "localisation_precise": L'adresse complète du restaurant.
    - "lien_restaurant": L'URL du site web ou de la page Google Maps du restaurant.
    - "type_cuisine": Le type de cuisine proposé.
    - "ordre_de_prix_plat": Une estimation du prix moyen d'un plat principal (par exemple : "15-25€").
    """

    chat_response = client.chat.complete(
        model=model,
        messages=[{"role": "user", "content": prompt_systeme}],
        response_format={"type": "json_object"} # Cette option force Mistral à retourner du JSON valide
    )

    return chat_response.choices[0].message.content

# Exemple d'utilisation avec ton prompt type
prompt_de_recherche = "Je cherche un bon restaurant italien à Paris, plutôt abordable."
resultat_json = trouver_restaurants(prompt_de_recherche)

print(resultat_json)