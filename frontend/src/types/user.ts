export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  oauthProvider: string;
  oauthId: string;
  isActive: boolean;
  isAdmin: boolean;
  createdAt: Date;
  lastLogin?: Date;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: User;
}