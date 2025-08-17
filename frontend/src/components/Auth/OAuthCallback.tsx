import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Container } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

const OAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [processed, setProcessed] = useState(false);

  useEffect(() => {
    const handleCallback = async () => {
      if (processed) return; // Prevent multiple callback processing
      setProcessed(true);
      
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const error = searchParams.get('error');

      if (error) {
        setStatus('error');
        toast.error(`Authentication error: ${error}`);
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (!code || !state) {
        setStatus('error');
        toast.error('Missing authentication parameters');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      try {
        await login(code, state);
        setStatus('success');
        toast.success('Successfully signed in!');
        navigate('/documents');
      } catch (error) {
        setStatus('error');
        console.error('OAuth callback error:', error);
        const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
        
        // Check for specific OAuth errors
        if (errorMessage.includes('expired') || errorMessage.includes('used already')) {
          toast.error('Authentication session expired. Please sign in again.');
        } else {
          toast.error(`Authentication failed: ${errorMessage}`);
        }
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, login, navigate, processed]);

  const renderContent = () => {
    switch (status) {
      case 'processing':
        return (
          <>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Completing sign-in...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we verify your authentication.
            </Typography>
          </>
        );
      case 'success':
        return (
          <>
            <Typography variant="h6" gutterBottom color="success.main">
              Sign-in successful!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redirecting to your documents...
            </Typography>
          </>
        );
      case 'error':
        return (
          <>
            <Typography variant="h6" gutterBottom color="error.main">
              Sign-in failed
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Redirecting to login page...
            </Typography>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="sm" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      <Box sx={{ 
        width: '100%', 
        textAlign: 'center',
        p: 4,
        border: '1px solid #e0e0e0',
        borderRadius: 2,
        bgcolor: 'background.paper'
      }}>
        {renderContent()}
      </Box>
    </Container>
  );
};

export default OAuthCallback;