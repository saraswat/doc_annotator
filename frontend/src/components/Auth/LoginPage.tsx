import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Paper, 
  Typography, 
  Container,
  CircularProgress,
  TextField,
  Divider,
  Alert
} from '@mui/material';
import { Google as GoogleIcon, Lock } from '@mui/icons-material';
import { authService } from '../../services/auth';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [loginMode, setLoginMode] = useState<'oauth' | 'password'>('oauth');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { loginDirect } = useAuth();
  const navigate = useNavigate();

  const handleOAuthLogin = async () => {
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

  const handlePasswordLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await authService.loginWithPassword(email, password);
      
      loginDirect(response.user, response.accessToken, response.refreshToken);
      
      if (response.password_reset_required) {
        // Redirect to password change page
        navigate('/password-change-required');
      } else {
        // Normal login flow
        navigate('/documents');
      }
    } catch (error: any) {
      console.error('Password login error:', error);
      
      // Handle different error response formats
      let errorMessage = 'Login failed';
      if (error.response?.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.detail) {
          if (typeof error.response.data.detail === 'string') {
            errorMessage = error.response.data.detail;
          } else if (Array.isArray(error.response.data.detail)) {
            errorMessage = error.response.data.detail.map((d: any) => d.msg || d).join(', ');
          } else {
            errorMessage = 'Invalid login credentials';
          }
        } else {
          errorMessage = 'Login failed';
        }
      }
      
      setError(errorMessage);
    } finally {
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

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loginMode === 'oauth' ? (
          <Box>
            <Button
              variant="contained"
              size="large"
              onClick={handleOAuthLogin}
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
                mb: 2
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign in with Google'}
            </Button>
            
            <Box sx={{ mt: 2 }}>
              <Divider sx={{ color: 'rgba(255,255,255,0.5)', mb: 2 }}>OR</Divider>
              <Button
                variant="outlined"
                startIcon={<Lock />}
                onClick={() => setLoginMode('password')}
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.8)',
                    bgcolor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                Sign in with Password
              </Button>
            </Box>
          </Box>
        ) : (
          <Box>
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                },
                mb: 2
              }}
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              variant="outlined"
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                },
                mb: 3
              }}
            />
            <Button
              fullWidth
              variant="contained"
              size="large"
              onClick={handlePasswordLogin}
              disabled={isLoading || !email || !password}
              startIcon={isLoading ? <CircularProgress size={20} /> : <Lock />}
              sx={{
                bgcolor: 'white',
                color: '#1976d2',
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.9)',
                },
                py: 1.5,
                fontSize: '1.1rem',
                mb: 2
              }}
            >
              {isLoading ? 'Signing in...' : 'Sign in with Password'}
            </Button>
            
            <Box sx={{ mt: 2 }}>
              <Divider sx={{ color: 'rgba(255,255,255,0.5)', mb: 2 }}>OR</Divider>
              <Button
                variant="outlined"
                startIcon={<GoogleIcon />}
                onClick={() => setLoginMode('oauth')}
                sx={{
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'rgba(255,255,255,0.8)',
                    bgcolor: 'rgba(255,255,255,0.1)'
                  }
                }}
              >
                Sign in with Google
              </Button>
            </Box>
          </Box>
        )}

        <Typography variant="caption" display="block" sx={{ mt: 3, opacity: 0.7 }}>
          By signing in, you agree to our terms of service and privacy policy.
        </Typography>
      </Paper>
    </Container>
  );
};

export default LoginPage;