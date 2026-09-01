import { useState, useEffect } from 'react';
import type { UserProfile, ChatSession, ChatMessage, AppConfig } from '@/shared/types';
import { LoginForm } from '@/features/auth/components/LoginForm';
import { checkAuthSession, logoutUser } from '@/features/auth/api';
import { fetchAppConfig, getCachedAppConfig } from '@/shared/api/config';
import { fetchServerSessions, fetchSessionHistory, deleteServerSession } from '@/features/chat/api';
import { BankingSidebar } from '@/features/sidebar/components/BankingSidebar';
import { ChatView } from '@/features/chat/components/ChatView';

export default function App() {
  const [config, setConfig] = useState<AppConfig>(() => getCachedAppConfig());
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => {
    const cached = localStorage.getItem('nepalbank_user');
    if (cached) {
      try {
        return JSON.parse(cached) as UserProfile;
      } catch {
        return null;
      }
    }
    return null;
  });

  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Backend Synchronized Chat Sessions State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>('');

  // Load SaaS App Configuration and Validate Session from Backend
  useEffect(() => {
    async function initApp() {
      const appConfig = await fetchAppConfig();
      setConfig(appConfig);

      const serverProfile = await checkAuthSession();
      if (serverProfile) {
        setCurrentUser(serverProfile);
        
        // Fetch sessions directly from Backend PostgreSQL / SQLite Database
        const serverSessions = await fetchServerSessions();
        if (serverSessions.length > 0) {
          setSessions(serverSessions);
          setActiveSessionId(serverSessions[0].id);
        } else {
          const freshId = crypto.randomUUID();
          setSessions([
            {
              id: freshId,
              title: 'New Conversation',
              createdAt: new Date().toISOString(),
              lastUpdated: new Date().toISOString(),
              messages: [],
            },
          ]);
          setActiveSessionId(freshId);
        }
      } else {
        // No active server session (e.g. cookie expired or logged out)
        setCurrentUser(null);
        localStorage.removeItem('nepalbank_user');
      }
      setIsLoadingAuth(false);
    }
    initApp();
  }, []);

  // When active session changes, load its message history from Backend if not loaded
  useEffect(() => {
    if (!currentUser || !activeSessionId) return;

    const currentSession = sessions.find((s) => s.id === activeSessionId);
    if (currentSession && currentSession.messages.length === 0) {
      fetchSessionHistory(activeSessionId).then((history) => {
        if (history.length > 0) {
          setSessions((prev) =>
            prev.map((s) =>
              s.id === activeSessionId ? { ...s, messages: history } : s
            )
          );
        }
      });
    }
  }, [activeSessionId, currentUser]);

  const handleLoginSuccess = async (profile: UserProfile) => {
    setCurrentUser(profile);
    const serverSessions = await fetchServerSessions();
    if (serverSessions.length > 0) {
      setSessions(serverSessions);
      setActiveSessionId(serverSessions[0].id);
    } else {
      const freshId = crypto.randomUUID();
      setSessions([
        {
          id: freshId,
          title: 'New Conversation',
          createdAt: new Date().toISOString(),
          lastUpdated: new Date().toISOString(),
          messages: [],
        },
      ]);
      setActiveSessionId(freshId);
    }
  };

  const handleLogout = async () => {
    await logoutUser();
    setCurrentUser(null);
    setSessions([]);
  };

  // Session Handlers (Synced with Backend DB)
  const handleNewSession = () => {
    const newId = crypto.randomUUID();
    const newSession: ChatSession = {
      id: newId,
      title: 'New Conversation',
      createdAt: new Date().toISOString(),
      lastUpdated: new Date().toISOString(),
      messages: [],
    };
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newId);
  };

  const handleSelectSession = (id: string) => {
    setActiveSessionId(id);
  };

  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await deleteServerSession(id);
    setSessions((prev) => {
      const filtered = prev.filter((s) => s.id !== id);
      if (filtered.length === 0) {
        const freshId = crypto.randomUUID();
        return [
          {
            id: freshId,
            title: 'New Conversation',
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            messages: [],
          },
        ];
      }
      if (activeSessionId === id) {
        setActiveSessionId(filtered[0].id);
      }
      return filtered;
    });
  };

  const handleClearCurrentSession = () => {
    setSessions((prev) =>
      prev.map((s) =>
        s.id === activeSessionId
          ? { ...s, messages: [], title: 'New Conversation', lastUpdated: new Date().toISOString() }
          : s
      )
    );
  };

  const handleUpdateActiveMessages = (updater: (prev: ChatMessage[]) => ChatMessage[]) => {
    setSessions((prev) =>
      prev.map((s) => {
        if (s.id === activeSessionId) {
          const updatedMessages = updater(s.messages);
          let title = s.title;
          const firstUserMsg = updatedMessages.find((m) => m.role === 'user');
          if (firstUserMsg && s.title === 'New Conversation') {
            title = firstUserMsg.content.slice(0, 28) + (firstUserMsg.content.length > 28 ? '...' : '');
          }
          return {
            ...s,
            messages: updatedMessages,
            title,
            lastUpdated: new Date().toISOString(),
          };
        }
        return s;
      })
    );
  };

  if (isLoadingAuth && !currentUser) {
    return (
      <div className="min-h-screen w-full bg-slate-950 flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  // 1. Auth View
  if (!currentUser) {
    return <LoginForm config={config} onSuccess={handleLoginSuccess} />;
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0];
  const activeMessages = activeSession?.messages.length > 0
    ? activeSession.messages
    : [
        {
          id: 'welcome',
          role: 'assistant' as const,
          content: `Namaste **${currentUser.name}**! 🙏 Welcome to the **${config.bank_name}** (${config.compliance_notice}).\n\nHow can I assist you with your ${config.supported_services} today?`,
          timestamp: new Date().toLocaleTimeString(),
          agent: config.assistant_name,
        },
      ];

  // 2. Main Authenticated Banking Feature Layout (Sessions synced with database)
  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-100 overflow-hidden">
      <BankingSidebar 
        currentUser={currentUser}
        config={config}
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onLogout={handleLogout} 
      />
      <ChatView 
        currentUser={currentUser} 
        config={config}
        sessionId={activeSessionId}
        messages={activeMessages}
        onUpdateMessages={handleUpdateActiveMessages}
        onResetSession={handleClearCurrentSession} 
        onLogout={handleLogout} 
      />
    </div>
  );
}
