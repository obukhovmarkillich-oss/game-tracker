import requests
from config import RAWG_API_KEY, RAWG_BASE_URL


def search_games(query: str, limit: int = 10) -> list:
    if not RAWG_API_KEY:
        return []
    params = {"key": RAWG_API_KEY, "search": query, "limit": limit}
    response = requests.get(f"{RAWG_BASE_URL}/games", params=params)
    response.raise_for_status()
    data = response.json()
    return [
        {
            "id": game["id"],
            "name": game["name"],
            "released": game.get("released"),
            "background_image": game.get("background_image"),
            "genres": [g["name"] for g in game.get("genres", []) or []],
            "platforms": [p["platform"]["name"] for p in game.get("platforms", []) or []],
        }
        for game in data.get("results", [])
    ]


def get_game_details(rawg_id: int) -> dict:
    if not RAWG_API_KEY:
        return {}
    response = requests.get(f"{RAWG_BASE_URL}/games/{rawg_id}", params={"key": RAWG_API_KEY})
    response.raise_for_status()
    data = response.json()
    return {
        "id": data["id"],
        "name": data["name"],
        "released": data.get("released"),
        "background_image": data.get("background_image"),
        "genres": [g["name"] for g in data.get("genres", [])],
        "platforms": [p["platform"]["name"] for p in data.get("platforms", [])],
        "description": data.get("description"),
        "metacritic": data.get("metacritic"),
    }
