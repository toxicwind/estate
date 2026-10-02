// Shared types and interfaces for the sovereign TypeScript codebase
// This file provides common definitions used across the codebase

export interface AuthContext {
  /** Unique identifier for the authentication context */
  id: string;
  /** User role/permission level */
  role: string;
  /** Timestamp of last authentication activity */
  lastActive: number;
  /** Whether the user is currently authenticated */
  isAuthenticated: boolean;
}

export interface TokenPayload {
  /** JWT or similar token payload */
  token: string;
  /** Issuer of the token */
  issuer: string;
  /** Expiration time */
  exp: number;
  /** Subject (user ID) */
  subject: string;
}

export interface AuthResult {
  /** Success indicator */
  success: boolean;
  /** Error message if operation failed */
  error?: string;
  /** Authentication status */
  status: 'valid' | 'invalid' | 'pending';
}

export interface SessionInfo {
  /** Current session identifier */
  sessionId: string;
  /** Total duration of the session in milliseconds */
  durationMs: number;
  /** Whether the session is active */
  isActive: boolean;
}

export type AuthMethod = 'login' | 'refresh' | 'logout' | 'verify';

export type SecurityLevel = 'low' | 'medium' | 'high' | 'critical';
