type ApiOptions = RequestInit & {
  token?: string | null;
};

const API_URL = "/api/v1";

function handleUnauthorizedResponse(token?: string | null) {
  if (!token || typeof window === "undefined") {
    return;
  }

  void import("@/stores/auth-store").then(({ useAuthStore }) => {
    useAuthStore.getState().logout();

    const next = `${window.location.pathname}${window.location.search}`;
    const loginUrl = new URL("/login", window.location.origin);
    if (next && next !== "/login") {
      loginUrl.searchParams.set("next", next);
    }

    window.location.replace(loginUrl.toString());
  });
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { token, headers, ...init } = options;
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      handleUnauthorizedResponse(token);
    }

    let detail = "Request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      detail = response.statusText || detail;
    }

    if (response.status === 401 && token) {
      detail = "Your session expired. Please log in again.";
    }

    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
