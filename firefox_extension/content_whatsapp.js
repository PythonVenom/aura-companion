// content_whatsapp.js — мост Aura ↔ WhatsApp Web.
// По аналогии с content_max.js.
// Селекторы WhatsApp Web (2026-09).

(function() {
    "use strict";

    // --- Утилиты ---

    function findSidebar() {
        // Левая панель со списком чатов.
        return document.querySelector('[aria-label="Chat list"]')
            || document.querySelector('div[data-testid="chat-list"]')
            || document.querySelector("#pane-side")
            || document.querySelector('[role="grid"]');
    }

    function findChatItems() {
        // Чаты — role=listitem внутри боковой панели.
        const pane = document.querySelector("#pane-side");
        if (pane) {
            return pane.querySelectorAll('[role="listitem"]');
        }
        const sidebar = findSidebar();
        if (sidebar) return sidebar.querySelectorAll('[role="listitem"]');
        return document.querySelectorAll('[role="listitem"]');
    }

    function findMessageInput() {
        // Поле ввода. В WA — contenteditable с data-tab="10" или aria-label.
        return document.querySelector('div[contenteditable="true"][data-tab="10"]')
            || document.querySelector('div[contenteditable="true"][data-tab="6"]')
            || document.querySelector('footer div[contenteditable="true"]')
            || document.querySelector('div[title="Type a message"]')
            || document.querySelector('div[aria-label*="message" i][contenteditable="true"]');
    }

    function findSearchInput() {
        return document.querySelector('div[contenteditable="true"][data-tab="3"]')
            || document.querySelector('div[title="Search input textbox"]')
            || document.querySelector('[aria-label="Search input textbox"]');
    }

    // --- Диагностика ---

    function deepDump() {
        const info = {
            url: location.href,
            title: document.title,
            buttons: [],
            inputs: [],
            roles: {},
            sidebars: []
        };

        document.querySelectorAll("button, [role=button]").forEach((el, i) => {
            if (i > 40) return;
            const text = (el.innerText || el.getAttribute("aria-label") || "").trim();
            info.buttons.push({
                i: i,
                tag: el.tagName,
                ariaLabel: el.getAttribute("aria-label"),
                title: el.getAttribute("title"),
                dataTestId: el.getAttribute("data-testid"),
                text: text.substring(0, 60)
            });
        });

        document.querySelectorAll("input, textarea, [contenteditable=true]").forEach((el, i) => {
            if (i > 10) return;
            info.inputs.push({
                i: i,
                tag: el.tagName,
                role: el.getAttribute("role"),
                dataTab: el.getAttribute("data-tab"),
                ariaLabel: el.getAttribute("aria-label"),
                placeholder: el.getAttribute("placeholder") || el.getAttribute("title"),
                contentEditable: el.getAttribute("contenteditable"),
                cls: (el.className || "").substring(0, 60)
            });
        });

        document.querySelectorAll("[role]").forEach(el => {
            const r = el.getAttribute("role");
            info.roles[r] = (info.roles[r] || 0) + 1;
        });

        // Sidebar info
        const pane = document.querySelector("#pane-side");
        if (pane) {
            info.sidebars.push({
                id: "pane-side",
                childCount: pane.children.length,
                cls: (pane.className || "").substring(0, 80)
            });
        }

        return info;
    }

    // --- Список чатов ---

    function listChats() {
        const items = findChatItems();
        const chats = [];
        items.forEach((el, i) => {
            if (i > 50) return;
            const rect = el.getBoundingClientRect();
            if (rect.width < 50) return;
            const text = (el.innerText || "").trim();
            if (!text) return;
            const lines = text.split("\n").filter(l => l.trim());
            chats.push({
                index: i,
                name: lines[0] || "",
                preview: lines.slice(1, 3).join(" | "),
                x: Math.round(rect.left),
                y: Math.round(rect.top)
            });
        });
        return { count: chats.length, chats: chats };
    }

    // --- Поиск чата ---

    function findChat(query) {
        const q = (query || "").toLowerCase().trim();
        if (!q) return { found: false, error: "empty query" };

        // Fuzzy стемы для падежей.
        const stems = [q];
        if (q.length > 4) stems.push(q.substring(0, q.length - 1));
        if (q.length > 5) stems.push(q.substring(0, q.length - 2));

        // 1. Поиск по видимым чатам.
        const items = findChatItems();
        for (const el of items) {
            const text = (el.innerText || "").toLowerCase();
            for (const stem of stems) {
                if (text.includes(stem)) {
                    el.click();
                    const lines = text.split("\n").filter(l => l.trim());
                    return { found: true, name: lines[0] || "", matched: stem };
                }
            }
        }

        // 2. Если не нашли — через поиск.
        const search = findSearchInput();
        if (search) {
            search.focus();
            // contenteditable — execCommand.
            document.execCommand("selectAll", false, null);
            document.execCommand("insertText", false, query);
            // Ждём фильтрации
            // Возвращаем false, клиент повторит.
            return { found: false, query: q, triedSearch: true };
        }

        return { found: false, query: q };
    }

    // --- Поле ввода / отправка ---

    function dumpSendUI() {
        const input = findMessageInput();
        const info = { input: null, buttons: [] };
        if (input) {
            info.input = {
                tagName: input.tagName,
                role: input.getAttribute("role"),
                contentEditable: input.isContentEditable,
                dataTab: input.getAttribute("data-tab"),
                ariaLabel: input.getAttribute("aria-label"),
                placeholder: input.getAttribute("data-placeholder") || input.getAttribute("title"),
                cls: (input.className || "").substring(0, 100)
            };
            const footer = input.closest("footer");
            if (footer) {
                footer.querySelectorAll("button, [role=button]").forEach(b => {
                    info.buttons.push({
                        tag: b.tagName,
                        ariaLabel: b.getAttribute("aria-label"),
                        title: b.getAttribute("title"),
                        dataTestId: b.getAttribute("data-testid"),
                        span: b.querySelector("span[data-icon]")?.getAttribute("data-icon") || null,
                        visible: b.offsetParent !== null
                    });
                });
            }
        }
        return info;
    }

    function sendMessageReal(text) {
        if (!text) return { sent: false, error: "empty text" };
        const input = findMessageInput();
        if (!input) return { sent: false, error: "message input not found" };

        input.focus();
        // contenteditable → execCommand (WA слушает input events).
        document.execCommand("selectAll", false, null);
        document.execCommand("delete", false, null);
        document.execCommand("insertText", false, text);
        return { typed: true, text: text.substring(0, 100) };
    }

    function sendMessageFinalize() {
        const input = findMessageInput();
        if (!input) return { sent: false, error: "input not found" };

        input.focus();

        // 1. Пробуем кнопку Send.
        const sendBtn = document.querySelector('button[aria-label="Send"]')
            || document.querySelector('span[data-icon="send"]')?.closest("button")
            || document.querySelector('span[data-icon="wds-ic-send-filled"]')?.closest("button");
        if (sendBtn) {
            sendBtn.click();
            return { sent: true, method: "button" };
        }

        // 2. Fallback — Enter.
        for (const type of ["keydown", "keypress", "keyup"]) {
            const ev = new KeyboardEvent(type, {
                key: "Enter", code: "Enter", keyCode: 13, which: 13,
                bubbles: true, cancelable: true, composed: true,
            });
            input.dispatchEvent(ev);
        }
        return { sent: true, method: "enter" };
    }

    function clearMessageInput() {
        const input = findMessageInput();
        if (!input) return { cleared: false, error: "input not found" };
        input.focus();
        document.execCommand("selectAll", false, null);
        document.execCommand("delete", false, null);
        return { cleared: true };
    }

    // --- Чтение ---

    function readLastMessage() {
        // Сообщения: div[data-id] внутри main или .message-in/.message-out.
        const main = document.querySelector('div[data-testid="conversation-panel-messages"]')
            || document.querySelector("#main");
        if (!main) return { error: "no main" };

        const bubbles = main.querySelectorAll('div.message-in, div.message-out, div[data-id^="true"], div[data-id^="false"]');
        if (bubbles.length === 0) {
            // fallback — общий текст.
            return { last: (main.innerText || "").slice(-500) };
        }
        const last = bubbles[bubbles.length - 1];
        const text = (last.querySelector("span.selectable-text")?.innerText || last.innerText || "").trim();
        return {
            last: text.substring(0, 300),
            direction: last.classList.contains("message-in") ? "in" : "out"
        };
    }

    function getTitle() {
        // Название активного чата.
        const header = document.querySelector('header');
        if (!header) return { title: document.title };
        const title = (header.innerText || "").split("\n")[0].trim();
        return { title: title.substring(0, 100) };
    }

    // --- Message router от background ---

    window.addEventListener("message", async (event) => {
        if (event.source !== window) return;
        const msg = event.data;
        if (!msg || !msg.action) return;
        console.log("[Aura WhatsApp] got action:", msg.action);

        let result = null;
        try {
            switch (msg.action) {
                case "wa_dump":
                    result = deepDump();
                    break;
                case "wa_list_chats":
                    result = listChats();
                    break;
                case "wa_find_chat":
                    result = findChat(msg.query || "");
                    break;
                case "wa_send_message":
                    result = sendMessageReal(msg.text || "");
                    break;
                case "wa_send_finalize":
                    result = sendMessageFinalize();
                    break;
                case "wa_dump_send_ui":
                    result = dumpSendUI();
                    break;
                case "wa_clear_input":
                    result = clearMessageInput();
                    break;
                case "wa_title":
                    result = getTitle();
                    break;
                case "wa_read_last":
                    result = readLastMessage();
                    break;
                default:
                    result = { ok: false, error: "unknown action: " + msg.action };
            }
        } catch (e) {
            result = { ok: false, error: e.message };
        }

        window.postMessage({ __aura_response: true, requestId: msg.requestId, result: result }, "*");
    });

    console.log("[Aura WhatsApp] content_whatsapp.js loaded");
})();
