const SESSION_KEY = "recall-extension-session";

const EMPTY_SESSION = {
  token: null,
  user: null,
};

export async function getSession() {
  const stored = await chrome.storage.local.get(SESSION_KEY);
  return stored[SESSION_KEY] ?? EMPTY_SESSION;
}

export async function setSession(session) {
  await chrome.storage.local.set({ [SESSION_KEY]: session });
}

export async function clearSession() {
  await chrome.storage.local.remove(SESSION_KEY);
}