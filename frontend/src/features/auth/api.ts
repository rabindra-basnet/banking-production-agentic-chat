import type { UserProfile } from '@/shared/types';

export interface LoginResponse {
  access_token?: string;
  csrf_token?: string;
  customer_id: string;
  name: string;
  email: string;
  role?: string;
  tier: string;
  accounts: string[];
}

// ── In-Memory Access Token Storage (Guards against CSRF and XSS token persistence) ──
let inMemoryAccessToken: string | null = null;
let inMemoryCsrfToken: string | null = null;

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setAccessToken(token: string | null, csrfToken?: string | null): void {
  inMemoryAccessToken = token;
  if (csrfToken !== undefined) inMemoryCsrfToken = csrfToken;
}

let authCheckPromise: Promise<UserProfile | null> | null = null;

/**
 * Validates active session on page reload or token expiry by hitting /api/v1/auth/refresh
 * (Only endpoint accepting the secure HttpOnly refresh cookie).
 */
export async function checkAuthSession(): Promise<UserProfile | null> {
  if (authCheckPromise) return authCheckPromise;

  authCheckPromise = (async () => {
    try {
      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        setAccessToken(null, null);
        return null;
      }

      const data: LoginResponse = await response.json();
      if (data.access_token) {
        setAccessToken(data.access_token, data.csrf_token);
      }

      return {
        customerId: data.customer_id,
        name: data.name,
        email: data.email,
        role: data.role as UserProfile['role'],
        tier: data.tier as UserProfile['tier'],
        accounts: data.accounts,
      };
    } catch {
      setAccessToken(null, null);
      return null;
    } finally {
      setTimeout(() => {
        authCheckPromise = null;
      }, 1000);
    }
  })();

  return authCheckPromise;
}

/**
 * Authenticate customer credentials, retrieve in-memory access token, and set HttpOnly refresh cookie.
 */
export async function loginUser(username: string, password?: string): Promise<UserProfile> {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    body: JSON.stringify({
      username,
      password: password || 'password123',
    }),
  });

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || errData.message || 'Authentication failed. Please verify credentials.');
  }

  const data: LoginResponse = await response.json();
  if (data.access_token) {
    setAccessToken(data.access_token, data.csrf_token);
  }

  return {
    customerId: data.customer_id,
    name: data.name,
    email: data.email,
    role: data.role as UserProfile['role'],
    tier: data.tier as UserProfile['tier'],
    accounts: data.accounts,
  };
}

/**
 * Sign out user, revoke tokens on server, and clear in-memory state.
 */
export async function logoutUser(): Promise<void> {
  const token = inMemoryAccessToken;
  setAccessToken(null, null);

  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }).catch(() => {});
}

/**
 * Authenticated Fetch wrapper with automatic 401 refresh retry logic.
 */
export async function authenticatedFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers || {});
  
  if (inMemoryAccessToken) {
    headers.set('Authorization', `Bearer ${inMemoryAccessToken}`);
  }
  if (inMemoryCsrfToken) {
    headers.set('X-CSRF-Token', inMemoryCsrfToken);
  }

  let response = await fetch(input, {
    ...init,
    headers,
    credentials: 'same-origin',
  });

  // If 401 Unauthorized, automatically attempt access token refresh once
  if (response.status === 401) {
    const refreshed = await checkAuthSession();
    if (refreshed && inMemoryAccessToken) {
      const retryHeaders = new Headers(init.headers || {});
      retryHeaders.set('Authorization', `Bearer ${inMemoryAccessToken}`);
      if (inMemoryCsrfToken) retryHeaders.set('X-CSRF-Token', inMemoryCsrfToken);

      response = await fetch(input, {
        ...init,
        headers: retryHeaders,
        credentials: 'same-origin',
      });
    }
  }

  return response;
}
