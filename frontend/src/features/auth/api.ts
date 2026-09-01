import type { UserProfile } from '@/shared/types';

export interface LoginResponse {
  customer_id: string;
  name: string;
  email: string;
  role?: string;
  tier: string;
  accounts: string[];
}

let authCheckPromise: Promise<UserProfile | null> | null = null;

export async function checkAuthSession(): Promise<UserProfile | null> {
  if (authCheckPromise) return authCheckPromise;

  authCheckPromise = (async () => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        method: 'GET',
        credentials: 'same-origin',
      });

      if (!response.ok) {
        return null;
      }

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
      // Reset after resolution so subsequent manual checks can re-query
      setTimeout(() => {
        authCheckPromise = null;
      }, 1000);
    }
  })();

  return authCheckPromise;
}

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
    throw new Error(errData.detail || 'Authentication failed. Please verify credentials.');
  }

  const data: LoginResponse = await response.json();
  const profile: UserProfile = {
    customerId: data.customer_id,
    name: data.name,
    email: data.email,
    role: data.role as UserProfile['role'],
    tier: data.tier as UserProfile['tier'],
    accounts: data.accounts,
  };

  // Cache user profile locally so reloads are instantaneous
  localStorage.setItem('nepalbank_user', JSON.stringify(profile));
  return profile;
}

export async function logoutUser(): Promise<void> {
  localStorage.removeItem('nepalbank_user');
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
  }).catch(() => {});
}
