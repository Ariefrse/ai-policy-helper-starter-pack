'use client';
import React from 'react';
import { apiAsk } from '../lib/api';
import { Message } from '../lib/types';
import styles from './Chat.module.css';

interface MessageItemProps {
  message: Message;
  index: number;
}

const MessageItem = React.memo(({ message, index }: MessageItemProps) => {
  const citationsArray = React.useMemo(() => message.citations || [], [message.citations]);
  const chunksArray = React.useMemo(() => message.chunks || [], [message.chunks]);

  // Group citations and chunks by source title to avoid duplicate badges
  const uniqueCitationTitles = React.useMemo(() => {
    const titles = new Set<string>();
    for (const c of citationsArray) {
      if (c.title) titles.add(c.title);
    }
    return Array.from(titles);
  }, [citationsArray]);

  const chunksGroupedByTitle = React.useMemo(() => {
    const byTitle = new Map<string, typeof chunksArray>();
    for (const chunk of chunksArray) {
      const list = byTitle.get(chunk.title) || [];
      list.push(chunk);
      byTitle.set(chunk.title, list);
    }
    return byTitle;
  }, [chunksArray]);

  return (
    <div key={index} className={styles.messageContainer}>
      <div className={styles.messageHeader}>
        <div className={`${styles.avatar} ${message.role === 'user' ? styles.avatarUser : styles.avatarAssistant}`}>
          {message.role === 'user' ? '👤' : '🤖'}
        </div>
        <div className={styles.messageContent}>
          <div className={styles.messageRole}>
            {message.role === 'user' ? 'You' : 'AI Assistant'}
          </div>
          <div className={`${styles.messageBubble} ${message.role === 'user' ? styles.messageBubbleUser : styles.messageBubbleAssistant}`}>
            {message.content}
          </div>
        </div>
      </div>

      {citationsArray.length > 0 && (
        <div className={styles.citationsContainer}>
          <div className={styles.citationsHeader}>
            📚 Sources ({uniqueCitationTitles.length})
          </div>
          <div className={styles.citationsList}>
            {uniqueCitationTitles.map((title) => (
              <span
                key={title}
                className="badge"
                title={title}
              >
                📄 {title}
              </span>
            ))}
          </div>
        </div>
      )}

      {chunksArray.length > 0 && (
        <div className={styles.chunksContainer}>
          <details className={styles.chunkDetails}>
            <summary className={styles.chunkSummary}>
              🔍 View supporting sources ({chunksGroupedByTitle.size} files, {chunksArray.length} chunks)
            </summary>
            <div className={styles.chunkContent}>
              {Array.from(chunksGroupedByTitle.entries()).map(([title, groupChunks], groupIdx) => (
                <details key={`${title}-${groupIdx}`} className={styles.chunkItem}>
                  <summary className={styles.chunkTitle}>
                    📋 {title}
                    <span className={styles.chunkSection}> ({groupChunks.length} section{groupChunks.length > 1 ? 's' : ''})</span>
                  </summary>
                  {groupChunks.map((c, idx) => (
                    <div key={`${c.title}-${c.section}-${idx}`} className={idx < groupChunks.length - 1 ? styles.chunkItem : `${styles.chunkItem} ${styles.chunkItemLastChild}`}>
                      {c.section && (
                        <div className={styles.chunkSection}>
                          → {c.section}
                        </div>
                      )}
                      <div className={styles.chunkText}>
                        {c.text}
                      </div>
                    </div>
                  ))}
                </details>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
});

MessageItem.displayName = 'MessageItem';

export default function Chat() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [q, setQ] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const send = React.useCallback(async () => {
    if (!q.trim()) return;
    const my: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'user' as const,
      content: q
    };
    setMessages(m => [...m, my]);
    setLoading(true);
    try {
      const res = await apiAsk(q);
      const ai: Message = {
        id: `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        chunks: res.chunks
      };
      setMessages(m => [...m, ai]);
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Unknown error occurred';
      setMessages(m => [...m, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Error: ' + errorMessage
      }]);
    } finally {
      setLoading(false);
      setQ('');
    }
  }, [q]);

  const handleInputChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQ(e.target.value);
  }, []);

  const handleKeyDown = React.useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      send();
    }
  }, [send]);

  const messagesList = React.useMemo(() =>
    messages.map((message, index) => (
      <MessageItem
        key={message.id || `${message.role}-${index}`}
        message={message}
        index={index}
      />
    )), [messages]
  );

  return (
    <div className={`card ${styles.chatContainer}`}>
      <div className={styles.header}>
        <h2 className={styles.title}>💬 Policy Assistant</h2>
        {loading && (
          <div className={styles.loadingIndicator}>Thinking...</div>
        )}
      </div>

      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyStateIcon}>🤖</div>
            <div className={styles.emptyStateTitle}>Ask about shipping, returns, warranties, or product policies</div>
            <div className={styles.emptyStateSubtitle}>I'll provide answers with source citations</div>
          </div>
        ) : (
          messagesList
        )}
      </div>

      <div className={styles.inputContainer}>
        <input
          placeholder="Ask about policy or products..."
          value={q}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          className={styles.messageInput}
        />
        <button
          onClick={send}
          disabled={loading || !q.trim()}
          className={`${styles.sendButton} ${loading || !q.trim() ? styles.sendButtonDisabled : styles.sendButtonEnabled}`}
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>
    </div>
  );
}