// Aura Bridge — MV3 background service worker.
// Архитектура (из bridge-host): socket-server ↔ native-messaging ↔ Firefox.
// Firefox НЕ инициирует сообщения — только отвечает на команды Aura.
// F-022: MVP без ping-pong (bridge-host не поддерживает).
// Наука: Brooks 1975 (база > фичи).

const NATIVE_HOST = "aura_bridge";
let port = null;

function connect() {
  try {
    port = chrome.runtime.connectNative(NATIVE_HOST);
    port.onMessage.addListener((msg) => {
      // F-022: не логируем _token (утечка в console)
      const safe = { ...msg };
      if (safe._token) safe._token = "***";
      console.log("[Aura] native →", safe);
      // Broadcast в content scripts
      chrome.tabs.query({}, (tabs) => {
        for (const tab of tabs) {
          if (tab.id) {
            chrome.tabs.sendMessage(tab.id, msg).catch(() => {});
          }
        }
      });
    });
    port.onDisconnect.addListener(() => {
      const err = chrome.runtime.lastError;
      console.warn("[Aura] native disconnected:", err?.message || "clean");
      port = null;
      setTimeout(connect, 5000);
    });
    console.log("[Aura] native connected");
  } catch (e) {
    console.error("[Aura] connect failed:", e);
    setTimeout(connect, 5000);
  }
}

connect();

// Приём от content scripts
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  console.log("[Aura] content →", msg, "from tab", sender.tab?.id);
  if (port) {
    port.postMessage(msg);
    sendResponse({ ok: true });
  } else {
    sendResponse({ ok: false, error: "no native port" });
  }
  return true;
});
