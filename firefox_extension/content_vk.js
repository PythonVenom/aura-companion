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
    // Голосовая навигация: «вк лента», «вк друзья», «вк im», «вк audio».
    const shortcuts = listVKShortcuts();
    const sec = (section || "").toLowerCase().trim();
    const found = shortcuts.find(s =>
        s.name.toLowerCase().includes(sec) ||
        s.url.toLowerCase().includes("/" + sec)
    );
    if (found) {
        location.href = found.url;
        return { ok: true, url: found.url, name: found.name };
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



function listVKFriends() {
    const items = document.querySelectorAll(".friends_list .friends_row, [data-testid='friends-row']");
    const friends = [];
    items.forEach((el, i) => {
        if (i >= 20) return;
        const name = (el.querySelector('.fname, .friends_field_title')?.innerText || '').trim();
        if (name) friends.push({ name, index: i });
    });
    return friends;
}


function listVKGroups() {
    const items = document.querySelectorAll(".groups_list .group_row, [data-testid='groups-row']");
    const groups = [];
    items.forEach((el, i) => {
        if (i >= 20) return;
        const name = (el.querySelector('.group_name, .groups_group_name')?.innerText || '').trim();
        if (name) groups.push({ name, index: i });
    });
    return groups;
}


function listVKNews() {
    const items = document.querySelectorAll(".wall_post, [data-testid='wall-post']");
    const news = [];
    items.forEach((el, i) => {
        if (i >= 10) return;
        const text = (el.innerText || '').substring(0, 200);
        if (text) news.push({ text, index: i });
    });
    return news;
}


function vkNextTrack() {
    const btn = document.querySelector(".audio_player__next, [aria-label='next']");
    if (btn) { btn.click(); return { ok: true }; }
    return { ok: false };
}


function vkPrevTrack() {
    const btn = document.querySelector(".audio_player__prev, [aria-label='prev']");
    if (btn) { btn.click(); return { ok: true }; }
    return { ok: false };
}



function vkLikePost() {
    const btn = document.querySelector('.like_button, [aria-label="Нравится"]');
    if (btn) { btn.click(); return { ok: true }; }
    return { ok: false };
}

function vkCommentPost(text) {
    const input = document.querySelector('[contenteditable="true"][role="textbox"]');
    if (!input) return { ok: false };
    input.focus();
    document.execCommand('selectAll', false, null);
    document.execCommand('delete', false, null);
    document.execCommand('insertText', false, text);
    return { ok: true };
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
            case "vk_like_post":
                sendResponse({ ok: true, data: vkLikePost() });
                break;
            case "vk_comment_post":
                sendResponse({ ok: true, data: vkCommentPost(msg.text || '') });
                break;
            case "vk_list_friends":
                sendResponse({ ok: true, data: listVKFriends() });
                break;
            case "vk_list_groups":
                sendResponse({ ok: true, data: listVKGroups() });
                break;
            case "vk_list_news":
                sendResponse({ ok: true, data: listVKNews() });
                break;
            case "vk_next_track":
                sendResponse({ ok: true, data: vkNextTrack() });
                break;
            case "vk_prev_track":
                sendResponse({ ok: true, data: vkPrevTrack() });
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
