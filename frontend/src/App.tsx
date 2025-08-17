import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';

// Components
import Layout from './components/Layout/Layout';
import MainLayout from './components/Layout/MainLayout';
import LoginPage from './components/Auth/LoginPage';
import OAuthCallback from './components/Auth/OAuthCallback';
import ProtectedRoute from './components/Auth/ProtectedRoute';
import DocumentListWithLayout from './components/DocumentViewer/DocumentListWithLayout';
import DocumentViewerWithLayout from './components/DocumentViewer/DocumentViewerWithLayout';
import DocumentSelector from './components/DocumentSelector/DocumentSelector';
import AdminDashboard from './components/Admin/AdminDashboard';
import PasswordChangeRequired from './components/Auth/PasswordChangeRequired';

// Contexts
import { AuthProvider } from './contexts/AuthContext';
import { DocumentProvider } from './contexts/DocumentContext';
import { AnnotationProvider } from './contexts/AnnotationContext';

function App() {
  return (
    <AuthProvider>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/auth/callback" element={<OAuthCallback />} />
          
          {/* Password change required route */}
          <Route path="/password-change-required" element={
            <ProtectedRoute>
              <PasswordChangeRequired />
            </ProtectedRoute>
          } />
          
          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Navigate to="/selector" replace />
            </ProtectedRoute>
          } />
          
          <Route path="/documents" element={
            <ProtectedRoute>
              <DocumentProvider>
                <DocumentListWithLayout />
              </DocumentProvider>
            </ProtectedRoute>
          } />
          
          <Route path="/selector" element={
            <ProtectedRoute>
              <DocumentProvider>
                <MainLayout>
                  <DocumentSelector />
                </MainLayout>
              </DocumentProvider>
            </ProtectedRoute>
          } />
          
          <Route path="/documents/:documentId" element={
            <ProtectedRoute>
              <DocumentProvider>
                <AnnotationProvider>
                  <DocumentViewerWithLayout />
                </AnnotationProvider>
              </DocumentProvider>
            </ProtectedRoute>
          } />
          
          <Route path="/admin" element={
            <ProtectedRoute>
              <MainLayout>
                <AdminDashboard />
              </MainLayout>
            </ProtectedRoute>
          } />
          
          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </AuthProvider>
  );
}

export default App;