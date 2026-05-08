chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== "open-capture-window") {
    return false;
  }

  const params = new URLSearchParams({
    url: message.url ?? sender.tab?.url ?? "",
    title: message.title ?? sender.tab?.title ?? "",
  });

  chrome.windows
    .create({
      url: chrome.runtime.getURL(`popup/index.html?${params.toString()}`),
      type: "popup",
      width: 430,
      height: 760,
    })
    .then(() => sendResponse({ ok: true }))
    .catch((error) => sendResponse({ ok: false, error: error.message }));

  return true;
});