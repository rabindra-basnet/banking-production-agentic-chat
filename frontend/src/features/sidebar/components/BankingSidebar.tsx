import { 
  Landmark, 
  CreditCard, 
  LogOut, 
  MessageSquare, 
  Plus, 
  Trash2 
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { UserProfile, CustomerTier, ChatSession, AppConfig } from '@/shared/types';

interface BankingSidebarProps {
  currentUser: UserProfile;
  config: AppConfig;
  sessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  onLogout: () => void;
}

export function BankingSidebar({ 
  currentUser, 
  config,
  sessions, 
  activeSessionId, 
  onSelectSession, 
  onNewSession, 
  onDeleteSession,
  onLogout 
}: BankingSidebarProps) {
  const getTierVariant = (tier: CustomerTier) => {
    switch (tier) {
      case 'privileged':
        return 'privileged';
      case 'premium':
        return 'premium';
      default:
        return 'default';
    }
  };

  return (
    <aside className="w-80 border-r border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between hidden md:flex h-full">
      <div className="space-y-5 overflow-hidden flex flex-col flex-1">
        {/* Dynamic SaaS Brand Header */}
        <div className="flex items-center space-x-3 shrink-0">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-600 shadow-lg shadow-emerald-500/20">
            <Landmark className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base leading-tight tracking-wide text-white flex items-center gap-1.5">
              <span>{config.bank_name}</span>
              <Badge variant="default" className="text-[9px] px-1 py-0 font-mono">{config.bank_badge}</Badge>
            </h1>
            <p className="text-[11px] text-slate-400">{config.bank_tagline}</p>
          </div>
        </div>

        {/* New Chat Button */}
        <Button 
          onClick={onNewSession}
          variant="default"
          className="w-full h-9 text-xs flex items-center justify-center space-x-2 shrink-0 shadow-md shadow-emerald-600/15"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </Button>

        {/* Chat Sessions History List */}
        <div className="space-y-1.5 flex-1 overflow-y-auto pr-1 min-h-[140px]">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between px-1 mb-1">
            <span className="flex items-center space-x-1.5">
              <MessageSquare className="w-3 h-3 text-slate-400" />
              <span>Chat History</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">{sessions.length}</span>
          </div>

          <div className="space-y-1">
            {sessions.map((sess) => {
              const isActive = sess.id === activeSessionId;
              return (
                <div
                  key={sess.id}
                  onClick={() => onSelectSession(sess.id)}
                  className={`group relative flex items-center justify-between p-2.5 rounded-xl text-xs cursor-pointer transition-all ${
                    isActive 
                      ? 'bg-emerald-950/60 border border-emerald-500/50 text-slate-100 shadow-sm' 
                      : 'hover:bg-slate-800/60 text-slate-400 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-2 min-w-0 flex-1 pr-2">
                    <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span className="truncate text-[12px] font-medium leading-normal">{sess.title || 'New Conversation'}</span>
                  </div>

                  {sessions.length > 1 && (
                    <button
                      onClick={(e) => onDeleteSession(sess.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-400 text-slate-500 transition-opacity rounded"
                      title="Delete Conversation"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Registered Bank Accounts */}
        <div className="space-y-1.5 shrink-0 pt-2 border-t border-slate-800/60">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5 px-1">
            <CreditCard className="w-3 h-3 text-slate-400" />
            <span>Accounts</span>
          </h3>
          <div className="space-y-1">
            {currentUser.accounts.map((acc, i) => (
              <div
                key={i}
                className="text-[11px] bg-slate-950/40 border border-slate-800/60 px-2.5 py-1.5 rounded-lg font-mono text-slate-300 flex items-center justify-between"
              >
                <span className="truncate max-w-[170px]">{acc}</span>
                <span className="text-[9px] px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Active</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar Bottom: User Profile Card & Single Logout Action */}
      <div className="pt-3 border-t border-slate-800/80 shrink-0">
        <Card className="space-y-2 p-3 border-slate-800/80 bg-slate-950/80 shadow-none">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs shrink-0">
                {currentUser.name.charAt(0)}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-xs font-bold text-slate-200 truncate">{currentUser.name}</h4>
                <p className="text-[10px] text-slate-400 font-mono truncate">{currentUser.customerId}</p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-800 transition-colors cursor-pointer shrink-0 ml-1"
              title="Log Out"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="pt-1.5 border-t border-slate-800/80 text-[11px] space-y-1 text-slate-300">
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-[10px]">Authorization:</span>
              <Badge variant={getTierVariant(currentUser.tier)} className="text-[9px] uppercase font-bold py-0">
                {currentUser.tier}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-[10px]">Email:</span>
              <span className="text-[10px] text-slate-400 truncate max-w-[140px]">{currentUser.email}</span>
            </div>
          </div>
        </Card>
      </div>
    </aside>
  );
}
