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
     * Convert bytes to a human readable string.
     * @param {number} bytes
     * @returns {string}
     */
    function formatBytes(bytes) {
        if (!bytes) {
            return "0 B";
        }
        const units = ["B", "KB", "MB", "GB", "TB"];
        let size = bytes;
        let unit = 0;
        while (size >= 1024 && unit < units.length - 1) {
            size /= 1024;
            unit++;
        }
        const precision = size >= 10 || unit === 0 ? 0 : 1;
        return `${size.toFixed(precision)} ${units[unit]}`;
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
     * Highlight active video profile button.
     * @param {string} profileId
     */
    function setVideoProfileActive(profileId) {
        if (!profileId) {
            return;
        }
        const profileKey = String(profileId).toLowerCase();
        const buttons = $(".video-profile-btn");
        if (!buttons.length) {
            return;
        }
        buttons.each(function () {
            const btn = $(this);
            const isActive = btn.data("video-profile") === profileKey;
            btn.toggleClass("active", isActive);
            btn.attr("aria-pressed", isActive ? "true" : "false");
        });
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
            opened=null,
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
            this.opened = opened;
            this.close = close;
            this.error = error;
            this.message = message;
            this.binary = binary;
            this.ws = null;
            this.is_open = false;
            this.autoReconnect = reconnect !== false;
        }

        _open() {
            $(this.badge).removeClass("text-bg-success text-bg-danger").addClass("text-bg-warning");
            if (this.open)
                this.open(this.ws);
        }

        _close() {
            $(this.badge).removeClass("text-bg-warning text-bg-success").addClass("text-bg-danger");
            console.log(`${this.name} close`);
            this.is_open = false;
            if (this.autoReconnect) {
                setTimeout(() => this.connect(), this.reconnect);
            }
            if (this.close)
                this.close(this.ws);
        }

        _error() {
            console.log(`${this.name} error`);
            this.ws.close();
            this.is_open = false;
            if (this.error)
                this.error(this.ws);
        }

        _message(event) {
            if (!this.is_open) {
                $(this.badge).removeClass("text-bg-danger text-bg-warning").addClass("text-bg-success");
                this.is_open = true;
                if (this.opened)
                    this.opened(event);
            }
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

    const uploadBar = $("#upload-progressbar");
    const uploadLabel = $("#upload-progress");
    const uploadMeta = $("#upload-progress-meta");
    let uploadName = "";
    let uploadSize = 0;

    function setUploadProgress(percent) {
        if (!uploadBar.length) {
            return;
        }
        const pct = Math.max(0, Math.min(100, percent));
        uploadBar.attr("aria-valuenow", pct);
        uploadBar.attr("style", `width: ${pct}%`);
        uploadLabel.text(`${pct}%`);
    }

    function resetUploadProgress(message) {
        if (!uploadBar.length) {
            return;
        }
        uploadBar.removeClass("bg-danger");
        setUploadProgress(0);
        uploadMeta.text(message || "Idle");
        uploadName = "";
        uploadSize = 0;
    }

    /**
     * Auto web sockets
     */
    sockets = {};

    sockets.mqtt = new AutoWebSocket({
        name: "mqtt socket",
        url: `${location.protocol.replace("http","ws")}//${location.host}/ws/mqtt`,
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
        url: `${location.protocol.replace("http","ws")}//${location.host}/ws/video`,
        badge: "#badge-video",
        binary: true,
        reconnect: 2000,

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
            $("#video-resolution").text("Current: -");

            $(this.badge).removeClass("text-bg-warning text-bg-success").addClass("text-bg-danger");
        },
    });

    const videoPlayer = document.getElementById("player");
    const updateVideoResolution = () => {
        if (!videoPlayer) {
            return;
        }
        const width = videoPlayer.videoWidth;
        const height = videoPlayer.videoHeight;
        if (width && height) {
            $("#video-resolution").text(`Current: ${width}x${height}`);
        }
    };
    if (videoPlayer) {
        videoPlayer.addEventListener("loadedmetadata", updateVideoResolution);
        videoPlayer.addEventListener("loadeddata", updateVideoResolution);
    }

    sockets.ctrl = new AutoWebSocket({
        name: "Control socket",
        url: `${location.protocol.replace("http","ws")}//${location.host}/ws/ctrl`,
        badge: "#badge-ctrl",
        message: function (event) {
            let data = null;
            try {
                data = JSON.parse(event.data);
            } catch (err) {
                return;
            }
            if (data.video_profile) {
                setVideoProfileActive(data.video_profile);
            }
        },
    });

    sockets.pppp_state = new AutoWebSocket({
        name: "PPPP socket",
        url: `${location.protocol.replace("http","ws")}//${location.host}/ws/pppp-state`,
        badge: "#badge-pppp",
        reconnect: 5000,

        message: function(event) {
            const data = JSON.parse(event.data);
            if (data.status === "connected") {
                $(this.badge).removeClass("text-bg-danger text-bg-warning").addClass("text-bg-success");
            } else if (data.status === "disconnected") {
                $(this.badge).removeClass("text-bg-success text-bg-warning").addClass("text-bg-danger");
                if (this.ws) {
                    this.ws.close();
                    this.ws = null;
                }
            }
        },
    });

    sockets.upload = new AutoWebSocket({
        name: "Upload socket",
        url: `${location.protocol.replace("http","ws")}//${location.host}/ws/upload`,
        reconnect: 2000,
        message: function (event) {
            let data = null;
            try {
                data = JSON.parse(event.data);
            } catch (err) {
                return;
            }
            if (!data) {
                return;
            }
            if (data.name) {
                uploadName = data.name;
            }
            if (typeof data.size === "number") {
                uploadSize = data.size;
            }
            if (data.status === "start") {
                uploadBar.removeClass("bg-danger");
                setUploadProgress(0);
                const sizeText = uploadSize ? ` (${formatBytes(uploadSize)})` : "";
                uploadMeta.text(uploadName ? `Starting upload: ${uploadName}${sizeText}` : "Starting upload");
            } else if (data.status === "progress") {
                const total = data.size || uploadSize;
                const sent = data.sent || 0;
                const percent = total ? Math.round((sent / total) * 100) : 0;
                setUploadProgress(percent);
                const metaName = uploadName ? `Uploading ${uploadName}` : "Uploading";
                const metaSize = total ? ` (${formatBytes(sent)} / ${formatBytes(total)})` : "";
                uploadMeta.text(`${metaName}${metaSize}`);
            } else if (data.status === "done") {
                uploadBar.removeClass("bg-danger");
                setUploadProgress(100);
                const total = data.size || uploadSize;
                const sizeText = total ? ` (${formatBytes(total)})` : "";
                uploadMeta.text(uploadName ? `Upload complete: ${uploadName}${sizeText}` : "Upload complete");
            } else if (data.status === "error") {
                uploadBar.addClass("bg-danger");
                setUploadProgress(0);
                const errorText = data.error ? `: ${data.error}` : "";
                uploadMeta.text(`Upload failed${errorText}`);
            }
        },
        close: function () {
            resetUploadProgress("Idle");
        },
    });

    if ($("#badge-mqtt").length) {
        sockets.mqtt.connect();
    }
    if ($("#badge-ctrl").length) {
        sockets.ctrl.connect();
    }
    if ($("#badge-pppp").length) {
        sockets.pppp_state.connect();
    }
    if ($("#upload-progressbar").length) {
        sockets.upload.connect();
    }

    sockets.video.autoReconnect = false;

    let videoEnabled = false;

    $("#video-toggle").on("click", function() {
        videoEnabled = !videoEnabled;
        if (videoEnabled) {
            $("#vplayer").show();
            $(this).html('<i class="bi bi-camera-video-off"></i> Disable Video');
            sockets.ctrl.ws.send(JSON.stringify({ video_enabled: true }));
            sockets.video.autoReconnect = true;
            if (!sockets.video.ws) {
                sockets.video.connect();
            }
        } else {
            $("#vplayer").hide();
            $(this).html('<i class="bi bi-camera-video"></i> Enable Video');
            sockets.ctrl.ws.send(JSON.stringify({ video_enabled: false }));
            sockets.video.autoReconnect = false;
            if (sockets.video.ws) {
                sockets.video.ws.close();
                sockets.video.ws = null;
            }
            $("#video-resolution").text("Current: -");
        }
    });

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
     * On click of video profile buttons, sends JSON data to wsctrl to set video profile
     */
    $(".video-profile-btn").on("click", function () {
        const profile = $(this).data("video-profile");
        setVideoProfileActive(profile);
        if (sockets.ctrl.ws) {
            sockets.ctrl.ws.send(JSON.stringify({ video_profile: profile }));
        }
        return false;
    });

    $("#upload-rate").on("change", function () {
        const rate = $(this).val();
        const form_data = new URLSearchParams();
        form_data.append("upload_rate_mbps", rate);

        (async () => {
            const resp = await fetch("/api/ankerctl/config/upload-rate", {
                method: "POST",
                body: form_data,
            });
            if (resp.ok) {
                flash_message(`Upload rate set to ${rate} Mbps`, "success");
            } else {
                const data = await resp.json().catch(() => ({}));
                const msg = data.error ? data.error : `HTTP ${resp.status}`;
                flash_message(`Failed to update upload rate: ${msg}`, "danger");
            }
        })();
    });

});
