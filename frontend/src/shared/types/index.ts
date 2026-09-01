export type CustomerTier = 'standard' | 'premium' | 'privileged';
export type UserRole = 'customer' | 'support_agent' | 'admin';

export interface AppConfig {
  bank_name: string;
  bank_tagline: string;
  bank_badge: string;
  assistant_name: string;
  compliance_notice: string;
  supported_services: string;
}

export interface UserProfile {
  customerId: string;
  name: string;
  email: string;
  role?: UserRole;
  tier: CustomerTier;
  accounts: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agent?: string;
  isStreaming?: boolean;
  latencyMs?: number;
  costUsd?: number;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  lastUpdated: string;
  messages: ChatMessage[];
}

export interface StreamEventPayload {
  event: 'agent_switch' | 'token' | 'done' | 'error';
  session_id?: string;
  agent?: string;
  delta: string;
  is_final: boolean;
  metadata?: {
    routed_agent?: string;
    cost_usd?: number;
    latency_ms?: number;
  };
}
