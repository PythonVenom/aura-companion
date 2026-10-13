// Aura Bridge — content script для web.max.ru (MV3 MVP).
// Пока — только приём сообщений от background + логирование.

console.log("[Aura] content_max.js загружен на", location.href);

chrome.runtime.onMessage.addListener((msg) => {
  console.log("[Aura] background →", msg);
  // TODO: интеграция с DOM web.max.ru (голосовые команды)
});

// Проверка связи с background
chrome.runtime.sendMessage({ type: "content_ready", url: location.href })
  .then((r) => console.log("[Aura] background ответил:", r))
  .catch((e) => console.warn("[Aura] background недоступен:", e));
