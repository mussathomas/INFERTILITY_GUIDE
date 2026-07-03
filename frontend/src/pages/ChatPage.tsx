import { FormEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Message, type SourceCitation } from "../api/client";
import { useAuth } from "../context/AuthContext";

const SUGGESTED_QUESTIONS = [
  "What causes infertility in couples?",
  "Is acupuncture helpful for fertility treatment?",
  "I've heard stress causes all infertility — is that true?",
  "When should we see a fertility specialist?",
  "Can herbal medicine replace IVF?",
];

interface LocalMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  disclaimer?: string;
  pending?: boolean;
}

function SourcesPanel({ sources }: { sources: SourceCitation[] }) {
  if (!sources.length) return null;
  return (
    <details className="sources-panel">
      <summary>Verified sources ({sources.length})</summary>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>
            <strong>{s.document}</strong>
            <p>{s.excerpt}</p>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function ChatPage() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    api.conversations().then((convs) => {
      if (convs.length > 0) {
        const latest = convs[0];
        setConversationId(latest.id);
        setMessages(
          latest.messages.map((m: Message) => ({
            role: m.role,
            content: m.content,
            sources: m.sources ?? undefined,
          })),
        );
      }
    }).catch(() => {});
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;
    setError("");
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "assistant", content: "", pending: true }]);

    try {
      const res = await api.chat(text, conversationId);
      setConversationId(res.conversation_id);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: res.reply,
          sources: res.sources,
          disclaimer: res.disclaimer,
        };
        return updated;
      });
    } catch {
      setError("Failed to get a response. Please try again.");
      setMessages((prev) => prev.filter((m) => !m.pending));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const startNewChat = () => {
    setConversationId(undefined);
    setMessages([]);
    setError("");
  };

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="chat-header-left">
          <Link to="/chat" className="logo-link">UZAZI ASSISTANT</Link>
          <span className="header-tag">Infertility inquiry</span>
        </div>
        <div className="chat-header-right">
          <span className="user-greeting">Hello, {user?.full_name.split(" ")[0]}</span>
          <button type="button" className="btn btn-ghost" onClick={startNewChat}>
            New chat
          </button>
          <button type="button" className="btn btn-ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="chat-main">
        <aside className="chat-sidebar">
          <h3>About this assistant</h3>
          <p>
            Answers are grounded in a verified knowledge base and enhanced with Large Language Models.
            Common myths are corrected gently, and traditional medicine is discussed with balanced context.
          </p>
          <div className="info-cards">
            <div className="info-card">
              <span className="info-icon">✓</span>
              <div>
                <strong>Verified info</strong>
                <p>Responses cite knowledge base excerpts</p>
              </div>
            </div>
            <div className="info-card">
              <span className="info-icon">⚠</span>
              <div>
                <strong>Myth correction</strong>
                <p>Common misinformation is addressed clearly</p>
              </div>
            </div>
            <div className="info-card">
              <span className="info-icon">🌿</span>
              <div>
                <strong>Traditional medicine</strong>
                <p>MUHAS,Ethnomedicine &amp; herbs in balanced context</p>
              </div>
            </div>
          </div>
          <p className="sidebar-disclaimer">
            Not medical advice. Always consult a qualified fertility specialist.
          </p>
        </aside>

        <section className="chat-panel">
          <div className="messages-area">
            {messages.length === 0 && (
              <div className="welcome-block">
                <h2>How can we help you today?</h2>
                <p>Ask about infertility causes, treatments, myths, or traditional approaches.</p>
                <div className="suggested-grid">
                  {SUGGESTED_QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      className="suggested-btn"
                      onClick={() => sendMessage(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`message message--${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === "user" ? user?.full_name.charAt(0).toUpperCase() : "AI"}
                </div>
                <div className="message-body">
                  {msg.pending ? (
                    <div className="typing-indicator">
                      <span /><span /><span />
                    </div>
                  ) : (
                    <>
                      <div className="message-content">{msg.content}</div>
                      {msg.sources && <SourcesPanel sources={msg.sources} />}
                      {msg.disclaimer && (
                        <p className="message-disclaimer">{msg.disclaimer}</p>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {error && <div className="chat-error">{error}</div>}

          <form className="chat-input-form" onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about infertility, treatments, myths, or traditional medicine..."
              rows={2}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </section>
      </main>
    </div>
  );
}
