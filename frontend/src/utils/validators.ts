import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const alertSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().min(1, 'Description is required').max(2000),
  type: z.enum(['security', 'medical', 'fire', 'weather', 'crowd', 'technical', 'vip', 'general']),
  severity: z.enum(['critical', 'high', 'medium', 'low', 'info']),
  sector: z.string().optional(),
});

export const incidentSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().min(1, 'Description is required').max(2000),
  category: z.enum(['security', 'medical', 'fire', 'structural', 'crowd', 'equipment', 'weather', 'other']),
  priority: z.enum(['critical', 'high', 'medium', 'low']),
  sector: z.string().optional(),
});

export const eventSchema = z.object({
  name: z.string().min(1, 'Event name is required').max(200),
  description: z.string().min(1, 'Description is required').max(2000),
  date: z.string().min(1, 'Date is required'),
  type: z.enum(['match', 'concert', 'conference', 'other']),
  venue: z.string().min(1, 'Venue is required'),
  expectedAttendance: z.number().min(0, 'Must be a positive number'),
});

export const feedbackSchema = z.object({
  rating: z.number().min(1, 'Rating is required').max(5),
  category: z.string().min(1, 'Category is required'),
  message: z.string().min(10, 'Message must be at least 10 characters').max(2000),
});

export const settingsSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  language: z.string().min(2, 'Language is required'),
  theme: z.enum(['dark', 'light']),
  notifications: z.object({
    email: z.boolean(),
    push: z.boolean(),
    sms: z.boolean(),
  }),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type AlertFormData = z.infer<typeof alertSchema>;
export type IncidentFormData = z.infer<typeof incidentSchema>;
export type EventFormData = z.infer<typeof eventSchema>;
export type FeedbackFormData = z.infer<typeof feedbackSchema>;
