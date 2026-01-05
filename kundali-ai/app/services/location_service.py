import httpx
from typing import List, Dict, Any

class LocationService:
    """
    Service for searching locations using Open-Meteo Geocoding API.
    This API is free for non-commercial use and requires no API key.
    """

    API_URL = "https://geocoding-api.open-meteo.com/v1/search"

    async def search_cities(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for cities using Open-Meteo API.
        """
        if not query or len(query) < 2:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.API_URL,
                    params={
                        "name": query,
                        "count": 10,
                        "language": "en",
                        "format": "json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                if "results" not in data:
                    return []
                
                mapped_results = []
                for item in data.get("results", []):
                    # Construct a display name: Name, Region, Country
                    parts = [item.get("name")]
                    if item.get("admin1"):
                        parts.append(item.get("admin1"))
                    if item.get("country"):
                        parts.append(item.get("country"))
                    
                    display_name = ", ".join([p for p in parts if p])
                    
                    mapped_results.append({
                        "display_name": display_name,
                        "latitude": item.get("latitude"),
                        "longitude": item.get("longitude"),
                        "timezone": item.get("timezone", "UTC")
                    })
                
                return mapped_results

        except Exception as e:
            # Return error structure compatible with frontend
            return [{"error": "Failed to fetch location data. Please check your internet connection."}]