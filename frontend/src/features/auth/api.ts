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

// ── In-Memory Access Token Storage (Guards against CSRF and XSS persistence) ──
let inMemoryAccessToken: string | null = null;
let inMemoryCsrfToken: string | null = null;

// Multi-Tab Synchronization Channel
const authBroadcast = typeof window !== 'undefined' && 'BroadcastChannel' in window
  ? new BroadcastChannel('nepalbank_auth_sync')
  : null;

if (authBroadcast) {
  authBroadcast.onmessage = (event) => {
    if (event.data?.type === 'AUTH_TOKEN_ROTATED') {
      inMemoryAccessToken = event.data.access_token;
      inMemoryCsrfToken = event.data.csrf_token;
    } else if (event.data?.type === 'AUTH_LOGGED_OUT') {
      inMemoryAccessToken = null;
      inMemoryCsrfToken = null;
      window.location.reload();
    }
  };
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken;
}

export function setAccessToken(token: string | null, csrfToken?: string | null, broadcast = true): void {
  inMemoryAccessToken = token;
  if (csrfToken !== undefined) inMemoryCsrfToken = csrfToken;

  if (broadcast && authBroadcast && token) {
    authBroadcast.postMessage({
      type: 'AUTH_TOKEN_ROTATED',
      access_token: token,
      csrf_token: inMemoryCsrfToken,
    });
  }
}

// Global Single-Flight Mutex Promise to prevent Concurrency Race Conditions
let refreshMutexPromise: Promise<string | null> | null = null;

/**
 * Executes a single atomic token refresh. All concurrent 401 callers await this single promise.
 */
export async function getFreshAccessToken(): Promise<string | null> {
  if (refreshMutexPromise) {
    return refreshMutexPromise;
  }

  refreshMutexPromise = (async () => {
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
        setAccessToken(data.access_token, data.csrf_token, true);
        return data.access_token;
      }
      return null;
    } catch {
      setAccessToken(null, null);
      return null;
    } finally {
      refreshMutexPromise = null;
    }
  })();

  return refreshMutexPromise;
}

let authCheckPromise: Promise<UserProfile | null> | null = null;

/**
 * Validates active session on page reload by hitting /api/v1/auth/refresh
 */
export async function checkAuthSession(): Promise<UserProfile | null> {
  if (authCheckPromise) return authCheckPromise;

  authCheckPromise = (async () => {
    try {
      const token = await getFreshAccessToken();
      if (!token) return null;

      const response = await fetch('/api/v1/auth/me', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        credentials: 'same-origin',
      });

      if (!response.ok) return null;

      const data: LoginResponse = await response.json();
      return {
        customerId: data.customer_id,
        name: data.name,
        email: data.email,
        role: data.role as UserProfile['role'],
        tier: data.tier as UserProfile['tier'],
        accounts: data.accounts,
      };
    } catch {
      return null;
    } finally {
      setTimeout(() => {
        authCheckPromise = null;
      }, 500);
    }
  })();

  return authCheckPromise;
}

/**
 * Authenticate customer credentials, retrieve in-memory access token, and broadcast to other tabs.
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
    setAccessToken(data.access_token, data.csrf_token, true);
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
 * Sign out user, revoke tokens on server, and notify all tabs.
 */
export async function logoutUser(): Promise<void> {
  const token = inMemoryAccessToken;
  setAccessToken(null, null, false);

  if (authBroadcast) {
    authBroadcast.postMessage({ type: 'AUTH_LOGGED_OUT' });
  }

  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }).catch(() => {});
}

/**
 * Authenticated Fetch wrapper with automatic single-flight Mutex 401 refresh retry logic.
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

  // If 401 Unauthorized, queue behind single-flight token refresh mutex
  if (response.status === 401) {
    const newToken = await getFreshAccessToken();
    if (newToken) {
      const retryHeaders = new Headers(init.headers || {});
      retryHeaders.set('Authorization', `Bearer ${newToken}`);
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
