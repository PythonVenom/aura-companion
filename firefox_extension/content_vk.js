// VK Web — content script для Ауры.
// По образцу content_max.js (SiteAdapter pattern, ADR-016/018).
// URL: https://vk.com/\*

console.log("[Aura VK] content script loaded");


function _getActiveVKSection() {
    // VK — SPA. Определяем активный раздел по URL и DOM.
    const url = location.href;
    if (url.includes("/feed"))     return "feed";
    if (url.includes("/im"))       return "messages";
    if (url.includes("/friends"))  return "friends";
    if (url.includes("/groups"))   return "groups";
    if (url.includes("/audio"))    return "music";
    if (url.includes("/videos"))   return "videos";
    if (url.match(/\/wall/))       return "wall";
    return "unknown";
}


function listVKShortcuts() {
    // Возвращает доступные разделы (для навигации голосом).
    return [
        { name: "Лента",       url: "https://vk.com/feed" },
        { name: "Сообщения",   url: "https://vk.com/im" },
        { name: "Друзья",      url: "https://vk.com/friends" },
        { name: "Группы",      url: "https://vk.com/groups" },
        { name: "Музыка",      url: "https://vk.com/audio" },
        { name: "Видео",       url: "https://vk.com/videos" },
        { name: "Моя страница", url: "https://vk.com/me" },
    ];
}


function navigateVK(section) {
    // Голосовая навигация: «вк лента», «вк друзья».
    const shortcuts = listVKShortcuts();
    const found = shortcuts.find(s =>
        s.name.toLowerCase().includes(section.toLowerCase())
    );
    if (found) {
        location.href = found.url;
        return { ok: true, url: found.url };
    }
    return { ok: false, error: "section not found: " + section };
}


function getVKCurrentSection() {
    return {
        ok: true,
        section: _getActiveVKSection(),
        url: location.href,
        title: document.title,
    };
}




function listVKChats() {
    // Парсим список диалогов в /im
    const items = document.querySelectorAll('[data-testid="dialogs-item"], .dialogs_item, [role="listitem"]');
    const chats = [];
    items.forEach((el, i) => {
        if (i >= 20) return;
        const name = (el.querySelector('[data-testid="dialogs-item-name"], .dialogs_item_name, .peer-title')?.innerText || "").trim();
        const preview = (el.innerText || "").substring(0, 120).replace(name, "").trim();
        if (name) chats.push({ name, preview, index: i });
    });
    return chats;
}



function findVKInput() {
    return document.querySelector('[contenteditable="true"][role="textbox"], .im-editable-input');
}


function sendVKMessage(text) {
    const input = findVKInput();
    if (!input) return { sent: false, error: "input not found" };
    input.focus();
    document.execCommand("selectAll", false, null);
    document.execCommand("delete", false, null);
    document.execCommand("insertText", false, text);
    return { sent: false, typed: true, text: text.substring(0, 100) };
}


function finalizeVKMessage() {
    const input = findVKInput();
    if (!input) return { sent: false, error: "input not found" };
    input.focus();
    for (const type of ["keydown", "keypress", "keyup"]) {
        const ev = new KeyboardEvent(type, {
            key: "Enter", code: "Enter", keyCode: 13, which: 13,
            bubbles: true, cancelable: true, composed: true,
        });
        input.dispatchEvent(ev);
    }
    return { sent: true };
}

// Слушаем команды от background.js
browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    try {
        const action = msg.action;
        switch (action) {
            case "vk_list_shortcuts":
                sendResponse({ ok: true, data: listVKShortcuts() });
                break;
            case "vk_navigate":
                sendResponse({ ok: true, data: navigateVK(msg.section || "") });
                break;
            case "vk_send_message":
                sendResponse({ ok: true, data: sendVKMessage(msg.text || "") });
                break;
            case "vk_finalize":
                sendResponse({ ok: true, data: finalizeVKMessage() });
                break;
            case "vk_list_chats":
                sendResponse({ ok: true, data: listVKChats() });
                break;
            case "vk_current":
                sendResponse({ ok: true, data: getVKCurrentSection() });
                break;
            default:
                sendResponse({ ok: false, error: "unknown action: " + action });
        }
    } catch (e) {
        sendResponse({ ok: false, error: e.toString() });
    }
    return true;
});
