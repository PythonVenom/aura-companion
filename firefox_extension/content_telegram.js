// Telegram Web K — content script для Ауры.
// По образцу content_max.js / content_vk.js (ADR-018).
// URL: https://web.telegram.org/k/\*

console.log("[Aura Telegram] content script loaded");


function _getActiveSection() {
    const url = location.href;
    if (url.includes("/k/")) {
        // Telegram Web K: SPA. Определяем по видимым панелям.
        if (document.querySelector(".chat-info, .chat .bubble")) return "chat";
        return "chats";
    }
    return "unknown";
}


function listTelegramChats() {
    // Telegram Web K: .chatlist .chat
    const items = document.querySelectorAll(".chatlist .chat, .chat-list .chat");
    const chats = [];
    items.forEach((el, i) => {
        if (i >= 20) return;
        const name = (el.querySelector(".peer-title, .user-title, .title")?.innerText || "").trim();
        const preview = (el.querySelector(".last-message, .message")?.innerText || "").trim();
        if (name) chats.push({ name, preview, index: i });
    });
    return chats;
}


function findTelegramChat(query) {
    const q = query.toLowerCase();
    const items = document.querySelectorAll(".chatlist .chat, .chat-list .chat");
    for (const el of items) {
        const name = (el.querySelector(".peer-title, .user-title, .title")?.innerText || "").toLowerCase();
        if (name.includes(q)) {
            el.click();
            return { ok: true, found: true, name: name };
        }
    }
    return { ok: true, found: false };
}


function getTelegramCurrent() {
    return {
        ok: true,
        section: _getActiveSection(),
        url: location.href,
        title: document.title,
    };
}


function telegramSendMessage(text) {
    const input = document.querySelector('[contenteditable="true"], .input-message-input');
    if (!input) return { sent: false, error: "input not found" };
    input.focus();
    document.execCommand("selectAll", false, null);
    document.execCommand("delete", false, null);
    document.execCommand("insertText", false, text);
    return { sent: false, typed: true, text: text.substring(0, 100) };
}


function telegramFinalize() {
    const input = document.querySelector('[contenteditable="true"], .input-message-input');
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




function readTelegramLast() {
    const bubbles = document.querySelectorAll('.bubble .message, .message');
    if (!bubbles.length) return { text: '' };
    const last = bubbles[bubbles.length - 1];
    return { text: (last.innerText || '').substring(0, 500) };
}

function listTelegramFolders() {
    const items = document.querySelectorAll('.folder-tabs .menu-horizontal-div-item');
    const folders = [];
    items.forEach((el, i) => {
        const name = (el.innerText || '').trim();
        if (name) folders.push({ name, index: i });
    });
    return folders;
}

function openTelegramChannel(query) {
    const q = query.toLowerCase();
    const items = document.querySelectorAll('.chatlist .chat, .chat-list .chat');
    for (const el of items) {
        const name = (el.querySelector('.peer-title, .user-title, .title')?.innerText || '').toLowerCase();
        if (name.includes(q)) {
            el.click();
            return { ok: true, name };
        }
    }
    return { ok: false };
}

browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    try {
        const action = msg.action;
        switch (action) {
            case "tg_list_chats":
                sendResponse({ ok: true, data: listTelegramChats() });
                break;
            case "tg_find_chat":
                sendResponse({ ok: true, data: findTelegramChat(msg.query || "") });
                break;
            case "tg_send_message":
                sendResponse({ ok: true, data: telegramSendMessage(msg.text || "") });
                break;
            case "tg_finalize":
                sendResponse({ ok: true, data: telegramFinalize() });
                break;
            case "tg_read_last":
                sendResponse({ ok: true, data: readTelegramLast() });
                break;
            case "tg_list_folders":
                sendResponse({ ok: true, data: listTelegramFolders() });
                break;
            case "tg_open_channel":
                sendResponse({ ok: true, data: openTelegramChannel(msg.query || '') });
                break;
            case "tg_current":
                sendResponse({ ok: true, data: getTelegramCurrent() });
                break;
            default:
                sendResponse({ ok: false, error: "unknown action: " + action });
        }
    } catch (e) {
        sendResponse({ ok: false, error: e.toString() });
    }
    return true;
});
