import apiClient from './client';
import type { Direction, Place } from '../../types';

export const mapsApi = {
  async geocode(address: string): Promise<{ lat: number; lng: number }> {
    const { data } = await apiClient.get('/maps/geocode', { params: { address } });
    return data;
  },

  async reverseGeocode(lat: number, lng: number): Promise<string> {
    const { data } = await apiClient.get('/maps/reverse-geocode', { params: { lat, lng } });
    return data;
  },

  async getDirections(origin: { lat: number; lng: number }, destination: { lat: number; lng: number }): Promise<Direction> {
    const { data } = await apiClient.get('/maps/directions', {
      params: { originLat: origin.lat, originLng: origin.lng, destLat: destination.lat, destLng: destination.lng },
    });
    return data;
  },

  async searchNearby(location: { lat: number; lng: number }, type: string, radius = 500): Promise<Place[]> {
    const { data } = await apiClient.get('/maps/nearby', {
      params: { lat, lng, type, radius },
    });
    return data;
  },

  async getStadiumMap(stadiumId: string): Promise<{ sectors: { id: string; path: { lat: number; lng: number }[]; name: string }[] }> {
    const { data } = await apiClient.get(`/maps/stadium/${stadiumId}`);
    return data;
  },
};
