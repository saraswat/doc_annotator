import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Paper, 
  Typography, 
  Container,
  CircularProgress
} from '@mui/material';
import { Google as GoogleIcon } from '@mui/icons-material';
import { authService } from '../../services/auth';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    try {
      setIsLoading(true);
      const response = await authService.getAuthUrl();
      
      // Redirect to OAuth provider
      window.location.href = response.authorizationUrl;
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error instanceof Error ? error.message : String(error);
      toast.error(`Login failed: ${errorMessage}`);
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      <Paper 
        elevation={3} 
        sx={{ 
          width: '100%', 
          p: 4, 
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom>
          Document Annotation System
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 4, opacity: 0.9 }}>
          A professional tool for collaborative document review and annotation.
          Sign in to start annotating documents with your team.
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Features:
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            • Text selection and highlighting
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            • Real-time collaboration
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            • Thread-based discussions
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            • Support for HTML, Markdown, and PDF
          </Typography>
        </Box>

        <Button
          variant="contained"
          size="large"
          onClick={handleLogin}
          disabled={isLoading}
          startIcon={isLoading ? <CircularProgress size={20} /> : <GoogleIcon />}
          sx={{
            bgcolor: 'white',
            color: '#1976d2',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.9)',
            },
            px: 4,
            py: 1.5,
            fontSize: '1.1rem',
          }}
        >
          {isLoading ? 'Signing in...' : 'Sign in with Google'}
        </Button>

        <Typography variant="caption" display="block" sx={{ mt: 3, opacity: 0.7 }}>
          By signing in, you agree to our terms of service and privacy policy.
        </Typography>
      </Paper>
    </Container>
  );
};

export default LoginPage;