import { useState, useCallback, useEffect } from 'react';
import { useLoadScript } from '@react-google-maps/api';
import { googleMapsService } from '../services/maps/google-maps';
import type { MapMarker, Direction, Place } from '../types';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

export function useMaps(center = { lat: 32.7767, lng: -96.7970 }) {
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries: ['places', 'geometry'],
  });

  const [mapRef, setMapRef] = useState<HTMLDivElement | null>(null);
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [direction, setDirection] = useState<Direction | null>(null);
  const [nearbyPlaces, setNearbyPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoaded && mapRef) {
      googleMapsService.initMap(mapRef, center);
    }
  }, [isLoaded, mapRef, center]);

  const addMarker = useCallback((marker: MapMarker) => {
    googleMapsService.addMarker(marker);
    setMarkers((prev) => [...prev, marker]);
  }, []);

  const removeMarker = useCallback((id: string) => {
    googleMapsService.removeMarker(id);
    setMarkers((prev) => prev.filter((m) => m.id !== id));
  }, []);

  const clearMarkers = useCallback(() => {
    googleMapsService.clearMarkers();
    setMarkers([]);
  }, []);

  const getDirections = useCallback(async (destination: { lat: number; lng: number }) => {
    const start = markers[0]?.position || center;
    setLoading(true);
    try {
      const result = await googleMapsService.drawRoute(start, destination);
      setDirection(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, [markers, center]);

  const clearRoute = useCallback(() => {
    googleMapsService.clearRoute();
    setDirection(null);
  }, []);

  const searchNearby = useCallback(async (type: string) => {
    setLoading(true);
    try {
      const location = markers[0]?.position || center;
      const results = await googleMapsService.searchNearby(location, type, 500);
      setNearbyPlaces(results);
      return results;
    } finally {
      setLoading(false);
    }
  }, [markers, center]);

  return {
    isLoaded,
    loadError,
    mapRef,
    setMapRef,
    markers,
    direction,
    nearbyPlaces,
    loading,
    addMarker,
    removeMarker,
    clearMarkers,
    getDirections,
    clearRoute,
    searchNearby,
  };
}
