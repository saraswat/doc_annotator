export interface User {
  id: number;
  email: string;
  name: string;
  avatarUrl?: string;
  oauthProvider?: string;
  oauthId?: string;
  isActive: boolean;
  isAdmin: boolean;
  createdAt: string;
  lastLogin?: string;
  passwordResetRequired?: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: User;
}