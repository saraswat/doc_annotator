import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, AuthTokens } from '../types/user';
import { authService } from '../services/auth';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (code: string, state: string) => Promise<void>;
  loginDirect: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
  refreshUserData: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Helper function to get cookie value
  const getCookie = (name: string): string | null => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      const cookieValue = parts.pop()?.split(';').shift();
      return cookieValue || null;
    }
    return null;
  };

  // Check if user is already logged in on app start
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token might be expired, try to refresh
          const refreshed = await refreshToken();
          if (!refreshed) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            // Try cookie authentication as fallback
            await tryCookieAuth();
          }
        }
      } else {
        // No token, try cookie authentication for intranet
        await tryCookieAuth();
      }
      setIsLoading(false);
    };

    const tryCookieAuth = async () => {
      const crispUser = getCookie('crisp_user');
      console.log(`🍪 Frontend: Checking for crisp_user cookie: '${crispUser}'`);
      
      if (crispUser) {
        try {
          console.log(`🚀 Frontend: Attempting cookie authentication for user: ${crispUser}`);
          const tokens = await authService.loginWithCookie();
          localStorage.setItem('access_token', tokens.accessToken);
          localStorage.setItem('refresh_token', tokens.refreshToken);
          setUser(tokens.user);
          console.log(`✅ Frontend: Cookie authentication successful for: ${tokens.user.name}`);
          toast.success(`Welcome ${tokens.user.name}! Redirecting to documents...`);
        } catch (error: any) {
          console.error('❌ Frontend: Cookie authentication failed:', error);
          console.error('❌ Error details:', {
            message: (error as any)?.message,
            response: (error as any)?.response?.data,
            status: (error as any)?.response?.status,
            statusText: (error as any)?.response?.statusText
          });
        }
      } else {
        console.log('ℹ️ Frontend: No crisp_user cookie found');
      }
    };

    initAuth();
  }, []);

  const login = async (code: string, state: string) => {
    try {
      setIsLoading(true);
      const tokens = await authService.handleOAuthCallback(code, state);
      
      // Store tokens
      localStorage.setItem('access_token', tokens.accessToken);
      localStorage.setItem('refresh_token', tokens.refreshToken);
      
      setUser(tokens.user);
      // Don't show toast here, let the component handle it
    } catch (error) {
      console.error('Login error:', error);
      toast.error('Login failed. Please try again.');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const loginDirect = (user: User, accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    toast.success('Logged out successfully');
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      if (!refreshTokenValue) {
        return false;
      }

      const newToken = await authService.refreshToken(refreshTokenValue);
      localStorage.setItem('access_token', newToken.accessToken);
      
      // Get updated user info
      const userData = await authService.getCurrentUser();
      setUser(userData);
      
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  };

  const refreshUserData = async (): Promise<void> => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    loginDirect,
    logout,
    refreshToken,
    refreshUserData,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};