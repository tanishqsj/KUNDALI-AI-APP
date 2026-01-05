from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any

from app.services.location_service import LocationService

router = APIRouter()

@router.get(
    "/locations/search",
    response_model=List[Dict[str, Any]],
    summary="Search for cities and get their coordinates"
)
async def search_locations(
    q: str = Query(..., min_length=2, description="Search query for city name (e.g., 'del', 'new york')")
):
    """
    Search for a city by name. Returns a list of matching locations
    with their display name, latitude, longitude, and timezone name.
    
    This is used to power the dynamic city selector on the frontend.
    When a user selects a city, the frontend can use the returned
    latitude, longitude, and timezone to populate the fields for
    creating a new kundali.
    """
    try:
        service = LocationService()
        results = await service.search_cities(query=q)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while searching for locations: {e}")