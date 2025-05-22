import requests

def get_pokemon(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return {
            "name": data["name"].capitalize(),
            "base_experience": data["base_experience"],
            "type": data["types"][0]["type"]["name"],
            "height": data["height"],
            "weight": data["weight"]
        }
    except requests.exceptions.RequestException:
        return None
    except KeyError:
        return None
    except Exception:
        return None