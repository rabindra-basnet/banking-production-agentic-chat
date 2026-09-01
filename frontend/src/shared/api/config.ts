import type { AppConfig } from '@/shared/types';

export const DEFAULT_CONFIG: AppConfig = {
  bank_name: 'NepalBank AI',
  bank_tagline: 'Nepal Banking Assistant',
  bank_badge: 'NRB',
  assistant_name: 'NepalBank Assistant',
  compliance_notice: 'Nepal Rastra Bank compliant',
  supported_services: 'accounts, Fonepay QR payments, ConnectIPS transfers, or card protection',
};

let configPromise: Promise<AppConfig> | null = null;

export async function fetchAppConfig(): Promise<AppConfig> {
  if (configPromise) return configPromise;

  configPromise = (async () => {
    try {
      const response = await fetch('/api/v1/config', {
        method: 'GET',
        credentials: 'same-origin',
      });
      if (!response.ok) return DEFAULT_CONFIG;
      return await response.json();
    } catch {
      return DEFAULT_CONFIG;
    }
  })();

  return configPromise;
}
