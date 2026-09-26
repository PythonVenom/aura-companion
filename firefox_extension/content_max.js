// Aura Bridge — content script для max.ru.
// Фаза 13.1: диагностика. Позже — реальные действия.
//
// По науке: сначала изучаем DOM, потом делаем действия.
// Все селекторы — эвристики, потому что вёрстка меняется.

console.log("[Aura Max] v2.2 content script loaded:", location.href);

// --- Слушаем команды от background.js ---
browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    console.log("[Aura Max] got action:", msg.action);
    try {
        switch (msg.action) {
            case "max_dump_structure":
                sendResponse({ ok: true, data: dumpStructure() });
                break;
            case "max_deep_dump":
                sendResponse({ ok: true, data: deepDump() });
                break;
            case "max_list_chats":
                sendResponse({ ok: true, data: listChatsFromButtons() });
                break;
            case "max_find_chat":
                sendResponse({ ok: true, data: findChatFromButtons(msg.query) });
                break;
            case "max_send_message":
                sendResponse({ ok: true, data: sendMessageReal(msg.text) });
                break;
            case "max_send_finalize":
                sendResponse({ ok: true, data: sendMessageFinalize() });
                break;
            case "max_clear_input":
                sendResponse({ ok: true, data: clearMessageInput() });
                break;
            case "max_title":
                sendResponse({ ok: true, data: { title: document.title, url: location.href } });
                break;
            case "max_read_last":
                sendResponse({ ok: true, data: readLastMessage() });
                break;
            default:
                sendResponse({ ok: false, error: "unknown action: " + msg.action });
        }
    } catch (e) {
        console.error("[Aura Max] error:", e);
        sendResponse({ ok: false, error: e.toString() });
    }
    return true;  // async
});

// --- Диагностика ---
function deepDump() {
    // Глубокий дамп — 3 уровня DOM, с фильтром по интерактивным элементам.
    const info = {
        url: location.href,
        title: document.title,
        main: [],
        buttons: [],
        inputs: [],
        roles: {}
    };

    // Кнопки — все кликабельные
    document.querySelectorAll("button, [role=button]").forEach((el, i) => {
        if (i > 40) return;
        const text = (el.innerText || el.getAttribute("aria-label") || "").trim();
        info.buttons.push({
            i: i,
            tag: el.tagName,
            role: el.getAttribute("role"),
            ariaLabel: el.getAttribute("aria-label"),
            text: text.substring(0, 60)
        });
    });

    // Инпуты и textarea
    document.querySelectorAll("input, textarea, [contenteditable=true]").forEach((el, i) => {
        if (i > 10) return;
        info.inputs.push({
            i: i,
            tag: el.tagName,
            type: el.getAttribute("type"),
            placeholder: el.getAttribute("placeholder"),
            ariaLabel: el.getAttribute("aria-label"),
            contentEditable: el.getAttribute("contenteditable"),
            cls: (el.className || "").substring(0, 60)
        });
    });

    // Статистика по ролям
    document.querySelectorAll("[role]").forEach(el => {
        const r = el.getAttribute("role");
        info.roles[r] = (info.roles[r] || 0) + 1;
    });

    // 2 уровня main
    const main = document.querySelector("main");
    if (main) {
        info.main.push({ level: 0, tag: "MAIN", cls: (main.className||"").substring(0,60) });
        Array.from(main.children).forEach((c, i) => {
            if (i > 15) return;
            info.main.push({
                level: 1,
                i: i,
                tag: c.tagName,
                cls: (c.className || "").substring(0, 60),
                role: c.getAttribute("role"),
                ariaLabel: c.getAttribute("aria-label"),
                childCount: c.children.length,
                text: (c.innerText || "").substring(0, 60).replace(/\n/g, " | ")
            });
        });
    }

    return info;
}

function dumpStructure() {
    // Собираем верхнеуровневые элементы — что есть на странице.
    const info = {
        url: location.href,
        title: document.title,
        readyState: document.readyState,
        elements: []
    };

    // Ищем крупные контейнеры
    const containers = document.querySelectorAll("main, [role=main], [class*=chat], [class*=sidebar], [class*=list]");
    containers.forEach((el, i) => {
        if (i > 15) return;  // ограничим
        info.elements.push({
            tag: el.tagName,
            role: el.getAttribute("role"),
            cls: (el.className || "").substring(0, 80),
            ariaLabel: el.getAttribute("aria-label"),
            text: (el.innerText || "").substring(0, 80).replace(/\n/g, " ")
        });
    });

    return info;
}

function listChats() {
    // Ищем элементы похожие на чаты в списке.
    // Эвристики: role=listitem, или класс со словами chat/dialog/item.
    const candidates = document.querySelectorAll(
        "[role=listitem], [role=option], [class*=chat-item], [class*=dialog], [class*=conversation]"
    );
    const chats = [];
    candidates.forEach((el, i) => {
        if (i > 30) return;
        const text = (el.innerText || "").trim();
        if (text.length < 1) return;
        chats.push({
            index: i,
            text: text.substring(0, 100).replace(/\n/g, " | ")
        });
    });
    return { count: chats.length, chats };
}

function findChat(query) {
    const q = (query || "").toLowerCase();
    if (!q) return { found: false, error: "empty query" };

    const candidates = document.querySelectorAll(
        "[role=listitem], [role=option], [class*=chat-item], [class*=dialog], [class*=conversation]"
    );
    for (const el of candidates) {
        const text = (el.innerText || "").toLowerCase();
        if (text.includes(q)) {
            // Клик по элементу
            el.click();
            return { found: true, text: text.substring(0, 100) };
        }
    }
    return { found: false, query: q };
}


// --- Реальные функции для Макса (по дампу 2026-09-24) ---

function listChatsFromButtons() {
    const items = document.querySelectorAll("[role=listitem]");
    const chats = [];
    items.forEach((el, i) => {
        if (i > 50) return;
        const rect = el.getBoundingClientRect();
        // Левая панель со списком чатов — x < 500.
        // Сообщения в открытом чате — x > 500.
        if (rect.left > 500) return;
        const text = (el.innerText || "").trim();
        if (text.length === 0) return;
        const lines = text.split("\n").filter(l => l.trim());
        chats.push({
            index: i,
            name: lines[0] || "",
            preview: lines.slice(1, 3).join(" | "),
            x: Math.round(rect.left)
        });
    });
    return { count: chats.length, chats: chats };
}

function findChatReal(query) {
    const q = (query || "").toLowerCase().trim();
    if (q.length === 0) return { found: false, error: "empty query" };

    const searchInput = document.querySelector('input[placeholder="Найти"]');
    if (searchInput) {
        searchInput.focus();
        searchInput.value = query;
        searchInput.dispatchEvent(new Event("input", { bubbles: true }));
    }

    const items = document.querySelectorAll("[role=listitem]");
    for (const el of items) {
        const text = (el.innerText || "").toLowerCase();
        if (text.includes(q)) {
            el.click();
            return { found: true, name: text.split("\n")[0].substring(0, 60) };
        }
    }
    return { found: false, query: q, triedSearch: searchInput !== null };
}

function findMessageInput() {
    const candidates = document.querySelectorAll("[role=textbox], [contenteditable=true]");
    for (const el of candidates) {
        const ph = el.getAttribute("placeholder") || "";
        if (ph.toLowerCase().includes("найти")) continue;
        return el;
    }
    return null;
}

function sendMessageReal(text) {
    if (!text || text.length === 0) return { sent: false, error: "empty text" };
    const input = findMessageInput();
    if (input === null) return { sent: false, error: "message input not found" };

    input.focus();
    if (input.tagName === "TEXTAREA" || input.tagName === "INPUT") {
        input.value = text;
        input.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
        input.innerText = text;
        input.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }
    return { sent: false, typed: true, text: text.substring(0, 100) };
}

function readLastMessage() {
    const main = document.querySelector("main");
    if (main === null) return { error: "no main" };
    const messages = main.querySelectorAll("[class*=message], [class*=bubble]");
    if (messages.length === 0) {
        return { last: (main.innerText || "").slice(-500) };
    }
    const last = messages[messages.length - 1];
    return { last: (last.innerText || "").substring(0, 300) };
}


function listChatsFromButtons() {
    // Чаты — это <button> в левой панели (x < 400).
    const buttons = document.querySelectorAll("button");
    const chats = [];
    buttons.forEach((el, i) => {
        const rect = el.getBoundingClientRect();
        if (rect.left > 400) return;
        if (rect.width < 100) return;
        const text = (el.innerText || "").trim();
        if (text.length === 0) return;
        if (text === "Еще") return;
        const lines = text.split("\n").filter(l => l.trim());
        if (lines.length < 2) return;
        chats.push({
            index: i,
            name: lines[0] || "",
            preview: lines.slice(1, 3).join(" | ")
        });
    });
    return { count: chats.length, chats: chats };
}

function findChatFromButtons(query) {
    const q = (query || "").toLowerCase().trim();
    if (q.length === 0) return { found: false, error: "empty query" };
    // Fuzzy: обрезаем окончания для падежей.
    const stems = [q];
    if (q.length > 4) stems.push(q.substring(0, q.length - 1));
    if (q.length > 5) stems.push(q.substring(0, q.length - 2));
    const buttons = document.querySelectorAll("button");
    for (const el of buttons) {
        const rect = el.getBoundingClientRect();
        if (rect.left > 400) continue;
        if (rect.width < 100) continue;
        const text = (el.innerText || "").toLowerCase();
        if (text === "еще") continue;
        for (const stem of stems) {
            if (text.includes(stem)) {
                el.click();
                const lines = text.split("\n").filter(l => l.trim());
                return { found: true, name: lines[0] || "", matched: stem };
            }
        }
    }
    return { found: false, query: q };
}


function sendMessageFinalize() {
    // Отправить уже введённый текст. Пробуем Enter, потом кнопку.
    const input = findMessageInput();
    if (input === null) return { sent: false, error: "message input not found" };

    // Способ 1: симулируем Enter.
    input.focus();
    const enterEvent = new KeyboardEvent("keydown", {
        key: "Enter",
        code: "Enter",
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true,
    });
    input.dispatchEvent(enterEvent);

    // Способ 2 (fallback): ищем кнопку «Отправить».
    // По дампу кнопки в Максе без aria-label, но с иконкой.
    // Попробуем найти по type=submit или рядом с полем.
    setTimeout(() => {
        // Если поле пустое — значит Enter сработал.
        const val = (input.innerText || input.value || "").trim();
        if (val.length > 0) {
            const submit = document.querySelector('button[type=submit], [aria-label*="тправить" i]');
            if (submit) submit.click();
        }
    }, 300);

    return { sent: true };
}

function clearMessageInput() {
    // Очистить поле ввода.
    const input = findMessageInput();
    if (input === null) return { cleared: false, error: "message input not found" };

    input.focus();
    if (input.tagName === "TEXTAREA" || input.tagName === "INPUT") {
        input.value = "";
        input.dispatchEvent(new Event("input", { bubbles: true }));
    } else {
        input.innerText = "";
        input.dispatchEvent(new InputEvent("input", { bubbles: true }));
    }
    return { cleared: true };
}




