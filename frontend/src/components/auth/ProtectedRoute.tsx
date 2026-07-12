import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import LoadingSpinner from '../common/LoadingSpinner';
import type { ReactNode } from 'react';

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <LoadingSpinner fullScreen message="Loading StadiumOS AI..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return <>{children}</>;
}
