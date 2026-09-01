import { useState } from 'react';
import { 
  Landmark, 
  Fingerprint, 
  User, 
  KeyRound, 
  ShieldAlert, 
  ArrowRight, 
  Shield 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { UserProfile, AppConfig } from '@/shared/types';
import { loginUser } from '../api';

const PRESET_HINTS = [
  { label: 'Standard Customer', username: 'CIF908123', name: 'Rabindra Basnet (Standard)', pass: 'password123' },
  { label: 'Premium Customer', username: 'CIF908456', name: 'Sita Shrestha (Premium)', pass: 'password123' },
  { label: 'Privileged / Admin', username: 'admin', name: 'Prashant Thapa / Admin', pass: 'password123' },
];

interface LoginFormProps {
  config: AppConfig;
  onSuccess: (profile: UserProfile) => void;
}

export function LoginForm({ config, onSuccess }: LoginFormProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e?: React.FormEvent, customUser?: string, customPass?: string) => {
    if (e) e.preventDefault();
    const userToSubmit = customUser || username.trim();
    const passToSubmit = customPass || password;

    if (!userToSubmit) {
      setError('Please enter your Customer ID, Email, or Admin username.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const profile = await loginUser(userToSubmit, passToSubmit);
      onSuccess(profile);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-100 flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Background Ambient Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[32rem] h-[32rem] bg-emerald-600/10 blur-[130px] rounded-full pointer-events-none" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Dynamic SaaS Header Branding */}
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-600 shadow-xl shadow-emerald-500/20 mb-2">
            <Landmark className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center justify-center gap-2">
            <span>{config.bank_name}</span>
            <Badge variant="default">{config.bank_badge}</Badge>
          </h1>
          <p className="text-xs text-slate-400">
            {config.bank_tagline} & Secure Sign-In
          </p>
        </div>

        {/* Shadcn Card Login Form */}
        <Card className="space-y-5">
          <CardHeader className="pb-3 border-b border-slate-800 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Fingerprint className="w-4 h-4 text-emerald-400" />
              <span>Account Authentication</span>
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span>Username / Customer ID / Email</span>
                </label>
                <Input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. admin, CIF908123, or user@example.com"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                  <KeyRound className="w-3.5 h-3.5 text-slate-400" />
                  <span>Password</span>
                </label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                />
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-300 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-11"
              >
                <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </form>

            {/* Quick Demo Autofill Chips */}
            <div className="pt-3 border-t border-slate-800 space-y-2">
              <span className="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">
                Quick Fill Profiles:
              </span>
              <div className="grid grid-cols-3 gap-2">
                {PRESET_HINTS.map((h, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => {
                      setUsername(h.username);
                      setPassword(h.pass);
                    }}
                    className="p-2 rounded-lg bg-slate-950/80 hover:bg-slate-800 border border-slate-800 text-left transition-colors cursor-pointer"
                  >
                    <div className="text-[11px] font-medium text-slate-300 truncate">{h.label}</div>
                    <div className="text-[9px] text-emerald-400 font-mono">{h.username}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Regulatory Notice */}
            <div className="pt-2 text-center flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
              <Shield className="w-3.5 h-3.5 text-emerald-400" />
              <span>Protected by <strong className="text-slate-300">{config.compliance_notice}</strong></span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
