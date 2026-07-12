import { Card, CardContent, Typography, Box, List, ListItem, ListItemIcon, ListItemText, Chip, ToggleButton, ToggleButtonGroup } from '@mui/material';
import { Restaurant, Wc, LocalHospital, LocalParking, Store, WaterDrop } from '@mui/icons-material';
import type { Place } from '../../types';
import { useState } from 'react';

interface NearbyPlacesProps {
  places: Place[];
  loading?: boolean;
  onSearch: (type: string) => void;
}

const placeTypes = [
  { value: 'restaurant', label: 'Food', icon: <Restaurant fontSize="small" /> },
  { value: 'restroom', label: 'Restrooms', icon: <Wc fontSize="small" /> },
  { value: 'hospital', label: 'Medical', icon: <LocalHospital fontSize="small" /> },
  { value: 'parking', label: 'Parking', icon: <LocalParking fontSize="small" /> },
  { value: 'store', label: 'Shops', icon: <Store fontSize="small" /> },
  { value: 'cafe', label: 'Drinks', icon: <WaterDrop fontSize="small" /> },
];

export default function NearbyPlaces({ places, loading, onSearch }: NearbyPlacesProps) {
  const [selectedType, setSelectedType] = useState('restaurant');

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Nearby Facilities</Typography>

        <ToggleButtonGroup
          value={selectedType}
          exclusive
          onChange={(_, val) => { if (val) { setSelectedType(val); onSearch(val); } }}
          size="small"
          fullWidth
          sx={{ mb: 2, flexWrap: 'wrap' }}
        >
          {placeTypes.map((pt) => (
            <ToggleButton key={pt.value} value={pt.value} sx={{ flex: '1 1 auto', py: 0.5 }}>
              {pt.icon} <Typography variant="caption" sx={{ ml: 0.5 }}>{pt.label}</Typography>
            </ToggleButton>
          ))}
        </ToggleButtonGroup>

        {loading && (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="caption" color="text.secondary">Searching...</Typography>
          </Box>
        )}

        {!loading && places.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="caption" color="text.secondary">
              Click a category to find nearby facilities
            </Typography>
          </Box>
        )}

        {!loading && places.length > 0 && (
          <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
            {places.map((place) => (
              <ListItem key={place.id} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: place.isOpen !== false ? '#2e7d32' : '#616161' }} />
                </ListItemIcon>
                <ListItemText
                  primary={<Typography variant="body2" fontWeight={500}>{place.name}</Typography>}
                  secondary={
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">{place.address}</Typography>
                      {place.rating && (
                        <Chip label={`★ ${place.rating}`} size="small" sx={{ height: 18, fontSize: '0.6rem' }} />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
}
