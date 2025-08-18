import { User, AuthTokens } from '../types/user';
import apiService from './api';

class AuthService {
  async getAuthUrl(): Promise<{ authorizationUrl: string; state: string }> {
    const response = await apiService.get('/auth/login');
    return {
      authorizationUrl: response.data.authorization_url,
      state: response.data.state
    };
  }

  async handleOAuthCallback(code: string, state: string): Promise<AuthTokens> {
    const formData = new FormData();
    formData.append('code', code);
    formData.append('state', state);
    
    const response = await apiService.postFormData('/auth/callback', formData);
    
    // Convert snake_case to camelCase for frontend
    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      tokenType: response.data.token_type || 'bearer',
      user: response.data.user
    };
  }

  async refreshToken(refreshToken: string): Promise<{ accessToken: string }> {
    const response = await apiService.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return {
      accessToken: response.data.access_token,
    };
  }

  async getCurrentUser(): Promise<User> {
    const response = await apiService.get('/auth/me');
    return response.data;
  }

  async logout(): Promise<void> {
    await apiService.post('/auth/logout');
  }

  async loginWithPassword(email: string, password: string): Promise<AuthTokens & { password_reset_required: boolean }> {
    const response = await apiService.post('/auth/login/password', {
      email,
      password
    });
    
    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      tokenType: response.data.token_type || 'bearer',
      user: response.data.user,
      password_reset_required: response.data.password_reset_required
    };
  }

  async changePassword(newPassword: string): Promise<void> {
    await apiService.post('/auth/password/change', {
      new_password: newPassword
    });
  }

  async loginWithCookie(): Promise<AuthTokens> {
    const response = await apiService.get('/auth/login/cookie');
    
    return {
      accessToken: response.data.access_token,
      refreshToken: response.data.refresh_token,
      tokenType: response.data.token_type || 'bearer',
      user: response.data.user
    };
  }
}

export const authService = new AuthService();