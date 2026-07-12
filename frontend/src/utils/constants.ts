export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  CHAT: '/chat',
  ALERTS: '/alerts',
  INCIDENTS: '/incidents',
  EVENTS: '/events',
  MAPS: '/maps',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
} as const;

export const ALERT_TYPES = [
  { value: 'security', label: 'Security', color: '#d32f2f' },
  { value: 'medical', label: 'Medical', color: '#2e7d32' },
  { value: 'fire', label: 'Fire', color: '#d32f2f' },
  { value: 'weather', label: 'Weather', color: '#0288d1' },
  { value: 'crowd', label: 'Crowd', color: '#ed6c02' },
  { value: 'technical', label: 'Technical', color: '#9e9e9e' },
  { value: 'vip', label: 'VIP', color: '#f9a825' },
  { value: 'general', label: 'General', color: '#1a237e' },
] as const;

export const INCIDENT_CATEGORIES = [
  { value: 'security', label: 'Security' },
  { value: 'medical', label: 'Medical' },
  { value: 'fire', label: 'Fire' },
  { value: 'structural', label: 'Structural' },
  { value: 'crowd', label: 'Crowd Control' },
  { value: 'equipment', label: 'Equipment' },
  { value: 'weather', label: 'Weather' },
  { value: 'other', label: 'Other' },
] as const;

export const SEVERITY_COLORS: Record<string, string> = {
  critical: '#d32f2f',
  high: '#ed6c02',
  medium: '#0288d1',
  low: '#2e7d32',
  info: '#9e9e9e',
};

export const STATUS_COLORS: Record<string, string> = {
  active: '#d32f2f',
  acknowledged: '#0288d1',
  resolved: '#2e7d32',
  escalated: '#d32f2f',
  reported: '#ed6c02',
  investigating: '#0288d1',
  in_progress: '#f9a825',
  closed: '#9e9e9e',
};

export const STADIUM_SECTORS = [
  'Sector A', 'Sector B', 'Sector C', 'Sector D',
  'Sector E', 'Sector F', 'Sector G', 'Sector H',
  'North Stand', 'South Stand', 'East Stand', 'West Stand',
  'VIP Box', 'Press Box', 'Medical Bay', 'Control Room',
] as const;

export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
  { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
  { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇧🇷' },
  { code: 'zh', name: 'Chinese', nativeName: '中文', flag: '🇨🇳' },
  { code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
] as const;

export const MAP_FACILITY_TYPES = [
  { value: 'restaurant', label: 'Food & Dining' },
  { value: 'restroom', label: 'Restrooms' },
  { value: 'hospital', label: 'Medical' },
  { value: 'parking', label: 'Parking' },
  { value: 'store', label: 'Shops' },
  { value: 'cafe', label: 'Drinks' },
] as const;

export const REFRESH_INTERVALS = {
  DASHBOARD: 30000,
  ALERTS: 15000,
  MAPS: 10000,
} as const;
