import { useEffect, useRef, useCallback, useState } from 'react';
import { Box, Paper, Typography, CircularProgress, Alert } from '@mui/material';
import { googleMapsService } from '../../services/maps/google-maps';
import type { MapMarker, SectorStatus } from '../../types';
import SectorOverlay from './SectorOverlay';

interface StadiumMapProps {
  sectors?: SectorStatus[];
  markers?: MapMarker[];
  center?: { lat: number; lng: number };
  zoom?: number;
  onMarkerClick?: (marker: MapMarker) => void;
  onSectorClick?: (sector: SectorStatus) => void;
  height?: number | string;
}

export default function StadiumMap({
  sectors = [],
  markers = [],
  center = { lat: 32.7767, lng: -96.7970 },
  zoom = 16,
  onMarkerClick,
  onSectorClick,
  height = 500,
}: StadiumMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [mapReady, setMapReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!mapRef.current) return;
    try {
      const gmap = googleMapsService.initMap(mapRef.current, center, zoom);
      if (gmap) setMapReady(true);
    } catch {
      setError('Failed to initialize map. Please check your API key.');
    }
  }, [center, zoom]);

  useEffect(() => {
    if (!mapReady) return;
    googleMapsService.clearMarkers();
    markers.forEach((m) => googleMapsService.addMarker(m));
  }, [mapReady, markers]);

  const handleMarkerClick = useCallback(
    (e: google.maps.MouseEvent) => {
      const lat = e.latLng?.lat();
      const lng = e.latLng?.lng();
      if (lat && lng) {
        const marker = markers.find(
          (m) => Math.abs(m.position.lat - lat) < 0.0001 && Math.abs(m.position.lng - lng) < 0.0001
        );
        if (marker) onMarkerClick?.(marker);
      }
    },
    [markers, onMarkerClick]
  );

  if (error) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="error">{error}</Alert>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Make sure VITE_GOOGLE_MAPS_API_KEY is set in your .env file.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ position: 'relative', overflow: 'hidden', borderRadius: 2 }}>
      <Box ref={mapRef} sx={{ width: '100%', height }} />
      {!mapReady && (
        <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(10,14,39,0.8)' }}>
          <CircularProgress sx={{ color: 'secondary.main' }} />
        </Box>
      )}
      {mapReady && sectors.length > 0 && (
        <SectorOverlay sectors={sectors} onSectorClick={onSectorClick} />
      )}
    </Paper>
  );
}
