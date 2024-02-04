$(function () {
    /**
     * Updates the Copywrite year on document ready
     */
    $("#copyYear").text(new Date().getFullYear());

    /**
     * Redirect page when modal dialog is shown
     */
    var popupModal = document.getElementById("popupModal");

    popupModal.addEventListener("shown.bs.modal", function (e) {
        window.location.href = $("#reload").data("href");
    });

    /**
     * On click of an element with attribute "data-clipboard-src", updates clipboard with text from that element
     */
    if (navigator.clipboard) {
        /* Clipboard support present: link clipboard icons to source object */
        $("[data-clipboard-src]").each(function(i, elm) {
            $(elm).on("click", function () {
                const src = $(elm).attr("data-clipboard-src");
                const value = $(src).text();
                navigator.clipboard.writeText(value);
                console.log(`Copied ${value} to clipboard`);
            });
        });
    } else {
        /* Clipboard support missing: remove clipboard icons to minimize confusion */
        $("[data-clipboard-src]").remove();
    };

    /**
     * Initializes bootstrap alerts and sets a timeout for when they should automatically close
     */
    $(".alert").each(function (i, alert) {
        var bsalert = new bootstrap.Alert(alert);
        setTimeout(() => {
            bsalert.close();
        }, +alert.getAttribute("data-timeout"));
    });

    /**
     * Get temperature from input
     * @param {number} temp Temperature in Celsius
     * @returns {number} Rounded temperature
     */
    function getTemp(temp) {
        return Math.round(temp / 100);
    }

    /**
     * Calculate the percentage between two numbers
     * @param {number} layer
     * @param {number} total
     * @returns {number} percentage
     */
    function getPercentage(progress) {
        return Math.round(((progress / 100) * 100) / 100);
    }

    /**
     * Convert time in seconds to hours, minutes, and seconds format
     * @param {number} totalseconds
     * @returns {string} Formatted time string
     */
    function getTime(totalseconds) {
        const hours = Math.floor(totalseconds / 3600);
        const minutes = Math.floor((totalseconds % 3600) / 60);
        const seconds = totalseconds % 60;

        const timeString =
            `${hours.toString().padStart(2, "0")}:` +
            `${minutes.toString().padStart(2, "0")}:` +
            `${seconds.toString().padStart(2, "0")}`;

        return timeString;
    }

    /**
     * Calculates the AnkerMake M5 Speed ratio ("X-factor")
     * @param {number} speed - The speed value in mm/s
     * @return {number} The speed factor in units of "X" (50mm/s)
     */
    function getSpeedFactor(speed) {
        return `X${speed / 50}`;
    }

    /**
     * Updates the country code <select> element
     */
    (function(selectElement) {
        var countryCodes = selectElement.data("countrycodes");
        var currentCountry = selectElement.data("country");
        countryCodes.forEach((item) => {
            var selected = (currentCountry == item.c) ? " selected" : "";
            $(`<option value="${item.c}"${selected}>${item.n}</option>`).appendTo(selectElement);
        });
    })($("#loginCountry"));

    /**
     * Login data submission and CAPTCHA handling
     */
    $("#captchaRow").hide();
    $("#loginCaptchaId").val("");

    $("#config-login-form").on("submit", function(e) {
        e.preventDefault();

        (async () => {
            const form = $("#config-login-form");
            const url = form.attr("action");

            const form_data = new URLSearchParams();
            for (const pair of new FormData(form.get(0))) {
                form_data.append(pair[0], pair[1]);
            }

            const resp = await fetch(url, {
                method: 'POST',
                body: form_data
            });

            if (resp.status < 300) {
                const data = await resp.json();
                const input = $("#loginCaptchaText");
                if ("redirect" in data) {
                    document.location = data["redirect"];
                }
                else if ("error" in data) {
                    flash_message(data["error"], "danger");
                    input.get(0).focus();
                }
                else if ("captcha_id" in data) {
                    input.val("");
                    input.attr("aria-required", "true");
                    input.prop("required");
                    input.get(0).focus();
                    $("#loginCaptchaId").val(data["captcha_id"]);
                    $("#loginCaptchaImg").attr("src", data["captcha_url"]);
                    $("#captchaRow").show();
                }
            }
            else {
                flash_message(`HTTP Error ${resp.status}: ${resp.statusText}`, "danger")
            }
        })();
    });

    function flash_message(message, category) {
        // copy from base.html
        $(`<div class="alert alert-${category} alert-dismissible fade show" data-timeout="7500" role="alert">` +
          '<button type="button" class="btn-close btn-sm btn-close-white" data-bs-dismiss="alert" aria-label="Close">' +
          '</button>' +
          message +
          '</div>').appendTo($("#messages").empty());
        // does not auto-close yet...
    }

    /**
     * AutoWebSocket class
     *
     * This class wraps a WebSocket, and makes it automatically reconnect if the
     * connection is lost.
     */
    class AutoWebSocket {
        constructor({
            name,
            url,
            badge=null,
            open=null,
            close=null,
            error=null,
            message=null,
            binary=false,
            reconnect=1000,
        }) {
            this.name = name;
            this.url = url;
            this.badge = badge;
            this.reconnect = reconnect;
            this.open = open;
            this.close = close;
            this.error = error;
            this.message = message;
            this.binary = binary;
            this.ws = null;
        }

        _open() {
            $(this.badge).removeClass("text-bg-success text-bg-danger").addClass("text-bg-warning");
            if (this.open)
                this.open(this.ws);
        }

        _close() {
            $(this.badge).removeClass("text-bg-warning text-bg-success").addClass("text-bg-danger");
            console.log(`${this.name} close`);
            setTimeout(() => this.connect(), this.reconnect);
            if (this.close)
                this.close(this.ws);
        }

        _error() {
            console.log(`${this.name} error`);
            this.ws.close();
            if (this.error)
                this.error(this.ws);
        }

        _message(event) {
            $(this.badge).removeClass("text-bg-danger text-bg-warning").addClass("text-bg-success");
            if (this.message)
                this.message(event);
        }

        connect() {
            var ws = this.ws = new WebSocket(this.url);
            if (this.binary)
                ws.binaryType = "arraybuffer";
            ws.addEventListener("open", this._open.bind(this));
            ws.addEventListener("close", this._close.bind(this));
            ws.addEventListener("error", this._error.bind(this));
            ws.addEventListener("message", this._message.bind(this));
        }
    }

    /**
     * Auto web sockets
     */
    sockets = {};

    sockets.mqtt = new AutoWebSocket({
        name: "mqtt socket",
        url: `ws://${location.host}/ws/mqtt`,
        badge: "#badge-mqtt",

        message: function (ev) {
            const data = JSON.parse(ev.data);
            if (data.commandType == 1001) {
                // Returns Print Details
                $("#print-name").text(data.name);
                $("#time-elapsed").text(getTime(data.totalTime));
                $("#time-remain").text(getTime(data.time));
                const progress = getPercentage(data.progress);
                $("#progressbar").attr("aria-valuenow", progress);
                $("#progressbar").attr("style", `width: ${progress}%`);
                $("#progress").text(`${progress}%`);
            } else if (data.commandType == 1003) {
                // Returns Nozzle Temp
                const current = getTemp(data.currentTemp);
                const target = getTemp(data.targetTemp);
                $("#nozzle-temp").text(`${current}°C`);
                $("#set-nozzle-temp").attr("value", `${target}°C`);
            } else if (data.commandType == 1004) {
                // Returns Bed Temp
                const current = getTemp(data.currentTemp);
                const target = getTemp(data.targetTemp);
                $("#bed-temp").text(`${current}°C`);
                $("#set-bed-temp").attr("value", `${target}°C`);
            } else if (data.commandType == 1006) {
                // Returns Print Speed
                const X = getSpeedFactor(data.value);
                $("#print-speed").text(`${data.value}mm/s ${X}`);
            } else if (data.commandType == 1052) {
                // Returns Layer Info
                const layer = `${data.real_print_layer} / ${data.total_layer}`;
                $("#print-layer").text(layer);
            } else {
                console.log("Unhandled mqtt message:", data);
            }
        },

        close: function () {
            $("#print-name").text("");
            $("#time-elapsed").text("00:00:00");
            $("#time-remain").text("00:00:00");
            $("#progressbar").attr("aria-valuenow", 0);
            $("#progressbar").attr("style", "width: 0%");
            $("#progress").text("0%");
            $("#nozzle-temp").text("0°C");
            $("#set-nozzle-temp").attr("value", "0°C");
            $("#bed-temp").text("$0°C");
            $("#set-bed-temp").attr("value", "0°C");
            $("#print-speed").text("0mm/s");
            $("#print-layer").text("0 / 0");
        },
    });

    /**
     * Initializing a new instance of JMuxer for video playback
     */
    sockets.video = new AutoWebSocket({
        name: "Video socket",
        url: `ws://${location.host}/ws/video`,
        badge: "#badge-pppp",
        binary: true,

        open: function () {
            this.jmuxer = new JMuxer({
                node: "player",
                mode: "video",
                flushingTime: 0,
                fps: 15,
                // debug: true,
                onReady: function (data) {
                    console.log(data);
                },
                onError: function (data) {
                    console.log(data);
                },
            });
        },

        message: function (event) {
            this.jmuxer.feed({
                video: new Uint8Array(event.data),
            });
        },

        close: function () {
            if (!this.jmuxer)
                return;

            this.jmuxer.destroy();

            /* Clear video source (to show loading animation) */
            $("#player").attr("src", "");
        },
    });

    sockets.ctrl = new AutoWebSocket({
        name: "Control socket",
        url: `ws://${location.host}/ws/ctrl`,
        badge: "#badge-ctrl",
    });

    /* Only connect websockets if #player element exists in DOM (i.e., if we
     * have a configuration). Otherwise we are constantly trying to make
     * connections that will never succeed. */
    if ($("#player").length) {
        sockets.mqtt.connect();
        sockets.video.connect();
        sockets.ctrl.connect();
    }

    /**
     * On click of element with id "light-on", sends JSON data to wsctrl to turn light on
     */
    $("#light-on").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ light: true }));
        return false;
    });

    /**
     * On click of element with id "light-off", sends JSON data to wsctrl to turn light off
     */
    $("#light-off").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ light: false }));
        return false;
    });

    /**
     * On click of element with id "quality-low", sends JSON data to wsctrl to set video quality to low
     */
    $("#quality-low").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ quality: 0 }));
        return false;
    });

    /**
     * On click of element with id "quality-high", sends JSON data to wsctrl to set video quality to high
     */
    $("#quality-high").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ quality: 1 }));
        return false;
    });

});
