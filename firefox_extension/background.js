// Aura Bridge — фоновая логика Firefox
// Общается с native host через stdin/stdout

let nativePort = null;

function connectNative() {
    try {
        nativePort = browser.runtime.connectNative("aura_bridge");
        console.log("[Aura] Native host подключён");

        nativePort.onMessage.addListener(async (msg) => {
            console.log("[Aura] Получено:", msg);
            try {
                const response = await handleCommand(msg);
                nativePort.postMessage({ id: msg.id, ...response });
            } catch (e) {
                nativePort.postMessage({ id: msg.id, error: e.toString() });
            }
        });

        nativePort.onDisconnect.addListener((p) => {
            console.log("[Aura] Native host отключён:", p.error?.message);
            nativePort = null;
            // Переподключиться через 3 сек
            setTimeout(connectNative, 3000);
        });
    } catch (e) {
        console.error("[Aura] Ошибка подключения:", e);
        setTimeout(connectNative, 3000);
    }
}

async function findTelegramTab() {
    const tabs = await browser.tabs.query({ url: "*://web.telegram.org/*" });
    return tabs[0] || null;
}

async function findVKTab() {
    const tabs = await browser.tabs.query({ url: "*://vk.com/*" });
    return tabs[0] || null;
}

async function findMaxTab() {
    // Ищем открытую вкладку max.ru. Если нет — null.
    const tabs = await browser.tabs.query({});
    for (const t of tabs) {
        if (t.url && (t.url.includes("max.ru") || t.url.includes("web.max.ru"))) {
            return t;
        }
    }
    return null;
}

async function handleCommand(msg) {
    const action = msg.action;

    switch (action) {
        case "list_tabs": {
            const tabs = await browser.tabs.query({});
            return {
                tabs: tabs.map(t => ({
                    id: t.id,
                    title: t.title,
                    url: t.url,
                    active: t.active,
                    windowId: t.windowId,
                    index: t.index
                }))
            };
        }

        case "find_tab": {
            const query = (msg.query || "").toLowerCase();
            const tabs = await browser.tabs.query({});
            const matches = tabs.filter(t =>
                t.title.toLowerCase().includes(query) ||
                t.url.toLowerCase().includes(query)
            );
            return {
                tabs: matches.map(t => ({
                    id: t.id,
                    title: t.title,
                    url: t.url,
                    active: t.active
                }))
            };
        }

        case "activate_tab": {
            const tabId = msg.tab_id;
            if (!tabId) return { error: "no tab_id" };
            const tab = await browser.tabs.get(tabId);
            await browser.tabs.update(tabId, { active: true });
            await browser.windows.update(tab.windowId, { focused: true });
            return { success: true, title: tab.title };
        }

        case "close_tab": {
            const tabId = msg.tab_id;
            if (!tabId) return { error: "no tab_id" };
            await browser.tabs.remove(tabId);
            return { success: true };
        }

        case "close_tab_by_name": {
            const query = (msg.query || "").toLowerCase();
            const tabs = await browser.tabs.query({});
            const matches = tabs.filter(t =>
                t.title.toLowerCase().includes(query) ||
                t.url.toLowerCase().includes(query)
            );
            if (matches.length === 0) {
                return { error: "not found" };
            }
            // Закрыть первое совпадение
            const tab = matches[0];
            await browser.tabs.remove(tab.id);
            return { success: true, title: tab.title };
        }

        case "focus_tab_by_name": {
            const query = (msg.query || "").toLowerCase();
            const tabs = await browser.tabs.query({});
            const matches = tabs.filter(t =>
                t.title.toLowerCase().includes(query) ||
                t.url.toLowerCase().includes(query)
            );
            if (matches.length === 0) {
                return { error: "not found" };
            }
            const tab = matches[0];
            await browser.tabs.update(tab.id, { active: true });
            await browser.windows.update(tab.windowId, { focused: true });
            return { success: true, title: tab.title };
        }

        case "open_tab": {
            const url = msg.url;
            if (!url) return { error: "no url" };
            const tab = await browser.tabs.create({ url, active: msg.active !== false });
            return { success: true, tabId: tab.id, title: tab.title };
        }

        case "new_tab_search": {
            const query = msg.query || "";
            const url = `https://www.google.com/search?q=${encodeURIComponent(query)}`;
            const tab = await browser.tabs.create({ url, active: true });
            return { success: true, tabId: tab.id };
        }

        case "next_tab": {
            const tabs = await browser.tabs.query({ currentWindow: true });
            const active = tabs.find(t => t.active);
            if (!active) return { error: "no active tab" };
            const nextIndex = (active.index + 1) % tabs.length;
            await browser.tabs.update(tabs[nextIndex].id, { active: true });
            return { success: true, title: tabs[nextIndex].title };
        }

        case "prev_tab": {
            const tabs = await browser.tabs.query({ currentWindow: true });
            const active = tabs.find(t => t.active);
            if (!active) return { error: "no active tab" };
            const prevIndex = (active.index - 1 + tabs.length) % tabs.length;
            await browser.tabs.update(tabs[prevIndex].id, { active: true });
            return { success: true, title: tabs[prevIndex].title };
        }

                // === Max.ru (Фаза 13.1) ===
        case "max_dump_structure":
        case "max_list_chats":
	case "max_deep_dump":
        case "max_send_finalize":
        case "max_dump_send_ui":
        case "max_clear_input":
        case "max_send_message":
        case "max_read_last":
        case "max_title":
        case "tg_list_chats":
        case "tg_find_chat":
        case "tg_send_message":
        case "tg_finalize":
        case "tg_current": {
            const tgTab = await findTelegramTab();
            if (!tgTab) return { error: "telegram tab not found" };
            const payload = { action: action };
            if (msg.query) payload.query = msg.query;
            if (msg.text) payload.text = msg.text;
            try {
                return await browser.tabs.sendMessage(tgTab.id, payload);
            } catch (e) {
                return { error: "content script: " + e.toString() };
            }
        }
        case "vk_list_shortcuts":
        case "vk_navigate":
        case "vk_list_chats":
        case "vk_list_friends":
        case "vk_list_groups":
        case "vk_list_news":
        case "vk_next_track":
        case "vk_prev_track":
        case "vk_send_message":
        case "vk_finalize":
        case "vk_current": {
            const vkTab = await findVKTab();
            if (!vkTab) return { error: "vk tab not found" };
            const payload = { action: action };
            if (msg.section) payload.section = msg.section;
            if (msg.text) payload.text = msg.text;
            if (msg.query) payload.query = msg.query;
            try {
                return await browser.tabs.sendMessage(vkTab.id, payload);
            } catch (e) {
                return { error: "content script: " + e.toString() };
            }
        }
        case "max_find_chat": {
            const maxTab = await findMaxTab();
            if (!maxTab) return { error: "max tab not found" };
            const payload = { action: action };
            if (msg.query) payload.query = msg.query;
            if (msg.text) payload.text = msg.text;
            if (msg.tab_id) payload.tab_id = msg.tab_id;
            try {
                return await browser.tabs.sendMessage(maxTab.id, payload);
            } catch (e) {
                return { error: "content script: " + e.toString() };
            }
        }
	case "ping":
            return { pong: true, version: "1.0" };

        default:
            return { error: `unknown action: ${action}` };
    }
}

// Подключаемся при старте
connectNative();

// Подключаемся при загрузке расширения
browser.runtime.onInstalled.addListener(() => {
    console.log("[Aura] Extension installed");
    if (!nativePort) connectNative();
});

browser.runtime.onStartup.addListener(() => {
    if (!nativePort) connectNative();
});

console.log("[Aura Bridge] Background script loaded");
