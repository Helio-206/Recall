const BUTTON_ID = "recall-save-trigger";

function isSupportedYouTubePage() {
  const host = window.location.hostname.toLowerCase();
  const path = window.location.pathname;

  if (!host.includes("youtube") && host !== "youtu.be") {
    return false;
  }

  return (
    path.startsWith("/watch") ||
    path.startsWith("/playlist") ||
    path.startsWith("/@") ||
    path.startsWith("/channel/") ||
    path.startsWith("/c/") ||
    path.startsWith("/user/") ||
    path.startsWith("/shorts/") ||
    host === "youtu.be"
  );
}

function removeButton() {
  document.getElementById(BUTTON_ID)?.remove();
}

function renderButton() {
  if (!isSupportedYouTubePage()) {
    removeButton();
    return;
  }

  if (document.getElementById(BUTTON_ID)) {
    return;
  }

  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.innerHTML = '<span class="recall-save-dot"></span><span>Save to Recall</span>';
  button.addEventListener("click", () => {
    chrome.runtime.sendMessage({
      type: "open-capture-window",
      url: window.location.href,
      title: document.title,
    });
  });

  document.body.appendChild(button);
}

renderButton();
document.addEventListener("yt-navigate-finish", renderButton);
window.addEventListener("popstate", renderButton);