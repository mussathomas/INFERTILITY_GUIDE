const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export interface User {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SourceCitation {
  document: string;
  excerpt: string;
}

export interface ChatResponse {
  conversation_id: number;
  reply: string;
  sources: SourceCitation[];
  disclaimer: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[] | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  messages: Message[];
}

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new ApiError(data.detail || "Request failed", res.status);
  }
  return data as T;
}

export const api = {
  register: (email: string, full_name: string, password: string) =>
    request<AuthResponse>("/register", {
      method: "POST",
      body: JSON.stringify({ email, full_name, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<User>("/me"),

  chat: (message: string, conversation_id?: number) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id }),
    }),

  conversations: () => request<Conversation[]>("/conversations"),
};

export { ApiError };
