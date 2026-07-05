const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

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

  const url = `${API_BASE}/api${path}`;
  console.log(`[API] ${options.method || "GET"} ${url}`);

  try {
    const res = await fetch(url, { ...options, headers });
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      console.error(`[API Error] ${res.status}: ${data.detail || "Unknown error"}`);
      throw new ApiError(data.detail || `Request failed with status ${res.status}`, res.status);
    }
    console.log(`[API Success] ${res.status}`);
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    console.error(`[API Network Error]`, error);
    throw new ApiError(
      error instanceof Error ? error.message : "Network error",
      0
    );
  }
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
