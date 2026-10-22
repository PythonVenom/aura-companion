import GObject from 'gi://GObject';
import St from 'gi://St';
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';

const API_URL = 'http://127.0.0.1:8765';

const AuraIndicator = GObject.registerClass(
class AuraIndicator extends PanelMenu.Button {
    _init() {
        super._init(0.0, 'Aura');
        this._icon = new St.Icon({
            icon_name: 'audio-input-microphone',
            style_class: 'system-status-icon',
        });
        this.add_child(this._icon);
        this._timeout = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, 2, () => {
            this._poll();
            return GLib.SOURCE_CONTINUE;
        });
        this._poll();
    }
    _poll() {
        const file = Gio.File.new_for_uri(API_URL + '/status');
        file.load_contents_async(null, (src, res) => {
            try {
                const [ok, contents] = src.load_contents_finish(res);
                const data = JSON.parse(new TextDecoder().decode(contents));
                this._icon.icon_name = this._iconFor(data.state || 'unknown');
            } catch (e) {
                this._icon.icon_name = 'dialog-question';
            }
        });
    }
    _iconFor(state) {
        const map = {
            idle: 'audio-input-microphone',
            listening: 'audio-input-microphone-symbolic',
            thinking: 'emblem-synchronizing',
            speaking: 'audio-volume-high',
            paused: 'media-playback-pause',
            error: 'dialog-error',
        };
        return map[state] || 'dialog-question';
    }
    destroy() {
        if (this._timeout) { GLib.source_remove(this._timeout); this._timeout = null; }
        super.destroy();
    }
});

let indicator = null;

export default class AuraExtension extends Extension {
    enable() {
        indicator = new AuraIndicator();
        Main.panel.addToStatusArea('aura', indicator);
    }
    disable() {
        if (indicator) { indicator.destroy(); indicator = null; }
    }
}
