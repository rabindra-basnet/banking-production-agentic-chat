import type { AppConfig } from '@/shared/types';

export const DEFAULT_CONFIG: AppConfig = {
  bank_name: 'NepalBank AI',
  bank_tagline: 'Nepal Banking Assistant',
  bank_badge: 'NRB',
  assistant_name: 'NepalBank Assistant',
  compliance_notice: 'Nepal Rastra Bank compliant',
  supported_services: 'accounts, Fonepay QR payments, ConnectIPS transfers, or card protection',
};

const CONFIG_STORAGE_KEY = 'nepalbank_app_config_cache';
const CONFIG_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

interface CachedConfigWrapper {
  config: AppConfig;
  timestamp: number;
}

export function getCachedAppConfig(): AppConfig {
  if (typeof window === 'undefined') return DEFAULT_CONFIG;
  try {
    const raw = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (!raw) return DEFAULT_CONFIG;
    const parsed: CachedConfigWrapper = JSON.parse(raw);
    return parsed.config || DEFAULT_CONFIG;
  } catch {
    return DEFAULT_CONFIG;
  }
}

let configPromise: Promise<AppConfig> | null = null;

/**
 * Fetches SaaS configuration from backend only when cache is expired or missing.
 * Prevents redundant network / database hits on every page load.
 */
export async function fetchAppConfig(): Promise<AppConfig> {
  if (typeof window !== 'undefined') {
    try {
      const raw = localStorage.getItem(CONFIG_STORAGE_KEY);
      if (raw) {
        const parsed: CachedConfigWrapper = JSON.parse(raw);
        const age = Date.now() - parsed.timestamp;
        if (age < CONFIG_CACHE_TTL_MS && parsed.config) {
          return parsed.config;
        }
      }
    } catch {
      // Fallback to network fetch if localStorage read fails
    }
  }

  if (configPromise) return configPromise;

  configPromise = (async () => {
    try {
      const response = await fetch('/api/v1/config', {
        method: 'GET',
        credentials: 'same-origin',
      });
      if (!response.ok) return getCachedAppConfig();
      const freshConfig: AppConfig = await response.json();

      if (typeof window !== 'undefined') {
        const wrapper: CachedConfigWrapper = {
          config: freshConfig,
          timestamp: Date.now(),
        };
        localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(wrapper));
      }

      return freshConfig;
    } catch {
      return getCachedAppConfig();
    } finally {
      configPromise = null;
    }
  })();

  return configPromise;
}
