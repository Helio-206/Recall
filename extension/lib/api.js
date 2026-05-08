import { getConfig } from "./config.js";

async function request(path, options = {}) {
  const { apiBaseUrl } = await getConfig();
  const { token, method = "GET", body } = options;
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = new Error(payload?.detail ?? response.statusText ?? "Request failed.");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

export function login(email, password) {
  return request("/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function getCurrentUser(token) {
  return request("/auth/me", { token });
}

export function listSpaces(token) {
  return request("/extension/spaces", { token });
}

export function listRecentSaves(token) {
  return request("/extension/recent-saves", { token });
}

export function saveCurrentUrl(token, payload) {
  return request("/extension/saves", {
    token,
    method: "POST",
    body: payload,
  });
}