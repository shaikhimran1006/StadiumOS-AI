from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config.settings import settings
from app.domain.interfaces.external_services import IMapsService, MapRoute

logger = logging.getLogger(__name__)

GOOGLE_MAPS_BASE_URL = "https://maps.googleapis.com/maps/api"
GOOGLE_ROUTES_BASE_URL = "https://routes.googleapis.com"
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"


class GoogleMapsService(IMapsService):
    def __init__(self) -> None:
        self._api_key = settings.GOOGLE_MAPS_API_KEY
        self._client: httpx.AsyncClient | None = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        if not self._api_key:
            logger.warning("Google Maps API key not configured")
            return
        self._client = httpx.AsyncClient(timeout=30.0)
        self._initialized = True
        logger.info("GoogleMapsService initialized")

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def geocode(self, address: str) -> dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()
        params = {
            "address": address,
            "key": self._api_key,
        }

        response = await client.get(
            f"{GOOGLE_MAPS_BASE_URL}/geocode/json",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return {"error": data.get("status", "UNKNOWN_ERROR"), "results": []}

        result = data["results"][0]
        return {
            "formatted_address": result.get("formatted_address", ""),
            "latitude": result["geometry"]["location"]["lat"],
            "longitude": result["geometry"]["location"]["lng"],
            "place_id": result.get("place_id", ""),
            "address_components": result.get("address_components", []),
            "types": result.get("types", []),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def reverse_geocode(self, lat: float, lon: float) -> dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()
        params = {
            "latlng": f"{lat},{lon}",
            "key": self._api_key,
        }

        response = await client.get(
            f"{GOOGLE_MAPS_BASE_URL}/geocode/json",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return {"error": data.get("status", "UNKNOWN_ERROR"), "results": []}

        result = data["results"][0]
        return {
            "formatted_address": result.get("formatted_address", ""),
            "latitude": result["geometry"]["location"]["lat"],
            "longitude": result["geometry"]["location"]["lng"],
            "place_id": result.get("place_id", ""),
            "address_components": result.get("address_components", []),
            "types": result.get("types", []),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_directions(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str = "walking",
        avoid: list[str] | None = None,
    ) -> MapRoute:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()

        mode_map = {
            "walking": "WALK",
            "driving": "DRIVE",
            "bicycling": "BICYCLE",
            "transit": "TRANSIT",
        }
        travel_mode = mode_map.get(mode, "WALK")

        payload: dict[str, Any] = {
            "origin": {
                "location": {
                    "latLng": {"latitude": origin[0], "longitude": origin[1]}
                }
            },
            "destination": {
                "location": {
                    "latLng": {"latitude": destination[0], "longitude": destination[1]}
                }
            },
            "travelMode": travel_mode,
            "computeAlternativeRoutes": False,
            "routeModifiers": {},
        }

        if avoid:
            avoid_map = {
                "tolls": "TOLLS",
                "highways": "HIGHWAYS",
                "ferries": "FERRIES",
            }
            modifiers = [avoid_map[a] for a in avoid if a in avoid_map]
            if modifiers:
                payload["routeModifiers"]["avoidTolls"] = "TOLLS" in modifiers
                payload["routeModifiers"]["avoidHighways"] = "HIGHWAYS" in modifiers
                payload["routeModifiers"]["avoidFerries"] = "FERRIES" in modifiers

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline,routes.legs",
        }

        response = await client.post(
            f"{GOOGLE_ROUTES_BASE_URL}/v2:computeRoutes",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("routes"):
            return MapRoute(steps=[], distance_meters=0, duration_seconds=0)

        route = data["routes"][0]

        distance_meters = route.get("distanceMeters", 0)

        duration_str = route.get("duration", "0s")
        duration_seconds = 0
        if duration_str.endswith("s"):
            duration_seconds = int(duration_str[:-1])
        elif duration_str.endswith("m"):
            duration_seconds = int(duration_str[:-1]) * 60
        elif duration_str.endswith("h"):
            duration_seconds = int(duration_str[:-1]) * 3600

        polyline = ""
        if "polyline" in route:
            polyline = route["polyline"].get("encodedPolyline", "")

        steps: list[dict[str, Any]] = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                step_duration = step.get("duration", "0s")
                step_seconds = 0
                if step_duration.endswith("s"):
                    step_seconds = int(step_duration[:-1])
                steps.append({
                    "instruction": step.get("staticDuration", ""),
                    "distance_meters": step.get("distanceMeters", 0),
                    "duration_seconds": step_seconds,
                    "start_location": step.get("startLocation", {}),
                    "end_location": step.get("endLocation", {}),
                })

        return MapRoute(
            steps=steps,
            distance_meters=distance_meters,
            duration_seconds=duration_seconds,
            polyline=polyline,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def find_nearby(
        self,
        lat: float,
        lon: float,
        place_type: str,
        radius_meters: int = 1000,
    ) -> list[dict[str, Any]]:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()

        payload = {
            "includedPrimaryTypes": [place_type],
            "maxResultCount": 20,
            "locationBias": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lon},
                    "radius": float(radius_meters),
                }
            },
        }

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types,places.rating,places.primaryType",
        }

        response = await client.post(
            f"{GOOGLE_PLACES_BASE_URL}:searchNearby",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        places: list[dict[str, Any]] = []
        for place in data.get("places", []):
            display_name = place.get("displayName", {})
            location = place.get("location", {})
            places.append({
                "name": display_name.get("text", ""),
                "formatted_address": place.get("formattedAddress", ""),
                "latitude": location.get("latitude", 0),
                "longitude": location.get("longitude", 0),
                "types": place.get("types", []),
                "rating": place.get("rating"),
                "primary_type": place.get("primaryType", ""),
            })

        return places

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get_elevation(self, lat: float, lon: float) -> float:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()
        params = {
            "locations": f"{lat},{lon}",
            "key": self._api_key,
        }

        response = await client.get(
            f"{GOOGLE_MAPS_BASE_URL}/elevation/json",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return 0.0

        return data["results"][0].get("elevation", 0.0)

    async def get_distance_matrix(
        self,
        origins: list[tuple[float, float]],
        destinations: list[tuple[float, float]],
        mode: str = "walking",
    ) -> dict[str, Any]:
        if not self._initialized:
            raise RuntimeError("GoogleMapsService not initialized (no API key)")

        client = await self._ensure_client()

        origins_str = "|".join(f"{lat},{lon}" for lat, lon in origins)
        destinations_str = "|".join(f"{lat},{lon}" for lat, lon in destinations)

        params = {
            "origins": origins_str,
            "destinations": destinations_str,
            "mode": mode,
            "key": self._api_key,
        }

        response = await client.get(
            f"{GOOGLE_MAPS_BASE_URL}/distancematrix/json",
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK":
            return {"error": data.get("status", "UNKNOWN_ERROR"), "rows": []}

        return {
            "rows": data.get("rows", []),
            "status": data.get("status", "UNKNOWN"),
        }

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
