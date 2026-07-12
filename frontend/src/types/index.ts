export type UserRole = 'admin' | 'operator' | 'viewer' | 'security';

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  role: UserRole;
  language: string;
  createdAt: string;
  lastLogin: string;
}

export type AlertType = 'security' | 'medical' | 'fire' | 'weather' | 'crowd' | 'technical' | 'vip' | 'general';

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  description: string;
  sector?: string;
  location?: { lat: number; lng: number };
  status: 'active' | 'acknowledged' | 'resolved' | 'escalated';
  createdBy: string;
  assignedTo?: string;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
}

export type IncidentCategory = 'security' | 'medical' | 'fire' | 'structural' | 'crowd' | 'equipment' | 'weather' | 'other';

export type IncidentStatus = 'reported' | 'investigating' | 'in_progress' | 'resolved' | 'closed';

export interface Incident {
  id: string;
  category: IncidentCategory;
  title: string;
  description: string;
  sector?: string;
  location?: { lat: number; lng: number };
  status: IncidentStatus;
  priority: 'critical' | 'high' | 'medium' | 'low';
  reportedBy: string;
  assignedTo?: string;
  attachments?: string[];
  timeline: IncidentEvent[];
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
}

export interface IncidentEvent {
  id: string;
  message: string;
  createdBy: string;
  createdAt: string;
}

export interface Event {
  id: string;
  name: string;
  description: string;
  date: string;
  endDate?: string;
  type: 'match' | 'concert' | 'conference' | 'other';
  status: 'upcoming' | 'live' | 'completed' | 'cancelled';
  venue: string;
  expectedAttendance: number;
  actualAttendance?: number;
  teams?: { home: string; away: string };
  thumbnail?: string;
}

export interface Stadium {
  id: string;
  name: string;
  city: string;
  country: string;
  capacity: number;
  lat: number;
  lng: number;
  sectors: Sector[];
  imageUrl?: string;
}

export interface Sector {
  id: string;
  name: string;
  capacity: number;
  currentOccupancy: number;
  status: 'normal' | 'warning' | 'critical' | 'closed';
  alerts: Alert[];
  lat?: number;
  lng?: number;
}

export interface SectorStatus {
  id: string;
  name: string;
  occupancy: number;
  capacity: number;
  occupancyPercent: number;
  status: 'normal' | 'warning' | 'critical' | 'closed';
  activeAlerts: number;
  temperature?: number;
}

export interface Feedback {
  id: string;
  userId: string;
  rating: number;
  category: string;
  message: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  createdAt: string;
}

export interface Conversation {
  id: string;
  title: string;
  agent?: string;
  language: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export interface Message {
  id: string;
  conversationId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  agent?: string;
  sources?: string[];
  reactions?: string[];
  createdAt: string;
}

export interface ChatRequest {
  message: string;
  conversationId?: string;
  language?: string;
  agent?: string;
}

export interface ChatResponse {
  message: Message;
  conversationId: string;
  agent: string;
}

export interface DashboardMetrics {
  totalAlerts: number;
  activeAlerts: number;
  resolvedAlerts: number;
  totalIncidents: number;
  activeIncidents: number;
  totalEvents: number;
  upcomingEvents: number;
  liveEvents: number;
  occupancyRate: number;
  totalVisitors: number;
  aiInteractions: number;
  avgResponseTime: number;
  occupancyTrend: { time: string; value: number }[];
  alertsByType: { type: string; count: number }[];
  incidentsByCategory: { category: string; count: number }[];
}

export interface APIResponse<T> {
  data: T;
  message: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface MapMarker {
  id: string;
  position: { lat: number; lng: number };
  title: string;
  type: 'alert' | 'incident' | 'sector' | 'facility' | 'navigation';
  icon?: string;
  color?: string;
}

export interface Direction {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  route: { lat: number; lng: number }[];
  distance: string;
  duration: string;
  steps: DirectionStep[];
}

export interface DirectionStep {
  instruction: string;
  distance: string;
  duration: string;
  startLocation: { lat: number; lng: number };
}

export interface Place {
  id: string;
  name: string;
  address: string;
  location: { lat: number; lng: number };
  type: string;
  rating?: number;
  isOpen?: boolean;
  distance?: string;
  icon?: string;
}

export interface TranslationResponse {
  translatedText: string;
  sourceLanguage: string;
  targetLanguage: string;
}

export interface Language {
  code: string;
  name: string;
  nativeName: string;
}
