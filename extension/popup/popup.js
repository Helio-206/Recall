import {
  getCurrentUser,
  listRecentSaves,
  listSpaces,
  login,
  saveCurrentUrl,
} from "../lib/api.js";
import { getDashboardUrl, getExtensionVersion } from "../lib/config.js";
import { classifyPage } from "../lib/platform.js";
import { clearSession, getSession, setSession } from "../lib/storage.js";

const elements = {
  appView: document.getElementById("appView"),
  authView: document.getElementById("authView"),
  dashboardLink: document.getElementById("dashboardLink"),
  emailInput: document.getElementById("emailInput"),
  loginForm: document.getElementById("loginForm"),
  loginButton: document.getElementById("loginButton"),
  logoutButton: document.getElementById("logoutButton"),
  pageBadge: document.getElementById("pageBadge"),
  pageReason: document.getElementById("pageReason"),
  pageTitle: document.getElementById("pageTitle"),
  pageUrl: document.getElementById("pageUrl"),
  passwordInput: document.getElementById("passwordInput"),
  recentSaves: document.getElementById("recentSaves"),
  saveButton: document.getElementById("saveButton"),
  spaceSelect: document.getElementById("spaceSelect"),
  statusBanner: document.getElementById("statusBanner"),
  statusLabel: document.getElementById("statusLabel"),
};

const state = {
  session: null,
  spaces: [],
  recentSaves: [],
  pageContext: null,
  pageSupport: null,
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  bindEvents();
  elements.dashboardLink.href = await getDashboardUrl();

  state.pageContext = await readActivePageContext();
  state.pageSupport = classifyPage(state.pageContext);
  renderPageContext();

  const session = await getSession();
  if (!session.token) {
    showAuthView();
    setStatus("idle", "Sign in to Recall");
    return;
  }

  setStatus("loading", "Checking your Recall session…");
  try {
    const user = await getCurrentUser(session.token);
    state.session = { token: session.token, user };
    await setSession(state.session);
    await hydrateApp();
  } catch {
    await clearSession();
    state.session = null;
    showAuthView();
    setStatus("error", "Sign in to Recall");
  }
}

function bindEvents() {
  elements.loginForm.addEventListener("submit", handleLogin);
  elements.logoutButton.addEventListener("click", handleLogout);
  elements.saveButton.addEventListener("click", handleSave);
}

async function handleLogin(event) {
  event.preventDefault();
  elements.loginButton.disabled = true;
  setStatus("loading", "Signing in to Recall…");

  try {
    const session = await login(
      elements.emailInput.value.trim(),
      elements.passwordInput.value,
    );
    state.session = {
      token: session.access_token,
      user: session.user,
    };
    await setSession(state.session);
    await hydrateApp();
  } catch (error) {
    setStatus("error", error.message || "Sign in failed.");
  } finally {
    elements.loginButton.disabled = false;
  }
}

async function handleLogout() {
  await clearSession();
  state.session = null;
  state.spaces = [];
  state.recentSaves = [];
  showAuthView();
  renderRecentSaves();
  setStatus("idle", "Sign in to Recall");
}

async function handleSave() {
  if (!state.session?.token || !state.pageContext || !state.pageSupport?.supported) {
    return;
  }

  const selectedSpaceId = elements.spaceSelect.value;
  if (!selectedSpaceId) {
    setStatus("error", "Select a Learning Space first.");
    return;
  }

  elements.saveButton.disabled = true;
  setStatus("loading", "Saving to Recall…");

  try {
    await saveCurrentUrl(state.session.token, {
      space_id: selectedSpaceId,
      url: state.pageContext.url,
      page_title: state.pageContext.title,
      page_description: state.pageContext.description,
      browser: navigator.userAgent,
      extension_version: getExtensionVersion(),
    });
    setStatus("success", "Added to Learning Space");
    await refreshRecentSaves();
  } catch (error) {
    setStatus("error", error.message || "Save failed.");
  } finally {
    updateSaveButtonState();
  }
}

async function hydrateApp() {
  showAppView();
  setStatus("loading", "Loading your Learning Spaces…");

  const [spaces, recentSaves] = await Promise.all([
    listSpaces(state.session.token),
    listRecentSaves(state.session.token),
  ]);
  state.spaces = spaces;
  state.recentSaves = recentSaves;

  renderSpaces();
  renderRecentSaves();

  if (!state.pageSupport.supported) {
    setStatus("error", state.pageSupport.reason);
  } else if (!state.spaces.length) {
    setStatus("idle", "Create a Learning Space in Recall before saving.");
  } else {
    setStatus("idle", "Ready to save");
  }

  updateSaveButtonState();
}

async function refreshRecentSaves() {
  state.recentSaves = await listRecentSaves(state.session.token);
  renderRecentSaves();
}

function renderPageContext() {
  elements.pageTitle.textContent = state.pageContext?.title || "Untitled page";
  elements.pageUrl.textContent = state.pageContext?.url || "No URL available";
  elements.pageBadge.textContent = state.pageSupport?.label || "Checking";
  elements.pageReason.textContent = state.pageSupport?.reason || "Inspecting current tab.";
}

function renderSpaces() {
  if (!state.spaces.length) {
    elements.spaceSelect.innerHTML = '<option value="">No Learning Spaces yet</option>';
    updateSaveButtonState();
    return;
  }

  elements.spaceSelect.innerHTML = state.spaces
    .map(
      (space, index) =>
        `<option value="${space.id}" ${index === 0 ? "selected" : ""}>${escapeHtml(
          space.title,
        )} · ${space.video_count} videos</option>`,
    )
    .join("");
}

function renderRecentSaves() {
  if (!state.recentSaves.length) {
    elements.recentSaves.innerHTML =
      '<div class="empty-state">Your extension saves will appear here after the first capture.</div>';
    return;
  }

  elements.recentSaves.innerHTML = state.recentSaves
    .map((item) => {
      const dashboardHref = new URL(item.open_path, elements.dashboardLink.href).toString();
      return `
        <article class="recent-save">
          <div class="recent-save-top">
            <a href="${dashboardHref}" target="_blank" rel="noreferrer">${escapeHtml(
              item.page_title || item.space_title,
            )}</a>
            <span class="status-pill ${item.status}">${escapeHtml(item.status)}</span>
          </div>
          <div class="recent-save-meta">${escapeHtml(item.space_title)} · ${escapeHtml(
            formatTimestamp(item.created_at),
          )}</div>
          <div class="recent-save-meta">${escapeHtml(item.error_message || item.normalized_url)}</div>
        </article>
      `;
    })
    .join("");
}

function showAuthView() {
  elements.authView.hidden = false;
  elements.appView.hidden = true;
  updateSaveButtonState();
}

function showAppView() {
  elements.authView.hidden = true;
  elements.appView.hidden = false;
}

function updateSaveButtonState() {
  const hasSpaces = state.spaces.length > 0;
  const enabled = Boolean(state.session?.token) && hasSpaces && state.pageSupport?.supported;
  elements.saveButton.disabled = !enabled;
}

function setStatus(kind, message) {
  elements.statusBanner.className = `status-banner status-${kind}`;
  elements.statusLabel.textContent = message;
}

async function readActivePageContext() {
  const queryParams = new URLSearchParams(window.location.search);
  const overrideUrl = queryParams.get("url");
  const overrideTitle = queryParams.get("title");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const baseContext = {
    url: overrideUrl || tab?.url || "",
    title: overrideTitle || tab?.title || "",
    description: "",
    hasEmbeddedVideo: false,
  };

  if (!tab?.id) {
    return baseContext;
  }

  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const description =
          document.querySelector('meta[name="description"]')?.getAttribute("content") ||
          document
            .querySelector('meta[property="og:description"]')
            ?.getAttribute("content") ||
          "";
        const hasEmbeddedVideo = Boolean(
          document.querySelector(
            'video, iframe[src*="youtube.com"], iframe[src*="youtu.be"], iframe[src*="vimeo.com"]',
          ),
        );

        return {
          title: document.title,
          description,
          hasEmbeddedVideo,
        };
      },
    });

    return {
      ...baseContext,
      title: overrideTitle || result?.result?.title || baseContext.title,
      description: result?.result?.description || "",
      hasEmbeddedVideo: Boolean(result?.result?.hasEmbeddedVideo),
    };
  } catch {
    return baseContext;
  }
}

function formatTimestamp(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Just now";
  }
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}