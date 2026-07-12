import type { MapMarker, Direction, Place } from '../../types';

let googleMap: google.maps.Map | null = null;
const markers: Map<string, google.maps.Marker> = new Map();
let directionsRenderer: google.maps.DirectionsRenderer | null = null;

export const googleMapsService = {
  initMap(element: HTMLElement, center: { lat: number; lng: number }, zoom = 14): google.maps.Map {
    googleMap = new google.maps.Map(element, {
      center,
      zoom,
      disableDefaultUI: false,
      zoomControl: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
      styles: [
        { elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
        { elementType: 'labels.text.fill', stylers: [{ color: '#8ec3b9' }] },
        { elementType: 'labels.text.stroke', stylers: [{ color: '#1a3646' }] },
        { featureType: 'administrative.country', elementType: 'geometry.stroke', stylers: [{ color: '#4b6878' }] },
        { featureType: 'land', elementType: 'geometry', stylers: [{ color: '#16213e' }] },
        { featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#283e81' }] },
        { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#6f9ba5' }] },
        { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#304a7d' }] },
        { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#98a5be' }] },
        { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#2c6675' }] },
        { featureType: 'transit', elementType: 'labels.text.fill', stylers: [{ color: '#98a5be' }] },
        { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0e1626' }] },
        { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#4e6d70' }] },
      ],
    });
    directionsRenderer = new google.maps.DirectionsRenderer({ map: googleMap });
    return googleMap;
  },

  addMarker(marker: MapMarker): google.maps.Marker | null {
    if (!googleMap) return null;
    const gMarker = new google.maps.Marker({
      position: marker.position,
      map: googleMap,
      title: marker.title,
      icon: marker.icon || undefined,
    });
    const infoWindow = new google.maps.InfoWindow({ content: `<div style="color:#000;padding:8px"><strong>${marker.title}</strong><br/>Type: ${marker.type}</div>` });
    gMarker.addListener('click', () => infoWindow.open(googleMap, gMarker));
    markers.set(marker.id, gMarker);
    return gMarker;
  },

  removeMarker(id: string): void {
    const marker = markers.get(id);
    if (marker) {
      marker.setMap(null);
      markers.delete(id);
    }
  },

  clearMarkers(): void {
    markers.forEach((m) => m.setMap(null));
    markers.clear();
  },

  async drawRoute(origin: { lat: number; lng: number }, destination: { lat: number; lng: number }): Promise<Direction | null> {
    if (!googleMap || !directionsRenderer) return null;
    const directionsService = new google.maps.DirectionsService();
    return new Promise((resolve) => {
      directionsService.route(
        { origin, destination, travelMode: google.maps.TravelMode.WALKING },
        (result, status) => {
          if (status === 'OK' && result) {
            directionsRenderer!.setDirections(result);
            const route = result.routes[0];
            const leg = route.legs[0];
            resolve({
              origin,
              destination,
              route: route.overview_path.map((p) => ({ lat: p.lat(), lng: p.lng() })),
              distance: leg.distance?.text || '',
              duration: leg.duration?.text || '',
              steps: leg.steps.map((s) => ({
                instruction: s.instructions,
                distance: s.distance?.text || '',
                duration: s.duration?.text || '',
                startLocation: { lat: s.start_location.lat(), lng: s.start_location.lng() },
              })),
            });
          } else {
            resolve(null);
          }
        }
      );
    });
  },

  clearRoute(): void {
    directionsRenderer?.setDirections({ routes: [] });
  },

  async searchNearby(location: { lat: number; lng: number }, type: string, radius: number): Promise<Place[]> {
    return new Promise((resolve) => {
      if (!googleMap) { resolve([]); return; }
      const service = new google.maps.places.PlacesService(googleMap);
      service.nearbySearch(
        { location, radius, type: [type] },
        (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            resolve(
              results.map((r) => ({
                id: r.place_id || '',
                name: r.name || '',
                address: r.vicinity || '',
                location: { lat: r.geometry?.location.lat() || 0, lng: r.geometry?.location.lng() || 0 },
                type,
                rating: r.rating,
                isOpen: r.opening_hours?.isOpen(),
              }))
            );
          } else {
            resolve([]);
          }
        }
      );
    });
  },

  fitBounds(bounds: google.maps.LatLngBounds): void {
    googleMap?.fitBounds(bounds);
  },

  setCenter(center: { lat: number; lng: number }): void {
    googleMap?.setCenter(center);
  },

  setZoom(zoom: number): void {
    googleMap?.setZoom(zoom);
  },
};
