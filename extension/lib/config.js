const CONFIG_KEY = "recall-extension-config";

const DEFAULT_CONFIG = {
  apiBaseUrl: "http://localhost:8000/api/v1",
  dashboardBaseUrl: "http://localhost:3000",
};

export async function getConfig() {
  const stored = await chrome.storage.local.get(CONFIG_KEY);
  return {
    ...DEFAULT_CONFIG,
    ...(stored[CONFIG_KEY] ?? {}),
  };
}

export async function getDashboardUrl(path = "/dashboard") {
  const config = await getConfig();
  return new URL(path, config.dashboardBaseUrl).toString();
}

export function getExtensionVersion() {
  return chrome.runtime.getManifest().version;
}