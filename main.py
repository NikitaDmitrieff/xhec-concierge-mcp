"""
MCP Server Template
"""

from mcp.server.fastmcp import FastMCP
from pydantic import Field

import mcp.types as types
from mistralai import Mistral
from dotenv import load_dotenv


load_dotenv()

mcp = FastMCP("Echo Server", port=3000, stateless_http=True, debug=True)


@mcp.tool(
    title="Echo Tool",
    description="Echo the input text",
)
def echo(text: str = Field(description="The text to echo")) -> str:
    return text

@mcp.tool(
    title="Fetch restaurant suggestions",
    description="Fetch restaurant suggestions from Mistral",
)
def trouver_restaurants(prompt_utilisateur):
    """
    Cette fonction prend le prompt de l'utilisateur, l'enveloppe dans une instruction
    pour Mistral afin d'obtenir une liste de 5 restaurants au format JSON.
    """
      # Pense à gérer cette clé de manière sécurisée
    model = "mistral-large-latest"

    client = Mistral(api_key=env.get("MISTRAL_API_KEY"))

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
        response_format={"type": "json_object"}
    )

    return chat_response.choices[0].message.content


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

