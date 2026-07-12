from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.dependencies.getters import get_maps_service
from app.core.security.auth import TokenPayload, get_current_user
from app.services.maps.maps_service import GoogleMapsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maps", tags=["Maps"])


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=1, max_length=500)


class GeocodeResponse(BaseModel):
    formatted_address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    place_id: str = ""
    address_components: list[dict[str, Any]] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)


class DirectionsRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0)
    origin_lon: float = Field(..., ge=-180.0, le=180.0)
    destination_lat: float = Field(..., ge=-90.0, le=90.0)
    destination_lon: float = Field(..., ge=-180.0, le=180.0)
    mode: str = Field(default="walking", description="walking, driving, bicycling, transit")
    avoid: list[str] | None = Field(default=None, description="tolls, highways, ferries")


class DirectionsResponse(BaseModel):
    steps: list[dict[str, Any]] = Field(default_factory=list)
    distance_meters: float = 0.0
    duration_seconds: float = 0.0
    polyline: str | None = None


class PlacesRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    place_type: str = Field(..., min_length=1, max_length=100)
    radius_meters: int = Field(default=1000, ge=1, le=50000)


class PlacesResponse(BaseModel):
    places: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class DistanceMatrixRequest(BaseModel):
    origins: list[list[float]] = Field(..., description="List of [lat, lon] pairs")
    destinations: list[list[float]] = Field(..., description="List of [lat, lon] pairs")
    mode: str = Field(default="walking")


class DistanceMatrixResponse(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "UNKNOWN"


@router.post("/geocode", response_model=GeocodeResponse)
async def geocode_address(
    request: GeocodeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleMapsService = Depends(get_maps_service),
) -> GeocodeResponse:
    result = await service.geocode(address=request.address)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=result.get("error", "Geocoding failed"))
    return GeocodeResponse(
        formatted_address=result.get("formatted_address", ""),
        latitude=result.get("latitude", 0),
        longitude=result.get("longitude", 0),
        place_id=result.get("place_id", ""),
        address_components=result.get("address_components", []),
        types=result.get("types", []),
    )


@router.post("/directions", response_model=DirectionsResponse)
async def get_directions(
    request: DirectionsRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleMapsService = Depends(get_maps_service),
) -> DirectionsResponse:
    route = await service.get_directions(
        origin=(request.origin_lat, request.origin_lon),
        destination=(request.destination_lat, request.destination_lon),
        mode=request.mode,
        avoid=request.avoid,
    )
    return DirectionsResponse(
        steps=route.steps,
        distance_meters=route.distance_meters,
        duration_seconds=route.duration_seconds,
        polyline=route.polyline,
    )


@router.post("/places", response_model=PlacesResponse)
async def search_places(
    request: PlacesRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleMapsService = Depends(get_maps_service),
) -> PlacesResponse:
    places = await service.find_nearby(
        lat=request.latitude,
        lon=request.longitude,
        place_type=request.place_type,
        radius_meters=request.radius_meters,
    )
    return PlacesResponse(
        places=places,
        count=len(places),
    )


@router.post("/distance", response_model=DistanceMatrixResponse)
async def get_distance_matrix(
    request: DistanceMatrixRequest,
    current_user: TokenPayload = Depends(get_current_user),
    service: GoogleMapsService = Depends(get_maps_service),
) -> DistanceMatrixResponse:
    origins = [(c[0], c[1]) for c in request.origins]
    destinations = [(c[0], c[1]) for c in request.destinations]

    result = await service.get_distance_matrix(
        origins=origins,
        destinations=destinations,
        mode=request.mode,
    )
    return DistanceMatrixResponse(
        rows=result.get("rows", []),
        status=result.get("status", "UNKNOWN"),
    )
