# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_api_key() -> str:
    """Retrieve Google Maps API key from environment."""
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    return key


def geocode_address(address: str) -> dict[str, Any]:
    """Turn a street address, city, or landmark name into geographic coordinates (latitude and longitude) using the Geocoding API.

    Args:
        address: The address or place to geocode (e.g., '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Central Park, NY').

    Returns:
        A dictionary containing the key fields:
        - address: Formatted address string
        - location: Dict with 'latitude' and 'longitude'
        - place_id: Unique Google place ID
        - status: Status code or error message
    """
    api_key = _get_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return {
            "error": "GOOGLE_MAPS_API_KEY is not configured. Please set your Maps API key in .env.",
            "status": "MISSING_API_KEY",
        }

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}

    try:
        response = httpx.get(url, params=params, timeout=10.0)
        data = response.json()

        status = data.get("status")
        if status != "OK":
            err_msg = data.get("error_message", f"Geocoding failed with status: {status}")
            logger.warning("Geocoding API error: %s", err_msg)
            return {"error": err_msg, "status": status}

        results = data.get("results", [])
        if not results:
            return {"error": "No results found for given address.", "status": "ZERO_RESULTS"}

        first = results[0]
        geometry = first.get("geometry", {})
        loc = geometry.get("location", {})

        return {
            "status": "OK",
            "name": first.get("formatted_address", address),
            "address": first.get("formatted_address", address),
            "location": {
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
            },
            "place_id": first.get("place_id"),
        }

    except Exception as e:
        logger.exception("Geocoding request failed: %s", e)
        return {"error": f"Geocoding request failed: {str(e)}", "status": "REQUEST_ERROR"}


def search_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str,
    radius_meters: float = 1500.0,
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """Search for nearby places of a given type around a coordinate using the Places API (New).

    Args:
        latitude: Center latitude coordinate (e.g. 37.7749).
        longitude: Center longitude coordinate (e.g. -122.4194).
        place_type: Type of place to search for (e.g. 'gym', 'park', 'fitness_center', 'supermarket', 'spa', 'health', 'restaurant').
        radius_meters: Search radius in meters (default 1500.0 meters, max 50000.0).
        max_results: Maximum number of places to return (default 10).

    Returns:
        A list of place dictionaries with key fields:
        - name: The human-readable display name of the place
        - address: Formatted street address
        - location: Dict with 'latitude' and 'longitude'
        - types: List of place categories/types
    """
    api_key = _get_api_key()
    if not api_key or api_key == "PASTE_KEY_HERE":
        return [
            {
                "error": "GOOGLE_MAPS_API_KEY is not configured. Please set your Maps API key in .env.",
                "status": "MISSING_API_KEY",
            }
        ]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    # Normalize place_type into includedTypes array
    # Clean string if user passes comma separated or single type
    types_list = [t.strip().lower() for t in place_type.split(",") if t.strip()]
    if not types_list:
        types_list = ["gym"]

    payload = {
        "includedTypes": types_list,
        "maxResultCount": min(max(max_results, 1), 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
        if response.status_code != 200:
            err_msg = f"Places API returned HTTP {response.status_code}: {response.text}"
            logger.warning("Places API error: %s", err_msg)
            return [{"error": err_msg, "status": f"HTTP_{response.status_code}"}]

        data = response.json()
        places_raw = data.get("places", [])
        if not places_raw:
            return []

        out: list[dict[str, Any]] = []
        for p in places_raw:
            display_name = p.get("displayName", {}).get("text", "")
            formatted_address = p.get("formattedAddress", "")
            loc = p.get("location", {})
            out.append(
                {
                    "name": display_name,
                    "address": formatted_address,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "types": p.get("types", []),
                }
            )

        return out

    except Exception as e:
        logger.exception("Places searchNearby request failed: %s", e)
        return [{"error": f"Places request failed: {str(e)}", "status": "REQUEST_ERROR"}]
