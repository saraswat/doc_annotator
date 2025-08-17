import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import { Lock } from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { authService } from '../../services/auth';
import { useNavigate } from 'react-router-dom';

const PasswordChangeRequired: React.FC = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { user, refreshUserData } = useAuth();
  const navigate = useNavigate();

  const handlePasswordChange = async () => {
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    try {
      setIsLoading(true);
      await authService.changePassword(newPassword);
      
      // Refresh user data to get updated password_reset_required flag
      await refreshUserData();
      
      // Redirect to main application
      navigate('/documents');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handlePasswordChange();
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
          background: 'linear-gradient(135deg, #ff7043 0%, #ff5722 100%)',
          color: 'white'
        }}
      >
        <Lock sx={{ fontSize: 48, mb: 2, opacity: 0.9 }} />
        
        <Typography variant="h4" component="h1" gutterBottom>
          Password Change Required
        </Typography>
        
        <Typography variant="body1" sx={{ mb: 1, opacity: 0.9 }}>
          Welcome, {user?.name}
        </Typography>
        
        <Typography variant="body2" sx={{ mb: 4, opacity: 0.8 }}>
          For security reasons, you must change your password before continuing.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            onKeyPress={handleKeyPress}
            margin="normal"
            variant="outlined"
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'rgba(255,255,255,0.9)',
              },
              mb: 2
            }}
          />
          
          <TextField
            fullWidth
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            onKeyPress={handleKeyPress}
            margin="normal"
            variant="outlined"
            disabled={isLoading}
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: 'rgba(255,255,255,0.9)',
              }
            }}
          />
        </Box>

        <Button
          fullWidth
          variant="contained"
          size="large"
          onClick={handlePasswordChange}
          disabled={isLoading || !newPassword || !confirmPassword}
          startIcon={isLoading ? <CircularProgress size={20} /> : <Lock />}
          sx={{
            bgcolor: 'white',
            color: '#ff5722',
            '&:hover': {
              bgcolor: 'rgba(255, 255, 255, 0.9)',
            },
            py: 1.5,
            fontSize: '1.1rem',
          }}
        >
          {isLoading ? 'Changing Password...' : 'Change Password'}
        </Button>

        <Typography variant="caption" display="block" sx={{ mt: 3, opacity: 0.7 }}>
          Choose a strong password with at least 8 characters.
        </Typography>
      </Paper>
    </Container>
  );
};

export default PasswordChangeRequired;