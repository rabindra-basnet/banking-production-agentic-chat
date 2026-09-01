import type { StreamEventPayload, ChatSession, ChatMessage } from '@/shared/types';

export async function fetchServerSessions(): Promise<ChatSession[]> {
  try {
    const response = await fetch('/api/v1/sessions', {
      method: 'GET',
      credentials: 'same-origin',
    });

    if (!response.ok) return [];
    const data = await response.json();
    return (data.sessions || []).map((s: any) => ({
      id: s.id,
      title: s.title || 'New Conversation',
      createdAt: s.created_at,
      lastUpdated: s.updated_at,
      messages: [],
    }));
  } catch {
    return [];
  }
}

export async function fetchSessionHistory(sessionId: string): Promise<ChatMessage[]> {
  try {
    const response = await fetch(`/api/v1/history/${sessionId}`, {
      method: 'GET',
      credentials: 'same-origin',
    });

    if (!response.ok) return [];
    const data = await response.json();
    return (data.messages || []).map((m: any) => ({
      id: crypto.randomUUID(),
      role: m.role,
      content: m.content,
      timestamp: m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString(),
    }));
  } catch {
    return [];
  }
}

export async function deleteServerSession(sessionId: string): Promise<boolean> {
  try {
    const response = await fetch(`/api/v1/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'same-origin',
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function sendChatMessageStream(
  message: string,
  sessionId: string,
  onEvent: (event: StreamEventPayload) => void,
  onError: (err: any) => void
): Promise<void> {
  const idempotencyKey = `idem_${crypto.randomUUID()}`;

  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        message,
        session_id: sessionId,
        stream: true,
        idempotency_key: idempotencyKey,
      }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.replace('data: ', '').trim();
          if (!jsonStr) continue;

          try {
            const parsed: StreamEventPayload = JSON.parse(jsonStr);
            onEvent(parsed);
          } catch (parseErr) {
            console.error('Error parsing SSE payload:', parseErr);
          }
        }
      }
    }
  } catch (err: any) {
    onError(err);
  }
}
