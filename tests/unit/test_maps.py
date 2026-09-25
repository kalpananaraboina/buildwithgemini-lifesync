from unittest.mock import patch, MagicMock
from app.maps_service import geocode_address, search_nearby_places


def test_geocode_missing_key():
    with patch("app.maps_service._get_api_key", return_value="PASTE_KEY_HERE"):
        res = geocode_address("1600 Amphitheatre Pkwy, Mountain View, CA")
        assert "error" in res
        assert res["status"] == "MISSING_API_KEY"


def test_geocode_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                "geometry": {
                    "location": {"lat": 37.422388, "lng": -122.0841883}
                },
                "place_id": "ChIJ2eUgeAK6j4ARbn5u_wAGqWA",
            }
        ],
    }

    with patch("app.maps_service._get_api_key", return_value="AIzaSyFakeKey123"), patch(
        "httpx.get", return_value=mock_resp
    ) as mock_get:
        res = geocode_address("1600 Amphitheatre Pkwy, Mountain View, CA")
        assert res["status"] == "OK"
        assert res["address"] == "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
        assert res["location"]["latitude"] == 37.422388
        assert res["location"]["longitude"] == -122.0841883
        assert res["place_id"] == "ChIJ2eUgeAK6j4ARbn5u_wAGqWA"
        mock_get.assert_called_once()


def test_search_nearby_places_missing_key():
    with patch("app.maps_service._get_api_key", return_value=""):
        res = search_nearby_places(37.7749, -122.4194, "gym")
        assert len(res) == 1
        assert "error" in res[0]
        assert res[0]["status"] == "MISSING_API_KEY"


def test_search_nearby_places_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "places": [
            {
                "displayName": {"text": "Equinox Sports Club", "languageCode": "en"},
                "formattedAddress": "757 Market St, San Francisco, CA 94103",
                "location": {"latitude": 37.7865, "longitude": -122.4048},
                "types": ["gym", "health", "fitness_center"],
            }
        ]
    }

    with patch("app.maps_service._get_api_key", return_value="AIzaSyFakeKey123"), patch(
        "httpx.post", return_value=mock_resp
    ) as mock_post:
        res = search_nearby_places(37.7865, -122.4048, "gym", radius_meters=1000)
        assert len(res) == 1
        item = res[0]
        assert item["name"] == "Equinox Sports Club"
        assert item["address"] == "757 Market St, San Francisco, CA 94103"
        assert item["location"]["latitude"] == 37.7865
        assert item["location"]["longitude"] == -122.4048
        assert "gym" in item["types"]

        # Check headers and endpoint verified by Developer Knowledge MCP
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://places.googleapis.com/v1/places:searchNearby"
        headers = call_args[1]["headers"]
        assert headers["X-Goog-Api-Key"] == "AIzaSyFakeKey123"
        assert "places.displayName" in headers["X-Goog-FieldMask"]
