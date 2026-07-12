import { Box, Grid, Typography } from '@mui/material';
import StadiumMap from '../components/maps/StadiumMap';
import NavigationPanel from '../components/maps/NavigationPanel';
import NearbyPlaces from '../components/maps/NearbyPlaces';
import { useMaps } from '../hooks/useMaps';

export default function MapsPage() {
  const { isLoaded, loadError, mapRef, setMapRef, markers, direction, nearbyPlaces, loading, getDirections, clearRoute, searchNearby } = useMaps();

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Maps & Navigation</Typography>
        <Typography variant="body2" color="text.secondary">Interactive stadium map with navigation and facilities</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <StadiumMap
            markers={markers}
            height={600}
          />
        </Grid>
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <NavigationPanel
              direction={direction}
              onGetDirections={getDirections}
              onClearRoute={clearRoute}
              loading={loading}
            />
            <NearbyPlaces
              places={nearbyPlaces}
              loading={loading}
              onSearch={searchNearby}
            />
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
