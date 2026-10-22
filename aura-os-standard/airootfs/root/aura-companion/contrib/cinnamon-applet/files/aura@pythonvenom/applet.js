const Applet = imports.ui.applet;
const Soup = imports.gi.Soup;
const Mainloop = imports.mainloop;
const Gio = imports.gi.Gio;

const API_URL = 'http://127.0.0.1:8765';

function AuraApplet(metadata, orientation, panelHeight, instanceId) {
    this._init(metadata, orientation, panelHeight, instanceId);
}

AuraApplet.prototype = {
    __proto__: Applet.IconApplet.prototype,
    _init: function(metadata, orientation, panelHeight, instanceId) {
        Applet.IconApplet.prototype._init.call(this, orientation, panelHeight, instanceId);
        this.set_applet_icon_name('audio-input-microphone');
        this.set_applet_tooltip('Aura');
        this._session = new Soup.Session();
        this._timeout = Mainloop.timeout_add_seconds(2, () => {
            this._poll();
            return true;
        });
        this._poll();
    },
    _poll: function() {
        let msg = Soup.Message.new('GET', API_URL + '/status');
        this._session.queue_message(msg, (s, m) => {
            try {
                let data = JSON.parse(m.response_body.data);
                this.set_applet_tooltip('Aura: ' + (data.state || '?'));
            } catch (e) {}
        });
    },
    on_applet_clicked: function() {
        Gio.AppInfo.launch_default_for_uri(API_URL + '/ui', null);
    }
};

function main(metadata, orientation, panelHeight, instanceId) {
    return new AuraApplet(metadata, orientation, panelHeight, instanceId);
}
