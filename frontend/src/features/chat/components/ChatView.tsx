import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Send, 
  Bot, 
  User, 
  Sparkles, 
  RefreshCw, 
  LogOut 
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { ChatMessage, UserProfile, StreamEventPayload, AppConfig } from '@/shared/types';
import { sendChatMessageStream } from '../api';

const SUGGESTED_PROMPTS = [
  "What is my current account balance in NPR?",
  "Show my recent Fonepay QR and ConnectIPS debits",
  "I want to request a new Cheque Book (25 leaves)",
  "Emergency: Please block my debit card ending in 1234",
  "Can you show total summary across all my accounts in Nepal?",
];

interface ChatViewProps {
  currentUser: UserProfile;
  config: AppConfig;
  sessionId: string;
  messages: ChatMessage[];
  onUpdateMessages: (updater: (prev: ChatMessage[]) => ChatMessage[]) => void;
  onResetSession: () => void;
  onLogout: () => void;
}

export function ChatView({ 
  currentUser, 
  config,
  sessionId, 
  messages, 
  onUpdateMessages,
  onResetSession, 
  onLogout 
}: ChatViewProps) {
  const [inputMessage, setInputMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = textToSend || inputMessage;
    if (!query.trim() || isStreaming) return;

    const userMsgId = crypto.randomUUID();
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: query.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    onUpdateMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsStreaming(true);

    const assistantMsgId = crypto.randomUUID();
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString(),
      agent: config.assistant_name,
      isStreaming: true,
    };

    onUpdateMessages((prev) => [...prev, initialAssistantMsg]);

    let accumulatedText = '';

    await sendChatMessageStream(
      query.trim(),
      sessionId,
      (payload: StreamEventPayload) => {
        if (payload.event === 'token') {
          accumulatedText += payload.delta;
          onUpdateMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: accumulatedText }
                : msg
            )
          );
        } else if (payload.event === 'done') {
          onUpdateMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText,
                    isStreaming: false,
                    latencyMs: payload.metadata?.latency_ms,
                    costUsd: payload.metadata?.cost_usd,
                  }
                : msg
            )
          );
        }
      },
      (err: any) => {
        onUpdateMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: `⚠️ Failed to connect to banking assistant: ${err.message}`,
                  isStreaming: false,
                }
              : msg
          )
        );
      }
    );

    setIsStreaming(false);
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-slate-950">
      {/* Top Header - Dynamic Brand Config */}
      <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/40 backdrop-blur-md">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <div>
            <h2 className="font-semibold text-sm text-slate-100">
              {config.bank_tagline}
            </h2>
            <p className="text-xs text-slate-400">Authenticated Banking Session</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onResetSession}
            className="text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Clear Chat</span>
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={onLogout}
            className="text-xs md:hidden"
          >
            <LogOut className="w-3.5 h-3.5" />
          </Button>
        </div>
      </header>

      {/* Message Stream Thread */}
      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                  isUser
                    ? 'bg-emerald-600 text-white'
                    : 'bg-gradient-to-tr from-emerald-600 to-teal-700 text-white'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`max-w-2xl space-y-1 ${isUser ? 'items-end' : ''}`}>
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <span className="font-medium text-slate-300">
                    {isUser ? currentUser.name : config.assistant_name}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                  {!isUser && (currentUser.role === 'admin' || currentUser.tier === 'privileged') && msg.latencyMs !== undefined && (
                    <span className="text-emerald-400/80 font-mono text-[10px] bg-slate-900 border border-slate-800 px-1.5 py-0.5 rounded">
                      Admin: {msg.latencyMs.toFixed(0)}ms | ${msg.costUsd?.toFixed(4) || '0.0000'}
                    </span>
                  )}
                </div>

                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-emerald-600 text-white rounded-tr-none'
                      : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-md'
                  }`}
                >
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none space-y-2 [&>ul]:list-disc [&>ul]:pl-5 [&>ol]:list-decimal [&>ol]:pl-5 [&>p]:leading-relaxed [&>strong]:text-emerald-400 [&>code]:bg-slate-950 [&>code]:px-1.5 [&>code]:py-0.5 [&>code]:rounded [&>code]:text-emerald-300 [&>code]:font-mono [&>code]:text-xs">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}

                  {msg.isStreaming && !msg.content && (
                    <span className="inline-flex items-center space-x-1.5 text-slate-400 py-1">
                      <Sparkles className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                      <span className="text-xs">Processing request...</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        <div ref={chatEndRef} />
      </div>

      {/* Suggested Queries */}
      <div className="px-6 py-2 border-t border-slate-800/40 bg-slate-900/20 flex flex-wrap gap-2">
        {SUGGESTED_PROMPTS.map((prompt, idx) => (
          <button
            key={idx}
            disabled={isStreaming}
            onClick={() => handleSendMessage(prompt)}
            className="text-xs px-3 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-all text-left flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className="w-3 h-3 text-emerald-400" />
            <span>{prompt}</span>
          </button>
        ))}
      </div>

      {/* Message Input Box */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/60 backdrop-blur-md">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center space-x-3 max-w-5xl mx-auto"
        >
          <Input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about your balance, Fonepay QR debits, ConnectIPS, or Cheque book..."
            disabled={isStreaming}
            className="flex-1 h-12 text-sm bg-slate-950 font-sans"
          />
          <Button
            type="submit"
            disabled={!inputMessage.trim() || isStreaming}
            className="h-12 px-5"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </main>
  );
}
