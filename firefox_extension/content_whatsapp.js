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
        // Bug 51: WhatsApp использует role=row (не listitem).
        const pane = document.querySelector("#pane-side");
        if (pane) {
            const rows = pane.querySelectorAll('[role="row"]');
            if (rows.length > 0) return rows;
        }
        // fallback
        return document.querySelectorAll('[role="row"], [role="listitem"]');
    }

    function findMessageInput() {
        // Bug 51: WhatsApp в 2026 использует data-testid или role=textbox.
        return document.querySelector('[data-testid="conversation-compose-box-input"]')
            || document.querySelector('footer [contenteditable="true"]')
            || document.querySelector('div[contenteditable="true"][data-tab="10"]')
            || document.querySelector('div[contenteditable="true"][data-tab="6"]')
            || document.querySelector('[role="textbox"][contenteditable="true"]')
            || document.querySelector('div[title="Type a message"]')
            || document.querySelector('div[aria-label*="Сообщение" i]')
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
            sidebars: [],
            // Расширенная диагностика
            counts: {
                all: document.querySelectorAll("*").length,
                div: document.querySelectorAll("div").length,
                role_any: document.querySelectorAll("[role]").length,
                contenteditable: document.querySelectorAll("[contenteditable]").length,
                aria_label: document.querySelectorAll("[aria-label]").length,
                data_tab: document.querySelectorAll("[data-tab]").length,
                data_testid: document.querySelectorAll("[data-testid]").length,
                pane_side: !!document.querySelector("#pane-side"),
                main: !!document.querySelector("main, #main, [role=main]"),
            },
            body_ready: document.readyState,
            body_len: document.body ? document.body.innerHTML.length : 0
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

    function _clickRow(el) {
        // Bug 58: React/Preact в WhatsApp. Стратегия:
        // 1. inner [role=button] или [role=link] — click
        // 2. MouseEvent (pointerdown → pointerup → click) на сам row
        // 3. Native .click() fallback
        try {
            const inner = el.querySelector('[role="button"], [role="link"]');
            if (inner) {
                inner.click();
                return;
            }
            const rect = el.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            for (const type of ["pointerdown", "mousedown", "pointerup", "mouseup", "click"]) {
                const ev = new MouseEvent(type, {
                    bubbles: true, cancelable: true, composed: true,
                    view: window, clientX: cx, clientY: cy,
                });
                el.dispatchEvent(ev);
            }
        } catch (e) {
            _clickRow(el);
        }
    }

    function findChat(query) {
        const q = (query || "").toLowerCase().trim();
        if (!q) return { found: false, error: "empty query" };

        // Fuzzy стемы для падежей.
        const stems = [q];
        if (q.length > 4) stems.push(q.substring(0, q.length - 1));
        if (q.length > 5) stems.push(q.substring(0, q.length - 2));

        // 1. Поиск по видимым чатам (role=row).
        const items = findChatItems();
        for (const el of items) {
            const titleEl = el.querySelector('[title]');
            const text = ((titleEl?.getAttribute("title") || el.innerText) || "").toLowerCase();
            for (const stem of stems) {
                if (text.includes(stem)) {
                    // Bug 58: WhatsApp = React. Простой .click() не триггерит.
                    // Используем комбинацию: click на inner button + MouseEvent на row.
                    _clickRow(el);
                    const name = titleEl?.getAttribute("title") || text.split("\n")[0] || "";
                    return { found: true, name: name.substring(0, 60), matched: stem };
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
        // Bug 51: WhatsApp data-id на div сообщения.
        const main = document.querySelector('[data-testid="conversation-panel-messages"]')
            || document.querySelector("#main");
        if (!main) return { error: "no main" };

        // Строки с сообщениями: .message-in или .message-out
        const bubbles = main.querySelectorAll(
            'div.message-in, div.message-out, [data-id^="true"], [data-id^="false"]'
        );
        if (bubbles.length === 0) {
            return { last: (main.innerText || "").slice(-500) };
        }
        const last = bubbles[bubbles.length - 1];
        // Текст внутри: span.selectable-text или .copyable-text
        const textEl = last.querySelector("span.selectable-text") 
            || last.querySelector(".copyable-text")
            || last;
        const text = (textEl.innerText || "").trim();
        return {
            last: text.substring(0, 300),
            direction: last.classList.contains("message-in") ? "in" : "out"
        };
    }

    function getTitle() {
        // Bug 51: точный селектор WhatsApp.
        const el = document.querySelector('[data-testid="conversation-info-header-chat-title"]')
            || document.querySelector('header [title]')
            || document.querySelector('header span[dir="auto"]');
        if (el) {
            const title = (el.getAttribute("title") || el.innerText || "").trim();
            return { title: title.substring(0, 100) };
        }
        const header = document.querySelector('header');
        if (header) {
            const title = (header.innerText || "").split("\n")[0].trim();
            return { title: title.substring(0, 100) };
        }
        return { title: document.title };
    }

    // --- Слушаем команды от background.js (browser.runtime.onMessage) ---
browser.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    console.log("[Aura WhatsApp] got action:", msg.action);
    try {
        switch (msg.action) {
            case "wa_dump":
                sendResponse({ ok: true, data: deepDump() });
                break;
            case "wa_list_chats":
                sendResponse({ ok: true, data: listChats() });
                break;
            case "wa_find_chat":
                sendResponse({ ok: true, data: findChat(msg.query || "") });
                break;
            case "wa_send_message":
                sendResponse({ ok: true, data: sendMessageReal(msg.text || "") });
                break;
            case "wa_send_finalize":
                sendResponse({ ok: true, data: sendMessageFinalize() });
                break;
            case "wa_dump_send_ui":
                sendResponse({ ok: true, data: dumpSendUI() });
                break;
            case "wa_clear_input":
                sendResponse({ ok: true, data: clearMessageInput() });
                break;
            case "wa_title":
                sendResponse({ ok: true, data: getTitle() });
                break;
            case "wa_read_last":
                sendResponse({ ok: true, data: readLastMessage() });
                break;
            default:
                sendResponse({ ok: false, error: "unknown action: " + msg.action });
        }
    } catch (e) {
        sendResponse({ ok: false, error: e.message });
    }
    return true;  // async
});

console.log("[Aura WhatsApp] content_whatsapp.js loaded");

})();
