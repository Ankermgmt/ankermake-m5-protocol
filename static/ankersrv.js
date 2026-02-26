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
        $("[data-clipboard-src]").each(function (i, elm) {
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
        return Math.round(progress);
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

    function flash_message(message, category = "info", timeout = 7500) {
        const messages = $("#messages");
        if (!messages.length) {
            console.log(`[${category}] ${message}`);
            return;
        }
        const alert = $("<div>");
        alert.addClass(`alert alert-${category} alert-dismissible fade show`);
        alert.attr("data-timeout", timeout);
        alert.attr("role", "alert");

        const closeBtn = $("<button>");
        closeBtn.attr("type", "button");
        closeBtn.addClass("btn-close btn-sm btn-close-white");
        closeBtn.attr("data-bs-dismiss", "alert");
        closeBtn.attr("aria-label", "Close");

        alert.append(closeBtn);
        alert.append(document.createTextNode(message));
        messages.append(alert);

        const bsalert = new bootstrap.Alert(alert[0]);
        setTimeout(() => {
            bsalert.close();
        }, timeout);
    }

    /**
     * Escape a string for safe insertion into HTML to prevent XSS.
     * @param {string} str
     * @returns {string} HTML-escaped string
     */
    function escapeHtml(str) {
        const node = document.createTextNode(String(str));
        const div = document.createElement("div");
        div.appendChild(node);
        return div.innerHTML;
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
            badge = null,
            open = null,
            opened = null,
            close = null,
            error = null,
            message = null,
            binary = false,
            reconnect = 1000,
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
        url: `${location.protocol.replace("http", "ws")}//${location.host}/ws/mqtt`,
        badge: "#badge-mqtt",

        message: function (ev) {
            const data = JSON.parse(ev.data);
            if (data.commandType == 1000) {
                // Printer state machine: value=0 idle, value=1 printing, value=2 paused
                _updatePrintControlButtons(data.value);
                if (typeof _onMqttStateChange === "function") {
                    _onMqttStateChange(data.value);
                }
            } else if (data.commandType == 1001) {
                // ZZ_MQTT_CMD_PRINT_SCHEDULE: time=remaining, totalTime=elapsed
                $("#time-remain").text(getTime(data.time));
                if (data.totalTime !== undefined) {
                    $("#time-elapsed").text(getTime(data.totalTime));
                }
            } else if (data.commandType == 1003) {
                // Returns Nozzle Temp
                const current = getTemp(data.currentTemp);
                const target = getTemp(data.targetTemp);
                $("#nozzle-temp").text(`${current}°C`);
                if (!$("#set-nozzle-temp").is(":focus")) {
                    $("#set-nozzle-temp").val(target);
                }
                pushTempData("nozzle", current, target);
            } else if (data.commandType == 1004) {
                // Returns Bed Temp
                const current = getTemp(data.currentTemp);
                const target = getTemp(data.targetTemp);
                $("#bed-temp").text(`${current}°C`);
                if (!$("#set-bed-temp").is(":focus")) {
                    $("#set-bed-temp").val(target);
                }
                pushTempData("bed", current, target);
            } else if (data.commandType == 1006) {
                // Returns Print Speed
                const X = getSpeedFactor(data.value);
                $("#print-speed").text(`${data.value}mm/s ${X}`);
            } else if (data.commandType == 1007) {
                // auto_leveling: value = current probe point (1 center + 7×7 = 50 points total)
                const point = data.value;
                const total = 50;
                const pct = Math.min(100, Math.round(point / total * 100));
                const statusEl = document.getElementById("bed-level-status");
                if (statusEl) {
                    statusEl.innerHTML =
                        `<div class="alert alert-info py-1 small mb-0">` +
                        `<div class="d-flex justify-content-between mb-1">` +
                        `<span>Auto-Leveling… Punkt ${point} / ${total}</span>` +
                        `<span>${pct}%</span></div>` +
                        `<div class="progress" style="height:6px;">` +
                        `<div class="progress-bar progress-bar-striped progress-bar-animated" ` +
                        `style="width:${pct}%" aria-valuenow="${pct}"></div></div></div>`;
                }
            } else if (data.commandType == 1052) {
                // Returns Layer Info; derive progress from layer counts
                const layer = `${data.real_print_layer} / ${data.total_layer}`;
                $("#print-layer").text(layer);
                if (data.total_layer > 0) {
                    const progress = Math.round((data.real_print_layer / data.total_layer) * 100);
                    $("#progressbar").attr("aria-valuenow", progress);
                    $("#progressbar").attr("style", `width: ${progress}%`);
                    $("#progress").text(`${progress}%`);
                    document.title = progress > 0 && progress < 100
                        ? `\u{1F5A8}\uFE0F ${progress}% | ankerctl`
                        : "ankerctl";
                }
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
            $("#bed-temp").text("0°C");
            $("#set-bed-temp").attr("value", "0°C");
            $("#print-speed").text("0mm/s");
            $("#print-layer").text("0 / 0");
            document.title = "ankerctl";
            _updatePrintControlButtons(PRINT_STATE.IDLE);
        },
    });

    /**
     * Initializing a new instance of JMuxer for video playback
     */
    sockets.video = new AutoWebSocket({
        name: "Video socket",
        url: `${location.protocol.replace("http", "ws")}//${location.host}/ws/video`,
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
        url: `${location.protocol.replace("http", "ws")}//${location.host}/ws/ctrl`,
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
        url: `${location.protocol.replace("http", "ws")}//${location.host}/ws/pppp-state`,
        badge: "#badge-pppp",
        reconnect: 5000,

        message: function (event) {
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
        url: `${location.protocol.replace("http", "ws")}//${location.host}/ws/upload`,
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

    $("#video-toggle").on("click", function () {
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
     * Highlight the active light button.
     * @param {boolean|null} on - true = light on, false = light off, null = unknown
     */
    function setLightActive(on) {
        $("#light-on").toggleClass("active", on === true).attr("aria-pressed", on === true ? "true" : "false");
        $("#light-off").toggleClass("active", on === false).attr("aria-pressed", on === false ? "true" : "false");
    }

    /**
     * On click of element with id "light-on", sends JSON data to wsctrl to turn light on
     */
    $("#light-on").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ light: true }));
        setLightActive(true);
        return false;
    });

    /**
     * On click of element with id "light-off", sends JSON data to wsctrl to turn light off
     */
    $("#light-off").on("click", function () {
        sockets.ctrl.ws.send(JSON.stringify({ light: false }));
        setLightActive(false);
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

    const appriseForm = $("#apprise-form");
    if (appriseForm.length) {
        const appriseFields = {
            enabled: $("#apprise-enabled"),
            serverUrl: $("#apprise-server-url"),
            key: $("#apprise-key"),
            tag: $("#apprise-tag"),
            progressInterval: $("#apprise-progress-interval"),
            snapshotQuality: $("#apprise-snapshot-quality"),
            snapshotFallback: $("#apprise-snapshot-fallback"),
            snapshotLight: $("#apprise-snapshot-light"),
            progressIncludeImage: $("#apprise-progress-image"),
            events: {
                print_started: $("#apprise-event-print-started"),
                print_finished: $("#apprise-event-print-finished"),
                print_failed: $("#apprise-event-print-failed"),
                gcode_uploaded: $("#apprise-event-gcode-uploaded"),
                print_progress: $("#apprise-event-print-progress"),
            },
        };
        const appriseButtons = {
            save: $("#apprise-save"),
            test: $("#apprise-test"),
        };

        const setAppriseBusy = (busy) => {
            appriseButtons.save.prop("disabled", busy);
            appriseButtons.test.prop("disabled", busy);
        };

        const buildAppriseConfig = () => {
            const interval = parseInt(appriseFields.progressInterval.val(), 10);
            const snapshotQuality = appriseFields.snapshotQuality.val().trim().toLowerCase();
            return {
                enabled: appriseFields.enabled.is(":checked"),
                server_url: appriseFields.serverUrl.val().trim(),
                key: appriseFields.key.val().trim(),
                tag: appriseFields.tag.val().trim(),
                events: {
                    print_started: appriseFields.events.print_started.is(":checked"),
                    print_finished: appriseFields.events.print_finished.is(":checked"),
                    print_failed: appriseFields.events.print_failed.is(":checked"),
                    gcode_uploaded: appriseFields.events.gcode_uploaded.is(":checked"),
                    print_progress: appriseFields.events.print_progress.is(":checked"),
                },
                progress: {
                    interval_percent: Number.isNaN(interval) ? 25 : interval,
                    include_image: appriseFields.progressIncludeImage.is(":checked"),
                    snapshot_quality: snapshotQuality || "hd",
                    snapshot_fallback: appriseFields.snapshotFallback.is(":checked"),
                    snapshot_light: appriseFields.snapshotLight.is(":checked"),
                },
            };
        };

        const applyAppriseSettings = (apprise) => {
            const settings = apprise || {};
            const events = settings.events || {};
            const progress = settings.progress || {};
            appriseFields.enabled.prop("checked", Boolean(settings.enabled));
            appriseFields.serverUrl.val(settings.server_url || "");
            appriseFields.key.val(settings.key || "");
            appriseFields.tag.val(settings.tag || "");
            appriseFields.events.print_started.prop("checked", Boolean(events.print_started));
            appriseFields.events.print_finished.prop("checked", Boolean(events.print_finished));
            appriseFields.events.print_failed.prop("checked", Boolean(events.print_failed));
            appriseFields.events.gcode_uploaded.prop("checked", Boolean(events.gcode_uploaded));
            appriseFields.events.print_progress.prop("checked", Boolean(events.print_progress));
            if (progress.interval_percent !== undefined && progress.interval_percent !== null) {
                appriseFields.progressInterval.val(progress.interval_percent);
            } else {
                appriseFields.progressInterval.val("");
            }
            appriseFields.progressIncludeImage.prop("checked", Boolean(progress.include_image));
            appriseFields.snapshotQuality.val(progress.snapshot_quality || "hd");
            appriseFields.snapshotFallback.prop("checked", progress.snapshot_fallback !== false);
            appriseFields.snapshotLight.prop("checked", Boolean(progress.snapshot_light));
        };

        const loadAppriseSettings = async () => {
            setAppriseBusy(true);
            try {
                const resp = await fetch("/api/notifications/settings");
                if (resp.ok) {
                    const data = await resp.json();
                    applyAppriseSettings(data.apprise || {});
                } else {
                    const data = await resp.json().catch(() => ({}));
                    const msg = data.error ? data.error : `HTTP ${resp.status}`;
                    flash_message(`Failed to load notifications: ${msg}`, "danger");
                }
            } catch (err) {
                flash_message(`Failed to load notifications: ${err}`, "danger");
            } finally {
                setAppriseBusy(false);
            }
        };

        appriseButtons.save.on("click", async function () {
            setAppriseBusy(true);
            const payload = { apprise: buildAppriseConfig() };
            try {
                const resp = await fetch("/api/notifications/settings", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                if (resp.ok) {
                    const data = await resp.json().catch(() => ({}));
                    if (data.apprise) {
                        applyAppriseSettings(data.apprise);
                    }
                    flash_message("Notification settings saved", "success");
                } else {
                    const data = await resp.json().catch(() => ({}));
                    const msg = data.error ? data.error : `HTTP ${resp.status}`;
                    flash_message(`Failed to save notifications: ${msg}`, "danger");
                }
            } catch (err) {
                flash_message(`Failed to save notifications: ${err}`, "danger");
            } finally {
                setAppriseBusy(false);
            }
        });

        appriseButtons.test.on("click", async function () {
            setAppriseBusy(true);
            const payload = { apprise: buildAppriseConfig() };
            try {
                const resp = await fetch("/api/notifications/test", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                const data = await resp.json().catch(() => ({}));
                if (resp.ok) {
                    flash_message(data.message || "Test notification sent", "success");
                } else {
                    const msg = data.error ? data.error : `HTTP ${resp.status}`;
                    flash_message(`Test notification failed: ${msg}`, "danger");
                }
            } catch (err) {
                flash_message(`Test notification failed: ${err}`, "danger");
            } finally {
                setAppriseBusy(false);
            }
        });

        loadAppriseSettings();
    }

    (function (selectElement) {
        if (!selectElement.length) return;
        const countryCodes = selectElement.data("countrycodes");
        const currentCountry = selectElement.data("country");
        countryCodes.forEach((item) => {
            const selected = (currentCountry == item.c) ? " selected" : "";
            $(`<option value="${item.c}"${selected}>${item.n}</option>`).appendTo(selectElement);
        });
    })($("#loginCountry"));

    $("#captchaRow").hide();
    $("#loginCaptchaId").val("");

    $("#config-login-form").on("submit", function (e) {
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

    /**
     * Printer Control Logic
     */
    function sendPrinterGCode(gcode) {
        if (!gcode) return;
        console.log("Sending GCode:", gcode);
        fetch("/api/printer/gcode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gcode: gcode })
        }).catch(err => console.error("Failed to send GCode:", err));
    }

    function sendPrintControl(value) {
        console.log("Sending Print Control:", value);
        fetch("/api/printer/control", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ value: value })
        }).catch(err => console.error("Failed to send print control:", err));
    }

    const PRINT_CONTROL = {
        PAUSE: 2,
        RESUME: 3,
        STOP: 4,
    };

    // ct=1000 state values
    const PRINT_STATE = { IDLE: 0, PRINTING: 1, PAUSED: 2, CALIBRATING: 8 };

    let _currentPrintState = PRINT_STATE.IDLE;

    function _updatePrintControlButtons(state) {
        _currentPrintState = state;
        const printing = state === PRINT_STATE.PRINTING;
        const paused = state === PRINT_STATE.PAUSED;
        const active = printing || paused;
        $("#print-pause").toggleClass("d-none", !printing);
        $("#print-resume").toggleClass("d-none", !paused);
        $("#print-stop").toggleClass("d-none", !active);
    }

    const getStepDist = () => $('input[name="step-dist"]:checked').val() || "1";

    $("#move-x-plus").on("click", function () { sendPrinterGCode(`G91\nG0 X${getStepDist()} F3000\nG90`); return false; });
    $("#move-x-minus").on("click", function () { sendPrinterGCode(`G91\nG0 X-${getStepDist()} F3000\nG90`); return false; });
    $("#move-y-plus").on("click", function () { sendPrinterGCode(`G91\nG0 Y${getStepDist()} F3000\nG90`); return false; });
    $("#move-y-minus").on("click", function () { sendPrinterGCode(`G91\nG0 Y-${getStepDist()} F3000\nG90`); return false; });
    $("#move-z-plus").on("click", function () { sendPrinterGCode(`G91\nG0 Z${getStepDist()} F600\nG90`); return false; });
    $("#move-z-minus").on("click", function () { sendPrinterGCode(`G91\nG0 Z-${getStepDist()} F600\nG90`); return false; });

    $("#control-home-xy").on("click", function () { sendPrinterGCode("G28 X Y"); return false; });
    $("#control-home-z").on("click", function () { sendPrinterGCode("G28 Z"); return false; });
    $("#control-home-all").on("click", function () { sendPrinterGCode("G28"); return false; });

    // ------------------------------------------------------------------
    // Bed Level Map — shared rendering utilities
    // (defined at outer scope so they work with or without the debug tab)
    // ------------------------------------------------------------------

    /**
     * Map a deviation value to an RGB colour.
     * Negative values shade from blue (most negative) to white (zero).
     * Positive values shade from white (zero) to red (most positive).
     * The scale is symmetric: the larger absolute extreme defines ±range.
     *
     * @param {number} val   - cell value in mm
     * @param {number} range - symmetric range (Math.max(|min|, |max|))
     * @returns {string} CSS rgb(...) colour string
     */
    function bedLevelValueToColor(val, range) {
        if (range === 0) return "rgb(255,255,255)";
        const norm = Math.max(-1, Math.min(1, val / range)); // clamp to [-1, 1]
        if (norm < 0) {
            // blue → white  (t goes 0→1 as norm goes -1→0)
            const t = 1 + norm;
            const c = Math.round(t * 255);
            return `rgb(${c},${c},255)`;
        } else {
            // white → red  (t goes 0→1 as norm goes 0→1)
            const t = norm;
            const c = Math.round((1 - t) * 255);
            return `rgb(255,${c},${c})`;
        }
    }

    /**
     * Render the bed leveling heatmap into the specified wrapper element.
     * Draws column indices across the top and row indices down the left.
     *
     * @param {number[][]} grid     - 2-D array of mm deviation values
     * @param {number}     min      - global minimum value
     * @param {number}     max      - global maximum value
     * @param {string}     targetId - ID of wrapper element (default: "dbg-bedlevel-map-wrap")
     */
    function bedLevelRenderGrid(grid, min, max, targetId) {
        const wrapId = targetId || "dbg-bedlevel-map-wrap";
        const range = Math.max(Math.abs(min), Math.abs(max));
        const rows = grid.length;
        const cols = rows > 0 ? grid[0].length : 0;

        // Build a table: header row + one row per grid row
        const table = document.createElement("table");
        table.style.cssText = "border-collapse:separate; border-spacing:3px; font-size:0.75em; font-family:monospace;";

        // Column header row
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        // Empty corner cell above the row-label column
        const cornerTh = document.createElement("th");
        cornerTh.style.cssText = "padding:2px 6px; color:#6c757d; text-align:center;";
        headerRow.appendChild(cornerTh);
        for (let c = 0; c < cols; c++) {
            const th = document.createElement("th");
            th.style.cssText = "padding:2px 6px; color:#6c757d; text-align:center;";
            th.textContent = c;
            headerRow.appendChild(th);
        }
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Data rows — rendered bottom-to-top so Row 0 (front of printer) appears
        // at the bottom of the table and Row N-1 (back) at the top, matching
        // the view when standing in front of the printer.
        const tbody = document.createElement("tbody");
        for (let r = rows - 1; r >= 0; r--) {
            const tr = document.createElement("tr");

            // Row label
            const rowTh = document.createElement("th");
            rowTh.style.cssText = "padding:2px 6px; color:#6c757d; text-align:right; white-space:nowrap;";
            rowTh.textContent = r;
            tr.appendChild(rowTh);

            for (let c = 0; c < grid[r].length; c++) {
                const val = grid[r][c];
                const td = document.createElement("td");
                const bg = bedLevelValueToColor(val, range);
                // Choose dark or light text based on perceived luminance of background
                // For a blue-white-red palette the midpoints are light, extremes need contrast.
                const normAbs = range > 0 ? Math.abs(val) / range : 0;
                const textColor = normAbs > 0.65 ? "#ffffff" : "#212529";
                td.style.cssText = [
                    `background:${bg}`,
                    `color:${textColor}`,
                    "padding:5px 8px",
                    "border-radius:3px",
                    "text-align:center",
                    "white-space:nowrap",
                    "cursor:default",
                ].join(";");
                const display = val >= 0 ? `+${val.toFixed(3)}` : val.toFixed(3);
                td.textContent = display;
                td.title = `Row ${r}, Col ${c}: ${display} mm`;
                tr.appendChild(td);
            }
            tbody.appendChild(tr);
        }
        table.appendChild(tbody);

        const wrap = document.getElementById(wrapId);
        if (wrap) {
            wrap.innerHTML = "";
            wrap.appendChild(table);
        }
    }

    // ------------------------------------------------------------------
    // Bed Level Map — Setup > Tools card
    // ------------------------------------------------------------------

    /**
     * localStorage key and cap for bed level snapshots.
     */
    const BED_SNAP_KEY = "ankerctl_bed_snapshots";
    const BED_SNAP_MAX = 10;

    /**
     * Currently loaded bed level data (set by bedLevelRead()).
     * Shape: {grid, min, max, rows, cols} or null.
     */
    let _currentBedData = null;

    /** Load snapshots array from localStorage. */
    function bedSnapLoad() {
        try {
            return JSON.parse(localStorage.getItem(BED_SNAP_KEY) || "[]");
        } catch (_) {
            return [];
        }
    }

    /** Persist snapshots array to localStorage. */
    function bedSnapSave(snaps) {
        localStorage.setItem(BED_SNAP_KEY, JSON.stringify(snaps));
    }

    /**
     * Add a new snapshot from bed data. Enforces BED_SNAP_MAX limit.
     * @param {{grid, min, max, rows, cols}} data
     */
    function bedSnapAdd(data) {
        if (!data) return;
        const snaps = bedSnapLoad();
        const now = new Date();
        const pad = (n) => String(n).padStart(2, "0");
        const label =
            `${now.getFullYear()}/${pad(now.getMonth() + 1)}/${pad(now.getDate())} ` +
            `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        snaps.push({ id: "snap_" + Date.now(), label, data });
        while (snaps.length > BED_SNAP_MAX) {
            snaps.shift();
        }
        bedSnapSave(snaps);
        bedSnapRefreshUI();
        flash_message("Snapshot saved.", "success", 3000);
    }

    /**
     * Delete a snapshot by id and refresh UI.
     * @param {string} id
     */
    function bedSnapDelete(id) {
        const snaps = bedSnapLoad().filter(s => s.id !== id);
        bedSnapSave(snaps);
        bedSnapRefreshUI();
    }

    /**
     * Refresh both compare selects and the saved-snapshots list.
     */
    function bedSnapRefreshUI() {
        const snaps = bedSnapLoad();

        // Rebuild Snapshot A select
        const selA = document.getElementById("bed-snap-a-select");
        if (selA) {
            const prevA = selA.value;
            selA.innerHTML = "";
            if (snaps.length === 0) {
                selA.innerHTML = '<option value="" disabled selected>No snapshots saved yet</option>';
            } else {
                snaps.forEach(s => {
                    const opt = document.createElement("option");
                    opt.value = s.id;
                    opt.textContent = escapeHtml(s.label);
                    if (s.id === prevA) opt.selected = true;
                    selA.appendChild(opt);
                });
            }
        }

        // Rebuild Snapshot B select (always has "live" option first)
        const selB = document.getElementById("bed-snap-b-select");
        if (selB) {
            const prevB = selB.value;
            selB.innerHTML = '<option value="live">Read live from printer</option>';
            snaps.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s.id;
                opt.textContent = escapeHtml(s.label);
                if (s.id === prevB) opt.selected = true;
                selB.appendChild(opt);
            });
        }

        // Rebuild saved-snapshots list
        const listEl = document.getElementById("bed-snap-list");
        if (listEl) {
            if (snaps.length === 0) {
                listEl.innerHTML = '<span class="text-muted small">No snapshots saved yet.</span>';
            } else {
                listEl.innerHTML = "";
                snaps.forEach(s => {
                    const row = document.createElement("div");
                    row.className = "d-flex justify-content-between align-items-center border-bottom py-1";
                    row.innerHTML =
                        `<span class="small">${escapeHtml(s.label)}</span>` +
                        `<button class="btn btn-sm btn-outline-danger bed-snap-delete-btn" ` +
                        `data-snap-id="${escapeHtml(s.id)}">` +
                        `<i class="bi bi-trash"></i></button>`;
                    listEl.appendChild(row);
                });
            }
        }
    }

    /**
     * Compute cell-wise diff grid: B minus A.
     * Returns null if grids have mismatched dimensions.
     * @param {number[][]} gridA
     * @param {number[][]} gridB
     * @returns {number[][]|null}
     */
    function bedLevelDiffGrid(gridA, gridB) {
        if (!gridA || !gridB || gridA.length !== gridB.length) return null;
        const result = [];
        for (let r = 0; r < gridA.length; r++) {
            if (gridA[r].length !== gridB[r].length) return null;
            result.push(gridA[r].map((v, c) => gridB[r][c] - v));
        }
        return result;
    }

    /**
     * Fetch bed level from printer and display in the Setup > Tools card.
     * Sets _currentBedData on success and enables the Save Snapshot button.
     */
    async function bedLevelRead() {
        const statusEl = document.getElementById("bed-level-status");
        const gridEl = document.getElementById("bed-level-grid");
        const statsEl = document.getElementById("bed-level-stats");
        const saveBtn = document.getElementById("bed-level-save-btn");
        const readBtn = document.getElementById("bed-level-read-btn");

        if (!statusEl) return;

        statusEl.innerHTML =
            '<div class="alert alert-info py-2 small mb-0">' +
            '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
            'Sending M420 V \u2014 waiting for printer response (up to 15 s)...</div>';
        if (gridEl) gridEl.style.display = "none";
        if (readBtn) readBtn.prop ? $(readBtn).prop("disabled", true) : (readBtn.disabled = true);

        try {
            const resp = await fetch("/api/printer/bed-leveling");
            const data = await resp.json();

            if (!resp.ok) {
                statusEl.innerHTML =
                    `<div class="alert alert-danger py-2 small mb-0">` +
                    `Error ${resp.status}: ${escapeHtml(data.error || "Unknown error")}</div>`;
                return;
            }

            _currentBedData = data;

            if (statsEl) {
                statsEl.innerHTML =
                    `<span><strong>Min:</strong> ${data.min.toFixed(3)} mm</span>` +
                    `<span><strong>Max:</strong> +${data.max.toFixed(3)} mm</span>` +
                    `<span><strong>Range:</strong> ${(data.max - data.min).toFixed(3)} mm</span>` +
                    `<span class="text-muted">(${data.rows}&times;${data.cols} grid)</span>`;
            }

            bedLevelRenderGrid(data.grid, data.min, data.max, "bed-level-map-wrap");

            statusEl.innerHTML = "";
            if (gridEl) gridEl.style.display = "block";
            if (saveBtn) saveBtn.disabled = false;
        } catch (err) {
            statusEl.innerHTML =
                `<div class="alert alert-danger py-2 small mb-0">` +
                `Request failed: ${escapeHtml(String(err))}</div>`;
        } finally {
            if (readBtn) readBtn.disabled = false;
        }
    }

    /**
     * Compare two bed level grids and render a 3-panel diff view.
     */
    async function bedLevelCompare() {
        const statusEl = document.getElementById("bed-compare-status");
        const resultEl = document.getElementById("bed-compare-result");
        const selA = document.getElementById("bed-snap-a-select");
        const selB = document.getElementById("bed-snap-b-select");
        const diffStatsEl = document.getElementById("bed-compare-diff-stats");

        if (!statusEl) return;
        statusEl.innerHTML = "";
        if (resultEl) resultEl.style.display = "none";

        const snapIdA = selA ? selA.value : "";
        if (!snapIdA) {
            statusEl.innerHTML = '<div class="alert alert-warning py-2 small mb-0">Please select Snapshot A first.</div>';
            return;
        }

        const snaps = bedSnapLoad();
        const snapA = snaps.find(s => s.id === snapIdA);
        if (!snapA) {
            statusEl.innerHTML = '<div class="alert alert-danger py-2 small mb-0">Snapshot A not found.</div>';
            return;
        }

        const snapBId = selB ? selB.value : "live";
        let dataB = null;

        if (snapBId === "live") {
            statusEl.innerHTML =
                '<div class="alert alert-info py-2 small mb-0">' +
                '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
                'Reading live data from printer...</div>';
            try {
                const resp = await fetch("/api/printer/bed-leveling");
                const parsed = await resp.json();
                if (!resp.ok) {
                    statusEl.innerHTML =
                        `<div class="alert alert-danger py-2 small mb-0">` +
                        `Printer error: ${escapeHtml(parsed.error || "Unknown error")}</div>`;
                    return;
                }
                dataB = parsed;
            } catch (err) {
                statusEl.innerHTML =
                    `<div class="alert alert-danger py-2 small mb-0">` +
                    `Request failed: ${escapeHtml(String(err))}</div>`;
                return;
            }
        } else {
            const snapB = snaps.find(s => s.id === snapBId);
            if (!snapB) {
                statusEl.innerHTML = '<div class="alert alert-danger py-2 small mb-0">Snapshot B not found.</div>';
                return;
            }
            dataB = snapB.data;
        }

        const dataA = snapA.data;
        const diffGrid = bedLevelDiffGrid(dataA.grid, dataB.grid);

        if (!diffGrid) {
            statusEl.innerHTML =
                '<div class="alert alert-warning py-2 small mb-0">' +
                'Cannot compare: grids have different dimensions.</div>';
            return;
        }

        // Render grids
        bedLevelRenderGrid(dataA.grid, dataA.min, dataA.max, "bed-compare-a-wrap");
        bedLevelRenderGrid(dataB.grid, dataB.min, dataB.max, "bed-compare-b-wrap");

        const diffFlat = diffGrid.flat();
        const diffMin = Math.min(...diffFlat);
        const diffMax = Math.max(...diffFlat);
        bedLevelRenderGrid(diffGrid, diffMin, diffMax, "bed-compare-diff-wrap");

        // Diff stats
        if (diffStatsEl) {
            const avg = diffFlat.reduce((a, b) => a + b, 0) / diffFlat.length;
            const maxImprovement = -diffMin; // most negative diff = biggest improvement (lower deviation)
            const maxRegression = diffMax;   // most positive diff = biggest regression
            diffStatsEl.innerHTML =
                `<div><strong>Avg shift:</strong> ${avg >= 0 ? "+" : ""}${avg.toFixed(3)} mm</div>` +
                `<div><strong>Max improvement:</strong> ${maxImprovement.toFixed(3)} mm</div>` +
                `<div><strong>Max regression:</strong> +${maxRegression.toFixed(3)} mm</div>`;
        }

        statusEl.innerHTML = "";
        if (resultEl) resultEl.style.display = "block";
    }

    async function bedLevelLoadLast() {
        const statusEl = document.getElementById("bed-level-status");
        const gridEl = document.getElementById("bed-level-grid");
        const statsEl = document.getElementById("bed-level-stats");
        const saveBtn = document.getElementById("bed-level-save-btn");

        if (!statusEl) return;
        statusEl.innerHTML =
            '<div class="alert alert-info py-2 small mb-0">' +
            '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
            'Loading last saved map\u2026</div>';
        if (gridEl) gridEl.style.display = "none";

        try {
            const resp = await fetch("/api/printer/bed-leveling/last");
            const data = await resp.json();

            if (!resp.ok) {
                statusEl.innerHTML =
                    `<div class="alert alert-warning py-2 small mb-0">` +
                    `${escapeHtml(data.error || "No saved map found")}</div>`;
                return;
            }

            _currentBedData = data;

            if (statsEl) {
                const ts = data.saved_at
                    ? ` &mdash; saved ${data.saved_at.replace(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/, "$1-$2-$3 $4:$5:$6")}`
                    : "";
                statsEl.innerHTML =
                    `<span><strong>Min:</strong> ${data.min.toFixed(3)} mm</span>` +
                    `<span><strong>Max:</strong> +${data.max.toFixed(3)} mm</span>` +
                    `<span><strong>Range:</strong> ${(data.max - data.min).toFixed(3)} mm</span>` +
                    `<span class="text-muted">(${data.rows}&times;${data.cols} grid${ts})</span>`;
            }

            bedLevelRenderGrid(data.grid, data.min, data.max, "bed-level-map-wrap");
            statusEl.innerHTML = "";
            if (gridEl) gridEl.style.display = "block";
            if (saveBtn) saveBtn.disabled = false;
        } catch (err) {
            statusEl.innerHTML =
                `<div class="alert alert-danger py-2 small mb-0">` +
                `Request failed: ${escapeHtml(String(err))}</div>`;
        }
    }

    // Wire up Setup > Tools bed level buttons
    $("#bed-level-read-btn").on("click", function () { bedLevelRead(); });
    $("#bed-level-load-last-btn").on("click", function () { bedLevelLoadLast(); });
    $("#bed-level-save-btn").on("click", function () {
        bedSnapAdd(_currentBedData);
    });
    $("#bed-compare-btn").on("click", function () { bedLevelCompare(); });

    // Delegate delete buttons in snapshot list
    $(document).on("click", ".bed-snap-delete-btn", function () {
        const id = $(this).data("snap-id");
        if (id) bedSnapDelete(id);
    });

    // Initialize snapshot UI on page load
    bedSnapRefreshUI();

    /**
     * Auto-Leveling — state machine for polling after bed level command.
     * We listen on the MQTT WebSocket (commandType 1000) to detect completion.
     *
     * State:
     *   _waitingForBedLevel: false = idle, "heating" = saw active, "idle" = done
     */
    let _waitingForBedLevel = false;
    let _bedLevelPollTimeout = null;
    const BED_LEVEL_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes

    /**
     * Called by the MQTT message handler when commandType 1000 arrives.
     * value=0 → idle/finished, value=1 → active.
     */
    function _onMqttStateChange(value) {
        if (!_waitingForBedLevel) return;

        if (value === 1) {
            // Printer became active (heating / probing)
            _waitingForBedLevel = "active";
        } else if (value === 0 && _waitingForBedLevel === "active") {
            // Printer returned to idle after being active → leveling done
            _cancelBedLevelWait();
            const statusEl = document.getElementById("bed-level-status");
            if (statusEl) {
                statusEl.innerHTML =
                    '<div class="alert alert-success py-2 small mb-0">' +
                    '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
                    'Bed leveling complete — reading grid...</div>';
            }
            bedLevelRead();
        }
    }

    function _cancelBedLevelWait() {
        _waitingForBedLevel = false;
        if (_bedLevelPollTimeout) {
            clearTimeout(_bedLevelPollTimeout);
            _bedLevelPollTimeout = null;
        }
    }

    /**
     * Auto-Leveling
     */
    $("#auto-level-btn").on("click", async function () {
        if (!confirm("Start Auto-Leveling? Make sure the print bed is clear.")) return;
        const btn = $(this);
        btn.prop("disabled", true).html('<i class="bi bi-hourglass-split"></i> Leveling...');
        try {
            const resp = await fetch("/api/printer/autolevel", { method: "POST" });
            if (resp.ok) {
                flash_message("Auto-Leveling started — the printer will now probe the bed.", "success");

                // Start waiting for bed leveling to complete via MQTT state changes
                _waitingForBedLevel = true;
                const statusEl = document.getElementById("bed-level-status");
                const gridEl = document.getElementById("bed-level-grid");
                if (statusEl) {
                    statusEl.innerHTML =
                        '<div class="alert alert-info py-2 small mb-0">' +
                        '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
                        'Waiting for bed leveling to complete\u2026</div>';
                }
                if (gridEl) gridEl.style.display = "none";

                // Timeout after 10 minutes
                _bedLevelPollTimeout = setTimeout(function () {
                    if (_waitingForBedLevel) {
                        _cancelBedLevelWait();
                        if (statusEl) {
                            statusEl.innerHTML =
                                '<div class="alert alert-warning py-2 small mb-0">' +
                                'Bed leveling timed out (10 min). Click "Read" to check manually.</div>';
                        }
                    }
                }, BED_LEVEL_TIMEOUT_MS);
            } else {
                const data = await resp.json().catch(() => ({}));
                const msg = data.error ? data.error : `HTTP ${resp.status}`;
                flash_message(`Auto-Leveling failed: ${msg}`, "danger");
            }
        } catch (err) {
            flash_message(`Auto-Leveling failed: ${err}`, "danger");
        } finally {
            btn.prop("disabled", false).html('<i class="bi bi-rulers"></i> Start Auto-Level');
        }
    });

    /**
     * Temperature Control Logic
     */
    $("#set-nozzle-temp").on("change", function () {
        const temp = $(this).val();
        if (temp !== "") {
            sendPrinterGCode(`M104 S${temp}`);
        }
    });

    $("#set-bed-temp").on("change", function () {
        const temp = $(this).val();
        if (temp !== "") {
            sendPrinterGCode(`M140 S${temp}`);
        }
    });

    $(".preheat-preset").on("click", function () {
        const nozzle = $(this).attr("data-nozzle");
        const bed = $(this).attr("data-bed");
        sendPrinterGCode(`M104 S${nozzle}\nM140 S${bed}`);
        return false;
    });

    /**
     * Snapshot Button
     */
    $("#snapshot-btn").on("click", function () {
        const btn = $(this);
        btn.prop("disabled", true);
        fetch("/api/snapshot")
            .then(resp => {
                if (!resp.ok) throw new Error("Snapshot failed");
                return resp.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `ankerctl_snapshot_${Date.now()}.jpg`;
                a.click();
                URL.revokeObjectURL(url);
            })
            .catch(err => alert("Snapshot failed: " + err.message))
            .finally(() => btn.prop("disabled", false));
    });

    /**
     * GCode Console
     */
    function gcodeLog(msg) {
        const log = $("#gcode-log");
        const ts = new Date().toLocaleTimeString();
        log.append(`[${ts}] ${msg}\n`);
        log.scrollTop(log[0].scrollHeight);
    }

    function sendGCodeWithLog(gcode) {
        if (!gcode || !gcode.trim()) return;
        gcodeLog(`» ${gcode.trim().replace(/\n/g, " | ")}`);
        fetch("/api/printer/gcode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gcode: gcode })
        })
            .then(resp => resp.json().then(data => ({ ok: resp.ok, status: resp.status, data })))
            .then(({ ok, status, data }) => {
                if (ok) {
                    gcodeLog("✓ Sent successfully");
                } else {
                    gcodeLog(`✗ Error ${status}: ${data.error || "Unknown error"}`);
                }
            })
            .catch(err => gcodeLog(`✗ Failed: ${err.message}`));
    }

    // File upload
    $("#gcode-file-send").on("click", function () {
        const fileInput = document.getElementById("gcode-file");
        if (!fileInput.files.length) {
            gcodeLog("✗ No file selected");
            return;
        }
        const file = fileInput.files[0];
        const reader = new FileReader();
        reader.onload = function (e) {
            const content = e.target.result;
            const lines = content.split("\n").filter(l => l.trim() && !l.trim().startsWith(";"));
            gcodeLog(`Sending ${lines.length} commands from ${file.name}...`);
            sendGCodeWithLog(content);
        };
        reader.readAsText(file);
    });

    // Custom text input
    $("#gcode-text-send").on("click", function () {
        const input = $("#gcode-input");
        sendGCodeWithLog(input.val());
        input.val("");
    });

    // Enter key in textarea sends
    $("#gcode-input").on("keydown", function (e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            $("#gcode-text-send").click();
        }
    });

    $("#print-pause").on("click", function () {
        sendPrintControl(PRINT_CONTROL.PAUSE);
        _updatePrintControlButtons(PRINT_STATE.PAUSED);
        return false;
    });
    $("#print-resume").on("click", function () {
        sendPrintControl(PRINT_CONTROL.RESUME);
        _updatePrintControlButtons(PRINT_STATE.PRINTING);
        return false;
    });
    $("#print-stop").on("click", function () {
        if (confirm("Are you sure you want to stop the print? This will also turn off heaters.")) {
            sendPrintControl(PRINT_CONTROL.STOP);
            sendPrinterGCode("M104 S0\nM140 S0\nM106 S0");
            _updatePrintControlButtons(PRINT_STATE.IDLE);
        }
        return false;
    });

    /**
     * Temperature Graph — client‑side ring buffer + Chart.js
     */
    const TEMP_BUFFER_MAX = 3600;  // 1h at 1 sample/sec
    let tempWindowSec = 300;       // default 5m
    const tempData = [];           // [{t: Date, nC, nT, bC, bT}]
    let lastTempPush = 0;
    let _pendingNozzle = { c: null, t: null };
    let _pendingBed = { c: null, t: null };

    function pushTempData(type, current, target) {
        if (type === "nozzle") { _pendingNozzle = { c: current, t: target }; }
        else if (type === "bed") { _pendingBed = { c: current, t: target }; }

        const now = Date.now();
        if (now - lastTempPush < 1000) return; // 1s throttle
        lastTempPush = now;

        if (_pendingNozzle.c === null && _pendingBed.c === null) return;

        tempData.push({
            t: new Date(),
            nC: _pendingNozzle.c, nT: _pendingNozzle.t,
            bC: _pendingBed.c, bT: _pendingBed.t,
        });
        if (tempData.length > TEMP_BUFFER_MAX) tempData.shift();
    }

    // Initialize Chart.js (only if available)
    let tempChart = null;
    const chartCanvas = document.getElementById("temp-chart");

    if (typeof Chart !== "undefined" && chartCanvas) {
        const ctx = chartCanvas.getContext("2d");
        tempChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Nozzle",
                        borderColor: "#ff6384",
                        backgroundColor: "rgba(255,99,132,0.1)",
                        data: [], fill: false, tension: 0.3, pointRadius: 0, borderWidth: 2,
                    },
                    {
                        label: "Nozzle Target",
                        borderColor: "#ff6384",
                        borderDash: [5, 5],
                        data: [], fill: false, tension: 0, pointRadius: 0, borderWidth: 1,
                    },
                    {
                        label: "Bed",
                        borderColor: "#36a2eb",
                        backgroundColor: "rgba(54,162,235,0.1)",
                        data: [], fill: false, tension: 0.3, pointRadius: 0, borderWidth: 2,
                    },
                    {
                        label: "Bed Target",
                        borderColor: "#36a2eb",
                        borderDash: [5, 5],
                        data: [], fill: false, tension: 0, pointRadius: 0, borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                scales: {
                    x: {
                        ticks: { color: "#aaa", maxTicksLimit: 8 },
                        grid: { color: "rgba(255,255,255,0.05)" },
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: "°C", color: "#aaa" },
                        ticks: { color: "#aaa" },
                        grid: { color: "rgba(255,255,255,0.08)" },
                    },
                },
                plugins: {
                    legend: { labels: { color: "#ccc", usePointStyle: true } },
                },
            },
        });

        // Refresh chart every 2s
        setInterval(function () {
            if (!tempChart || tempData.length === 0) return;
            const cutoff = Date.now() - tempWindowSec * 1000;
            const visible = tempData.filter(d => d.t.getTime() >= cutoff);
            tempChart.data.labels = visible.map(d => d.t.toLocaleTimeString());
            tempChart.data.datasets[0].data = visible.map(d => d.nC);
            tempChart.data.datasets[1].data = visible.map(d => d.nT);
            tempChart.data.datasets[2].data = visible.map(d => d.bC);
            tempChart.data.datasets[3].data = visible.map(d => d.bT);
            tempChart.update();
        }, 2000);
    }

    // Time window selector
    $(".temp-window").on("click", function () {
        $(".temp-window").removeClass("active");
        $(this).addClass("active");
        tempWindowSec = parseInt($(this).data("window"), 10) || 300;
    });

    /**
     * Print History Tab
     */
    let historyOffset = 0;
    const HISTORY_LIMIT = 25;

    function formatDuration(sec) {
        if (!sec) return "-";
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        const s = sec % 60;
        return h > 0 ? `${h}h ${m}m` : m > 0 ? `${m}m ${s}s` : `${s}s`;
    }

    function statusBadge(status) {
        const map = {
            started: '<span class="badge bg-primary">In Progress</span>',
            finished: '<span class="badge bg-success">Finished</span>',
            failed: '<span class="badge bg-danger">Failed</span>',
        };
        return map[status] || `<span class="badge bg-secondary">${status}</span>`;
    }

    function loadHistory(append) {
        fetch(`/api/history?limit=${HISTORY_LIMIT}&offset=${historyOffset}`)
            .then(r => r.json())
            .then(data => {
                const tbody = $("#history-tbody");
                if (!append) tbody.empty();
                if (data.entries.length === 0 && !append) {
                    tbody.html('<tr><td colspan="4" class="text-center text-muted py-4">No history yet</td></tr>');
                }
                data.entries.forEach(e => {
                    const started = e.started_at ? new Date(e.started_at + "Z").toLocaleString() : "-";
                    const safeFilename = escapeHtml(e.filename);
                    const row = `<tr>
                        <td class="text-truncate" style="max-width:200px;" title="${safeFilename}">${safeFilename}</td>
                        <td>${statusBadge(e.status)}</td>
                        <td class="small">${started}</td>
                        <td>${formatDuration(e.duration_sec)}</td>
                    </tr>`;
                    tbody.append(row);
                });
                $("#history-count").text(`${Math.min(historyOffset + data.entries.length, data.total)} / ${data.total} entries`);
                if (historyOffset + data.entries.length < data.total) {
                    $("#history-load-more").show();
                } else {
                    $("#history-load-more").hide();
                }
            })
            .catch(err => console.error("History load failed:", err));
    }

    // Load on tab switch — use native addEventListener because Cash.js splits
    // "shown.bs.tab" at the dot and registers on event type "shown" instead of
    // the full Bootstrap event type "shown.bs.tab".
    const historyTabBtn = document.querySelector('button[data-bs-target="#history"]');
    if (historyTabBtn) {
        historyTabBtn.addEventListener("shown.bs.tab", function () {
            historyOffset = 0;
            loadHistory(false);
        });
    }

    $("#history-load-more").on("click", function () {
        historyOffset += HISTORY_LIMIT;
        loadHistory(true);
    });

    $("#history-clear").on("click", function () {
        if (!confirm("Clear all print history?")) return;
        fetch("/api/history", { method: "DELETE" })
            .then(() => {
                historyOffset = 0;
                loadHistory(false);
            });
    });

    /**
     * Timelapse — list + player layout
     */
    function formatSize(bytes) {
        if (!bytes) return "-";
        const mb = bytes / (1024 * 1024);
        return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
    }

    function timelapseSelectVideo(v) {
        const card        = document.getElementById("timelapse-player-card");
        const placeholder = document.getElementById("timelapse-player-placeholder");
        const videoEl     = document.getElementById("timelapse-player");
        const titleEl     = document.getElementById("timelapse-player-title");
        const metaEl      = document.getElementById("timelapse-player-meta");
        const deleteBtn   = document.getElementById("timelapse-player-delete");
        if (!card || !videoEl) return;

        document.querySelectorAll("#timelapse-list .list-group-item").forEach(el => {
            el.classList.toggle("active", el.dataset.file === v.filename);
        });

        titleEl.textContent = v.filename;
        metaEl.textContent  = `${v.created_at ? new Date(v.created_at).toLocaleString() : "-"} · ${formatSize(v.size_bytes)}`;
        videoEl.src         = `/api/timelapse/${escapeHtml(v.filename)}`;
        videoEl.load();
        if (deleteBtn) deleteBtn.dataset.file = v.filename;
        card.style.display        = "";
        placeholder.style.display = "none";
    }

    function loadTimelapses() {
        fetch("/api/timelapses")
            .then(r => r.json())
            .then(data => {
                const banner = document.getElementById("timelapse-disabled-banner");
                if (banner) banner.style.display = data.enabled ? "none" : "";

                const list = document.getElementById("timelapse-list");
                if (!list) return;
                list.innerHTML = "";

                if (data.videos.length === 0) {
                    list.innerHTML = '<div class="text-center text-muted py-4">No timelapse videos yet</div>';
                    return;
                }
                data.videos.forEach(v => {
                    const created      = v.created_at ? new Date(v.created_at).toLocaleString() : "-";
                    const safeFilename = escapeHtml(v.filename);
                    const item         = document.createElement("div");
                    item.className     = "list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2 px-3";
                    item.dataset.file  = v.filename;
                    item.innerHTML     = `
                        <div class="overflow-hidden me-2" style="cursor:pointer; flex:1; min-width:0;">
                            <div class="text-truncate fw-semibold small">${safeFilename}</div>
                            <div class="text-muted" style="font-size:0.75em;">${created} · ${formatSize(v.size_bytes)}</div>
                        </div>
                        <div class="d-flex gap-1 flex-shrink-0">
                            <a href="/api/timelapse/${safeFilename}" class="btn btn-sm btn-outline-secondary" download title="Download">
                                <i class="bi bi-download"></i>
                            </a>
                            <button type="button" class="btn btn-sm btn-outline-danger timelapse-delete" data-file="${safeFilename}" title="Delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </div>`;
                    item.querySelector(".overflow-hidden").addEventListener("click", () => timelapseSelectVideo(v));
                    list.appendChild(item);
                });
            })
            .catch(err => console.error("Timelapse load failed:", err));
    }

    // Load on tab show; auto-refresh every 15 s while active.
    const timelapseTabBtn = document.querySelector('button[data-bs-target="#timelapse"]');
    let _timelapseInterval = null;
    if (timelapseTabBtn) {
        timelapseTabBtn.addEventListener("shown.bs.tab", function () {
            loadTimelapses();
            if (!_timelapseInterval) {
                _timelapseInterval = setInterval(loadTimelapses, 15000);
            }
        });
        timelapseTabBtn.addEventListener("hidden.bs.tab", function () {
            if (_timelapseInterval) {
                clearInterval(_timelapseInterval);
                _timelapseInterval = null;
            }
        });
    }

    // Delete timelapse (list button or player delete button)
    $(document).on("click", ".timelapse-delete", function () {
        const file = $(this).data("file");
        if (!confirm(`Delete timelapse ${file}?`)) return;
        fetch(`/api/timelapse/${file}`, { method: "DELETE" })
            .then(() => {
                // If the deleted video is currently loaded in the player, clear it
                const videoEl     = document.getElementById("timelapse-player");
                const card        = document.getElementById("timelapse-player-card");
                const placeholder = document.getElementById("timelapse-player-placeholder");
                if (videoEl && videoEl.src.endsWith(encodeURIComponent(file))) {
                    videoEl.src = "";
                    if (card)        card.style.display        = "none";
                    if (placeholder) placeholder.style.display = "";
                }
                loadTimelapses();
            });
    });

    /**
     * Timelapse Settings
     */
    const timelapseForm = $("#timelapse-form");
    if (timelapseForm.length) {
        const tlFields = {
            enabled: $("#timelapse-enabled"),
            interval: $("#timelapse-interval"),
            maxVideos: $("#timelapse-max-videos"),
            persistent: $("#timelapse-persistent"),
            light: $("#timelapse-light"),
        };
        const tlSaveBtn = $("#timelapse-save");

        const loadTimelapseSettings = async () => {
            try {
                const resp = await fetch("/api/settings/timelapse");
                if (resp.ok) {
                    const data = await resp.json();
                    const cfg = data.timelapse || {};
                    tlFields.enabled.prop("checked", Boolean(cfg.enabled));
                    tlFields.interval.val(cfg.interval || 30);
                    tlFields.maxVideos.val(cfg.max_videos || 10);
                    tlFields.persistent.prop("checked", cfg.save_persistent !== false);
                    tlFields.light.val(cfg.light || "");
                }
            } catch (err) {
                console.error("Failed to load timelapse settings:", err);
            }
        };

        tlSaveBtn.on("click", async function () {
            const btn = $(this);
            btn.prop("disabled", true);
            const payload = {
                timelapse: {
                    enabled: tlFields.enabled.is(":checked"),
                    interval: parseInt(tlFields.interval.val(), 10) || 30,
                    max_videos: parseInt(tlFields.maxVideos.val(), 10) || 10,
                    save_persistent: tlFields.persistent.is(":checked"),
                    light: tlFields.light.val() || null
                }
            };
            try {
                const resp = await fetch("/api/settings/timelapse", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (resp.ok) {
                    flash_message("Timelapse settings saved", "success");
                    loadTimelapseSettings(); // Reload to confirm
                } else {
                    const data = await resp.json().catch(() => ({}));
                    flash_message(`Failed to save: ${data.error || resp.statusText}`, "danger");
                }
            } catch (err) {
                flash_message(`Error: ${err.message}`, "danger");
            } finally {
                btn.prop("disabled", false);
            }
        });

        // Load on tab show or init
        loadTimelapseSettings();
    }

    /**
     * MQTT Settings
     */
    const mqttForm = $("#mqtt-form");
    if (mqttForm.length) {
        const mqttFields = {
            enabled: $("#mqtt-enabled"),
            host: $("#mqtt-host"),
            port: $("#mqtt-port"),
            user: $("#mqtt-user"),
            password: $("#mqtt-password"),
            prefix: $("#mqtt-prefix"),
        };
        const mqttSaveBtn = $("#mqtt-save");

        const loadMqttSettings = async () => {
            try {
                const resp = await fetch("/api/settings/mqtt");
                if (resp.ok) {
                    const data = await resp.json();
                    const cfg = data.home_assistant || {};
                    mqttFields.enabled.prop("checked", Boolean(cfg.enabled));
                    mqttFields.host.val(cfg.mqtt_host || "");
                    mqttFields.port.val(cfg.mqtt_port || 1883);
                    mqttFields.user.val(cfg.mqtt_username || "");
                    mqttFields.password.val(cfg.mqtt_password || "");
                    mqttFields.prefix.val(cfg.discovery_prefix || "homeassistant");
                }
            } catch (err) {
                console.error("Failed to load MQTT settings:", err);
            }
        };

        mqttSaveBtn.on("click", async function () {
            const btn = $(this);
            btn.prop("disabled", true);
            const payload = {
                home_assistant: {
                    enabled: mqttFields.enabled.is(":checked"),
                    mqtt_host: mqttFields.host.val().trim(),
                    mqtt_port: parseInt(mqttFields.port.val(), 10) || 1883,
                    mqtt_username: mqttFields.user.val().trim(),
                    mqtt_password: mqttFields.password.val().trim(),
                    discovery_prefix: mqttFields.prefix.val().trim(),
                }
            };
            try {
                const resp = await fetch("/api/settings/mqtt", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (resp.ok) {
                    flash_message("MQTT settings saved. Service restarting...", "success");
                    setTimeout(loadMqttSettings, 1000);
                } else {
                    const data = await resp.json().catch(() => ({}));
                    flash_message(`Failed to save: ${data.error || resp.statusText}`, "danger");
                }
            } catch (err) {
                flash_message(`Error: ${err.message}`, "danger");
            } finally {
                btn.prop("disabled", false);
            }
        });

        loadMqttSettings();
    }

    /**
     * Debug Tab Logic
     * Only initialised when the debug tab element is present (ANKERCTL_DEV_MODE=true).
     */
    if ($("#debug").length) {

        // ------------------------------------------------------------------
        // Helpers
        // ------------------------------------------------------------------

        /**
         * Build a Bootstrap table.table-sm.table-dark with key-value rows.
         * Values are colour-coded: true=success, false=danger, null=muted.
         * @param {string} title
         * @param {Object} obj
         * @returns {HTMLElement} card element
         */
        function renderSection(title, obj) {
            const card = document.createElement("div");
            card.className = "card border-secondary mb-3";

            const header = document.createElement("div");
            header.className = "card-header small fw-semibold";
            header.textContent = title;
            card.appendChild(header);

            const table = document.createElement("table");
            table.className = "table table-sm table-dark mb-0";

            const tbody = document.createElement("tbody");
            Object.entries(obj).forEach(([key, value]) => {
                const tr = document.createElement("tr");

                const tdKey = document.createElement("td");
                tdKey.className = "text-muted small w-50";
                tdKey.textContent = key;

                const tdVal = document.createElement("td");
                tdVal.className = "small font-monospace";

                if (value === true) {
                    tdVal.innerHTML = '<span class="text-success">true</span>';
                } else if (value === false) {
                    tdVal.innerHTML = '<span class="text-danger">false</span>';
                } else if (value === null || value === undefined) {
                    tdVal.innerHTML = '<span class="text-muted">null</span>';
                } else {
                    tdVal.textContent = String(value);
                }

                tr.appendChild(tdKey);
                tr.appendChild(tdVal);
                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            card.appendChild(table);
            return card;
        }

        // ------------------------------------------------------------------
        // State Inspector
        // ------------------------------------------------------------------

        async function dbgRefreshState() {
            try {
                const resp = await fetch("/api/debug/state");
                if (!resp.ok) {
                    document.getElementById("dbg-state-tables").textContent = `Error: HTTP ${resp.status}`;
                    return;
                }
                const data = await resp.json();

                const container = document.getElementById("dbg-state-tables");
                container.innerHTML = "";

                // Top-level scalar values (e.g. debug_logging)
                const scalars = {};
                Object.entries(data).forEach(([key, val]) => {
                    if (typeof val !== "object" || val === null) {
                        scalars[key] = val;
                    }
                });
                if (Object.keys(scalars).length > 0) {
                    container.appendChild(renderSection("General", scalars));
                }

                // Nested objects rendered as separate tables
                Object.entries(data).forEach(([key, val]) => {
                    if (typeof val === "object" && val !== null) {
                        container.appendChild(renderSection(key.charAt(0).toUpperCase() + key.slice(1), val));
                    }
                });

                // Sync controls checkbox
                if (data.debug_logging !== undefined) {
                    $("#dbg-log-mqtt").prop("checked", data.debug_logging);
                }
            } catch (err) {
                document.getElementById("dbg-state-tables").textContent = "Error fetching state: " + err;
            }
        }

        document.getElementById("dbg-refresh-state").addEventListener("click", dbgRefreshState);

        // Auto-refresh state while the inspector sub-tab is active
        const dbgInspectorTab = document.getElementById("dbg-inspector-tab");
        let dbgStateInterval = null;
        if (dbgInspectorTab) {
            dbgInspectorTab.addEventListener("shown.bs.tab", function () {
                dbgRefreshState();
                dbgStateInterval = setInterval(dbgRefreshState, 3000);
            });
            dbgInspectorTab.addEventListener("hidden.bs.tab", function () {
                if (dbgStateInterval) { clearInterval(dbgStateInterval); dbgStateInterval = null; }
            });
        }

        // Also refresh when the top-level Debug tab itself is shown
        const mainDebugTabBtn = document.getElementById("debug-tab");
        if (mainDebugTabBtn) {
            mainDebugTabBtn.addEventListener("shown.bs.tab", function () {
                dbgRefreshState();
            });
        }

        // ------------------------------------------------------------------
        // Controls
        // ------------------------------------------------------------------

        $("#dbg-log-mqtt").on("change", async function () {
            const enabled = $(this).is(":checked");
            await fetch("/api/debug/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ debug_logging: enabled })
            });
            dbgRefreshState();
        });

        // ------------------------------------------------------------------
        // Simulation
        // ------------------------------------------------------------------

        async function dbgSimEvent(type, payload) {
            try {
                await fetch("/api/debug/simulate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ type: type, payload: payload })
                });
                dbgRefreshState();
            } catch (err) {
                flash_message("Sim failed: " + err, "danger");
            }
        }

        document.getElementById("dbg-sim-start").addEventListener("click", function () {
            dbgSimEvent("start", { filename: "debug_test.gcode" });
        });
        document.getElementById("dbg-sim-finish").addEventListener("click", function () {
            dbgSimEvent("finish", { filename: "debug_test.gcode" });
        });
        document.getElementById("dbg-sim-fail").addEventListener("click", function () {
            dbgSimEvent("fail", { filename: "debug_test.gcode" });
        });

        // Progress slider
        const progressSlider = document.getElementById("dbg-sim-progress-slider");
        const progressValue = document.getElementById("dbg-sim-progress-value");
        if (progressSlider) {
            progressSlider.addEventListener("input", function () {
                progressValue.textContent = this.value + "%";
            });
        }
        document.getElementById("dbg-sim-progress-btn").addEventListener("click", function () {
            const pct = progressSlider ? parseInt(progressSlider.value, 10) : 50;
            dbgSimEvent("progress", {
                progress: pct,
                filename: "debug_test.gcode",
                elapsed: 120,
                remaining: 60,
            });
        });

        // Temperature buttons
        $(".dbg-sim-temp").on("click", function () {
            const btn = $(this);
            dbgSimEvent("temperature", {
                temp_type: btn.data("temp-type"),
                current: parseInt(btn.data("current"), 10),
                target: parseInt(btn.data("target"), 10),
            });
        });

        // Speed button
        document.getElementById("dbg-sim-speed").addEventListener("click", function () {
            dbgSimEvent("speed", { speed: 250 });
        });

        // Layer button
        document.getElementById("dbg-sim-layer").addEventListener("click", function () {
            dbgSimEvent("layer", { current_layer: 42, total_layers: 200 });
        });

        // ------------------------------------------------------------------
        // Services Health Dashboard
        // ------------------------------------------------------------------

        /**
         * Return a Bootstrap badge colour class for a service state name.
         * @param {string} state
         * @returns {string}
         */
        function serviceStateClass(state) {
            switch (state) {
                case "Running": return "bg-success";
                case "Starting":
                case "Stopping": return "bg-warning text-dark";
                default: return "bg-secondary";
            }
        }

        async function dbgRefreshServices() {
            try {
                const resp = await fetch("/api/debug/services");
                if (!resp.ok) {
                    $("#dbg-services-grid").html(`<div class="col-12 text-danger small">Error: HTTP ${resp.status}</div>`);
                    return;
                }
                const data = await resp.json();
                const grid = $("#dbg-services-grid");
                grid.empty();

                // Determine if a print is currently active (for restart warning)
                let isPrinting = false;
                try {
                    const stateResp = await fetch("/api/debug/state");
                    if (stateResp.ok) {
                        const stateData = await stateResp.json();
                        isPrinting = !!(stateData.print && stateData.print.active);
                    }
                } catch (_) { /* ignore */ }

                Object.entries(data.services).forEach(([name, svc]) => {
                    const badgeClass = serviceStateClass(svc.state);
                    const card = $(`<div class="col-md-6 col-lg-4">
                        <div class="card border-secondary h-100">
                            <div class="card-header d-flex justify-content-between align-items-center small">
                                <strong>${escapeHtml(name)}</strong>
                                <span class="badge ${badgeClass}">${escapeHtml(svc.state)}</span>
                            </div>
                            <div class="card-body p-2">
                                <div class="small text-muted mb-1">
                                    <span class="me-2">Type: <code>${escapeHtml(svc.type)}</code></span>
                                </div>
                                <div class="small text-muted mb-2">
                                    <span class="me-2">Refs: ${svc.refs}</span>
                                    <span>Wanted: <span class="${svc.wanted ? 'text-success' : 'text-danger'}">${svc.wanted}</span></span>
                                </div>
                                <button class="btn btn-sm btn-outline-warning w-100 dbg-restart-svc"
                                    data-svc-name="${escapeHtml(name)}"
                                    data-is-printing="${isPrinting}">
                                    <i class="bi-arrow-clockwise"></i> Restart
                                </button>
                            </div>
                        </div>
                    </div>`);
                    grid.append(card);
                });

                const ts = new Date().toLocaleTimeString();
                $("#dbg-services-refresh-indicator").text(`Last updated: ${ts}`);
            } catch (err) {
                $("#dbg-services-grid").html(`<div class="col-12 text-danger small">Error: ${escapeHtml(String(err))}</div>`);
            }
        }

        // Restart button handler (delegated)
        $(document).on("click", ".dbg-restart-svc", async function () {
            const name = $(this).data("svc-name");
            const isPrinting = $(this).data("is-printing");
            const printWarning = isPrinting
                ? "\n\nWarning: A print is currently active. Restarting may interrupt it."
                : "";
            if (!confirm(`Restart service "${name}"?${printWarning}`)) return;

            try {
                const resp = await fetch(`/api/debug/services/${encodeURIComponent(name)}/restart`, {
                    method: "POST",
                });
                if (resp.ok) {
                    flash_message(`Service "${name}" restarting...`, "info");
                    setTimeout(dbgRefreshServices, 1500);
                    setTimeout(dbgRefreshServices, 3500);
                } else {
                    const data = await resp.json().catch(() => ({}));
                    flash_message(`Restart failed: ${data.error || resp.statusText}`, "danger");
                }
            } catch (err) {
                flash_message(`Restart failed: ${err}`, "danger");
            }
        });

        document.getElementById("dbg-refresh-services").addEventListener("click", dbgRefreshServices);

        // Auto-refresh when the services pill is active
        const dbgServicesTab = document.getElementById("dbg-services-tab");
        let dbgServicesInterval = null;
        if (dbgServicesTab) {
            dbgServicesTab.addEventListener("shown.bs.tab", function () {
                dbgRefreshServices();
                dbgServicesInterval = setInterval(dbgRefreshServices, 5000);
            });
            dbgServicesTab.addEventListener("hidden.bs.tab", function () {
                if (dbgServicesInterval) { clearInterval(dbgServicesInterval); dbgServicesInterval = null; }
            });
        }

        // ------------------------------------------------------------------
        // Log Viewer (enhanced)
        // ------------------------------------------------------------------

        let _rawLogLines = [];

        const dbgLogFileSelect = $("#dbg-log-file");
        const dbgLogContent = document.getElementById("dbg-log-content");
        const dbgLogPre = document.getElementById("dbg-log-pre");
        const dbgLogLevelFilter = document.getElementById("dbg-log-level");
        const dbgLogSearch = document.getElementById("dbg-log-search");
        const dbgLogCount = document.getElementById("dbg-log-count");
        const dbgLogAutoRefresh = document.getElementById("dbg-log-autorefresh");
        const dbgLogLinesInput = document.getElementById("dbg-log-lines");
        let dbgLogRefreshInterval = null;

        // Restore persisted viewer height from localStorage
        const _savedLogHeight = localStorage.getItem("dbg_log_height");
        if (_savedLogHeight && dbgLogPre) {
            dbgLogPre.style.height = _savedLogHeight;
        }

        // Persist viewer height on resize via ResizeObserver
        if (dbgLogPre && typeof ResizeObserver !== "undefined") {
            new ResizeObserver(function () {
                localStorage.setItem("dbg_log_height", dbgLogPre.style.height || dbgLogPre.offsetHeight + "px");
            }).observe(dbgLogPre);
        }

        // Restore and persist the lines-to-fetch setting
        if (dbgLogLinesInput) {
            const _savedLines = localStorage.getItem("dbg_log_lines");
            if (_savedLines) {
                dbgLogLinesInput.value = _savedLines;
            }
            dbgLogLinesInput.addEventListener("change", function () {
                localStorage.setItem("dbg_log_lines", this.value);
            });
        }

        async function dbgRefreshLogList() {
            try {
                const resp = await fetch("/api/debug/logs");
                if (!resp.ok) return;
                const data = await resp.json();
                const currentVal = dbgLogFileSelect.val();
                dbgLogFileSelect.empty();
                $('<option value="" disabled selected>Select log file...</option>').appendTo(dbgLogFileSelect);
                data.files.forEach(file => {
                    const opt = $(`<option value="${escapeHtml(file)}">${escapeHtml(file)}</option>`);
                    if (file === currentVal) opt.prop("selected", true);
                    dbgLogFileSelect.append(opt);
                });
            } catch (err) {
                console.error("Failed to list logs:", err);
            }
        }

        /**
         * Render filtered log lines into the DOM, applying level filter,
         * text search with <mark> highlighting, and updating the line counter.
         */
        function dbgApplyLogFilters() {
            const levelFilter = dbgLogLevelFilter ? dbgLogLevelFilter.value.trim().toUpperCase() : "";
            const searchTerm = dbgLogSearch ? dbgLogSearch.value.trim() : "";
            const searchLower = searchTerm.toLowerCase();

            let filtered = _rawLogLines;

            if (levelFilter) {
                filtered = filtered.filter(line => line.toUpperCase().includes(levelFilter));
            }
            if (searchTerm) {
                filtered = filtered.filter(line => line.toLowerCase().includes(searchLower));
            }

            dbgLogCount.textContent = `${filtered.length} / ${_rawLogLines.length} lines`;

            if (!searchTerm) {
                // No search — just escape and join
                dbgLogContent.innerHTML = filtered.map(l => escapeHtml(l)).join("\n");
            } else {
                // Highlight search term with <mark>
                const escapedSearch = searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
                const re = new RegExp(`(${escapedSearch})`, "gi");
                dbgLogContent.innerHTML = filtered
                    .map(l => escapeHtml(l).replace(re, "<mark>$1</mark>"))
                    .join("\n");
            }

            // Auto-scroll to bottom only when the user is already near the bottom,
            // so that manually scrolling up to read earlier lines is not interrupted.
            if (dbgLogPre) {
                const atBottom = dbgLogPre.scrollHeight - dbgLogPre.scrollTop - dbgLogPre.clientHeight < 40;
                if (atBottom) {
                    dbgLogPre.scrollTop = dbgLogPre.scrollHeight;
                }
            }
        }

        async function dbgLoadLogContent() {
            const filename = dbgLogFileSelect.val();
            if (!filename) return;
            try {
                const lines = dbgLogLinesInput ? (parseInt(dbgLogLinesInput.value, 10) || 500) : 500;
                const resp = await fetch(`/api/debug/logs/${encodeURIComponent(filename)}?lines=${lines}`);
                if (resp.ok) {
                    const data = await resp.json();
                    _rawLogLines = data.content.split("\n");
                    dbgApplyLogFilters();
                } else {
                    dbgLogContent.textContent = `Error loading log: ${resp.status}`;
                }
            } catch (err) {
                dbgLogContent.textContent = `Error loading log: ${err}`;
            }
        }

        dbgLogFileSelect.on("change", dbgLoadLogContent);
        document.getElementById("dbg-log-refresh-btn").addEventListener("click", dbgLoadLogContent);

        if (dbgLogLevelFilter) {
            dbgLogLevelFilter.addEventListener("change", dbgApplyLogFilters);
        }
        if (dbgLogSearch) {
            dbgLogSearch.addEventListener("input", dbgApplyLogFilters);
        }

        const dbgLogsTab = document.getElementById("dbg-logs-tab");
        if (dbgLogsTab) {
            dbgLogsTab.addEventListener("shown.bs.tab", dbgRefreshLogList);
        }

        if (dbgLogAutoRefresh) {
            dbgLogAutoRefresh.addEventListener("change", function () {
                if (this.checked) {
                    dbgLoadLogContent();
                    dbgLogRefreshInterval = setInterval(dbgLoadLogContent, 5000);
                } else {
                    if (dbgLogRefreshInterval) { clearInterval(dbgLogRefreshInterval); dbgLogRefreshInterval = null; }
                }
            });
        }

        // Clean up intervals when leaving the Debug tab
        if (mainDebugTabBtn) {
            mainDebugTabBtn.addEventListener("hidden.bs.tab", function () {
                if (dbgStateInterval) { clearInterval(dbgStateInterval); dbgStateInterval = null; }
                if (dbgServicesInterval) { clearInterval(dbgServicesInterval); dbgServicesInterval = null; }
                if (dbgLogRefreshInterval) {
                    clearInterval(dbgLogRefreshInterval);
                    dbgLogRefreshInterval = null;
                    if (dbgLogAutoRefresh) dbgLogAutoRefresh.checked = false;
                }
            });
        }

        async function dbgRefreshBedLevel() {
            const statusEl = document.getElementById("dbg-bedlevel-status");
            const gridEl = document.getElementById("dbg-bedlevel-grid");
            const statsEl = document.getElementById("dbg-bedlevel-stats");
            const btn = document.getElementById("dbg-bedlevel-refresh");

            if (!statusEl || !gridEl) return;

            // Show loading state
            statusEl.innerHTML =
                '<div class="alert alert-info py-2 small mb-0">' +
                '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
                'Sending M420 V — waiting for printer response (up to 15 s)...</div>';
            gridEl.style.display = "none";
            if (btn) btn.disabled = true;

            try {
                const resp = await fetch("/api/debug/bed-leveling");
                const data = await resp.json();

                if (!resp.ok) {
                    statusEl.innerHTML =
                        `<div class="alert alert-danger py-2 small mb-0">` +
                        `Error ${resp.status}: ${escapeHtml(data.error || "Unknown error")}</div>`;
                    return;
                }

                // Render stats bar
                if (statsEl) {
                    statsEl.innerHTML =
                        `<span><strong>Min:</strong> ${data.min.toFixed(3)} mm</span>` +
                        `<span><strong>Max:</strong> +${data.max.toFixed(3)} mm</span>` +
                        `<span><strong>Range:</strong> ${(data.max - data.min).toFixed(3)} mm</span>` +
                        `<span class="text-muted">(${data.rows}&times;${data.cols} grid)</span>`;
                }

                bedLevelRenderGrid(data.grid, data.min, data.max);

                statusEl.innerHTML = "";
                gridEl.style.display = "block";
            } catch (err) {
                statusEl.innerHTML =
                    `<div class="alert alert-danger py-2 small mb-0">` +
                    `Request failed: ${escapeHtml(String(err))}</div>`;
            } finally {
                if (btn) btn.disabled = false;
            }
        }

    } // end debug tab block

    /**
     * Filament Profiles
     */
    const filamentModal = document.getElementById("filamentModal");
    const bsFilamentModal = filamentModal ? new bootstrap.Modal(filamentModal) : null;

    function filamentToggleScarf() {
        const enabled = document.getElementById("filament-scarf-enabled");
        const opts    = document.getElementById("filament-scarf-opts");
        if (enabled && opts) opts.style.display = enabled.checked ? "" : "none";
    }

    function filamentToggleWipe() {
        const enabled = document.getElementById("filament-wipe-enabled");
        const opts    = document.getElementById("filament-wipe-opts");
        if (enabled && opts) opts.style.display = enabled.checked ? "" : "none";
    }

    function filamentReadForm() {
        return {
            name:                    document.getElementById("filament-name").value.trim(),
            brand:                   document.getElementById("filament-brand").value.trim(),
            material:                document.getElementById("filament-material").value.trim(),
            color:                   document.getElementById("filament-color").value,
            nozzle_temp_other_layer: parseInt(document.getElementById("filament-nozzle-temp-other").value, 10) || 0,
            nozzle_temp_first_layer: parseInt(document.getElementById("filament-nozzle-temp-first").value, 10) || 0,
            bed_temp_other_layer:    parseInt(document.getElementById("filament-bed-temp-other").value, 10) || 0,
            bed_temp_first_layer:    parseInt(document.getElementById("filament-bed-temp-first").value, 10) || 0,
            flow_rate:               parseFloat(document.getElementById("filament-flow-rate").value) || 1.0,
            filament_diameter:       parseFloat(document.getElementById("filament-diameter").value) || 1.75,
            pressure_advance:        parseFloat(document.getElementById("filament-pressure-advance").value) || 0,
            max_volumetric_speed:    parseFloat(document.getElementById("filament-max-vol-speed").value) || 0,
            travel_speed:            parseInt(document.getElementById("filament-travel-speed").value, 10) || 0,
            perimeter_speed:         parseInt(document.getElementById("filament-perimeter-speed").value, 10) || 0,
            infill_speed:            parseInt(document.getElementById("filament-infill-speed").value, 10) || 0,
            cooling_enabled:         document.getElementById("filament-cooling-enabled").checked ? 1 : 0,
            cooling_min_fan_speed:   parseInt(document.getElementById("filament-cooling-min").value, 10) || 0,
            cooling_max_fan_speed:   parseInt(document.getElementById("filament-cooling-max").value, 10) || 100,
            seam_position:           document.getElementById("filament-seam-position").value,
            seam_gap:                parseFloat(document.getElementById("filament-seam-gap").value) || 0,
            scarf_enabled:           document.getElementById("filament-scarf-enabled").checked ? 1 : 0,
            scarf_conditional:       document.getElementById("filament-scarf-conditional").checked ? 1 : 0,
            scarf_angle_threshold:   parseInt(document.getElementById("filament-scarf-angle").value, 10) || 155,
            scarf_length:            parseFloat(document.getElementById("filament-scarf-length").value) || 20.0,
            scarf_steps:             parseInt(document.getElementById("filament-scarf-steps").value, 10) || 10,
            scarf_speed:             parseInt(document.getElementById("filament-scarf-speed").value, 10) || 100,
            retract_length:          parseFloat(document.getElementById("filament-retract-length").value) || 0,
            retract_speed:           parseInt(document.getElementById("filament-retract-speed").value, 10) || 45,
            retract_lift_z:          parseFloat(document.getElementById("filament-retract-lift-z").value) || 0,
            wipe_enabled:            document.getElementById("filament-wipe-enabled").checked ? 1 : 0,
            wipe_distance:           parseFloat(document.getElementById("filament-wipe-distance").value) || 1.5,
            wipe_speed:              parseInt(document.getElementById("filament-wipe-speed").value, 10) || 40,
            wipe_retract_before:     document.getElementById("filament-wipe-retract-before").checked ? 1 : 0,
            notes:                   document.getElementById("filament-notes").value.trim(),
        };
    }

    function filamentFillForm(p) {
        document.getElementById("filament-id").value                       = p.id || "";
        document.getElementById("filament-name").value                     = p.name || "";
        document.getElementById("filament-brand").value                    = p.brand || "";
        document.getElementById("filament-material").value                 = p.material || "";
        document.getElementById("filament-color").value                    = p.color || "#FFFFFF";
        document.getElementById("filament-nozzle-temp-other").value        = p.nozzle_temp_other_layer ?? p.nozzle_temp ?? 220;
        document.getElementById("filament-nozzle-temp-first").value        = p.nozzle_temp_first_layer ?? (p.nozzle_temp_other_layer ?? p.nozzle_temp ?? 220) + 5;
        document.getElementById("filament-bed-temp-other").value           = p.bed_temp_other_layer ?? p.bed_temp ?? 60;
        document.getElementById("filament-bed-temp-first").value           = p.bed_temp_first_layer ?? (p.bed_temp_other_layer ?? p.bed_temp ?? 60) + 5;
        document.getElementById("filament-flow-rate").value                = p.flow_rate ?? 1.0;
        document.getElementById("filament-diameter").value                 = p.filament_diameter ?? 1.75;
        document.getElementById("filament-pressure-advance").value         = p.pressure_advance ?? 0;
        document.getElementById("filament-max-vol-speed").value            = p.max_volumetric_speed ?? 15;
        document.getElementById("filament-travel-speed").value             = p.travel_speed ?? 120;
        document.getElementById("filament-perimeter-speed").value          = p.perimeter_speed ?? 60;
        document.getElementById("filament-infill-speed").value             = p.infill_speed ?? 80;
        document.getElementById("filament-cooling-enabled").checked        = !!p.cooling_enabled;
        document.getElementById("filament-cooling-min").value              = p.cooling_min_fan_speed ?? 0;
        document.getElementById("filament-cooling-max").value              = p.cooling_max_fan_speed ?? 100;
        document.getElementById("filament-seam-position").value            = p.seam_position || "aligned";
        document.getElementById("filament-seam-gap").value                 = p.seam_gap ?? 0;
        document.getElementById("filament-scarf-enabled").checked          = !!p.scarf_enabled;
        document.getElementById("filament-scarf-conditional").checked      = !!p.scarf_conditional;
        document.getElementById("filament-scarf-angle").value              = p.scarf_angle_threshold ?? 155;
        document.getElementById("filament-scarf-length").value             = p.scarf_length ?? 20;
        document.getElementById("filament-scarf-steps").value              = p.scarf_steps ?? 10;
        document.getElementById("filament-scarf-speed").value              = p.scarf_speed ?? 100;
        document.getElementById("filament-retract-length").value           = p.retract_length ?? 0.8;
        document.getElementById("filament-retract-speed").value            = p.retract_speed ?? 45;
        document.getElementById("filament-retract-lift-z").value           = p.retract_lift_z ?? 0;
        document.getElementById("filament-wipe-enabled").checked           = !!p.wipe_enabled;
        document.getElementById("filament-wipe-distance").value            = p.wipe_distance ?? 1.5;
        document.getElementById("filament-wipe-speed").value               = p.wipe_speed ?? 40;
        document.getElementById("filament-wipe-retract-before").checked    = !!p.wipe_retract_before;
        document.getElementById("filament-notes").value                    = p.notes || "";
        // Sync conditional sub-section visibility
        filamentToggleScarf();
        filamentToggleWipe();
    }

    function filamentOpenNew() {
        filamentFillForm({});
        document.getElementById("filamentModalLabel").textContent = "New Filament Profile";
        if (bsFilamentModal) bsFilamentModal.show();
    }

    function filamentOpenEdit(profile) {
        filamentFillForm(profile);
        document.getElementById("filamentModalLabel").textContent = "Edit Filament Profile";
        if (bsFilamentModal) bsFilamentModal.show();
    }

    let _filamentSortAsc = true;
    let _filamentAllProfiles = [];

    function _renderFilaments() {
        const tbody = document.getElementById("filaments-tbody");
        if (!tbody) return;
        const query = (document.getElementById("filament-search")?.value || "").toLowerCase().trim();
        let profiles = _filamentAllProfiles.slice();
        if (query) {
            profiles = profiles.filter(p =>
                (p.name || "").toLowerCase().includes(query) ||
                (p.material || "").toLowerCase().includes(query) ||
                (p.brand || "").toLowerCase().includes(query)
            );
        }
        profiles.sort((a, b) => {
            const cmp = (a.name || "").localeCompare(b.name || "");
            return _filamentSortAsc ? cmp : -cmp;
        });
        if (profiles.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No filament profiles found</td></tr>';
            return;
        }
        tbody.innerHTML = "";
        profiles.forEach(p => {
                    const safeName     = escapeHtml(p.name);
                    const safeMaterial = escapeHtml(p.material || "");
                    const safeBrand    = escapeHtml(p.brand || "");
                    const safeId       = parseInt(p.id, 10);
                    const dotColor     = escapeHtml(p.color || "#FFFFFF");
                    const colorDot     = `<span style="display:inline-block;width:1.1rem;height:1.1rem;border-radius:50%;background:${dotColor};border:1px solid #aaa;vertical-align:middle;box-shadow:inset 0 0 0 1px rgba(0,0,0,0.08);"></span>`;
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td class="text-center">${colorDot}</td>
                        <td class="fw-semibold">${safeName}</td>
                        <td>${safeMaterial}</td>
                        <td class="text-muted small">${safeBrand}</td>
                        <td>${p.nozzle_temp_other_layer ?? p.nozzle_temp ?? "-"}&thinsp;°C</td>
                        <td>${p.bed_temp_other_layer ?? p.bed_temp ?? "-"}&thinsp;°C</td>
                        <td>${p.filament_diameter}&thinsp;mm</td>
                        <td class="text-end" style="white-space:nowrap;">
                            <div class="d-flex gap-1 justify-content-end">
                                <button class="btn btn-sm btn-outline-secondary filament-edit" data-id="${safeId}" title="Edit">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-info filament-duplicate" data-id="${safeId}" title="Duplicate">
                                    <i class="bi bi-files"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-warning filament-preheat" data-id="${safeId}" title="Preheat printer to these temperatures">
                                    <i class="bi bi-thermometer-half"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger filament-delete" data-id="${safeId}" title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </td>`;
                    tr.querySelector(".filament-edit").addEventListener("click", () => filamentOpenEdit(p));
                    tr.querySelector(".filament-duplicate").addEventListener("click", () => {
                        fetch(`/api/filaments/${safeId}/duplicate`, { method: "POST" })
                            .then(r => r.json())
                            .then(() => loadFilaments())
                            .catch(err => console.error("Duplicate failed:", err));
                    });
                    tr.querySelector(".filament-preheat").addEventListener("click", () => {
                        const nozzle = p.nozzle_temp_first_layer ?? p.nozzle_temp_other_layer ?? p.nozzle_temp ?? "?";
                        const bed    = p.bed_temp_first_layer ?? p.bed_temp_other_layer ?? p.bed_temp ?? "?";
                        if (!confirm(`Preheat printer for ${p.name}?\nNozzle: ${nozzle}°C, Bed: ${bed}°C`)) return;
                        fetch(`/api/filaments/${safeId}/apply`, { method: "POST" })
                            .then(r => r.json())
                            .then(res => {
                                if (res.error) { alert("Error: " + res.error); return; }
                                console.log("Preheat sent:", res.gcode);
                            })
                            .catch(err => console.error("Preheat failed:", err));
                    });
                    tr.querySelector(".filament-delete").addEventListener("click", () => {
                        if (!confirm(`Delete filament profile "${p.name}"?`)) return;
                        fetch(`/api/filaments/${safeId}`, { method: "DELETE" })
                            .then(() => loadFilaments())
                            .catch(err => console.error("Delete failed:", err));
                    });
                    tbody.appendChild(tr);
                });
    }

    function loadFilaments() {
        fetch("/api/filaments")
            .then(r => r.json())
            .then(data => {
                _filamentAllProfiles = data.filaments || [];
                _renderFilaments();
            })
            .catch(err => console.error("Filaments load failed:", err));
    }

    // Sort button
    const filamentSortBtn = document.getElementById("filament-sort-btn");
    if (filamentSortBtn) {
        filamentSortBtn.addEventListener("click", function () {
            _filamentSortAsc = !_filamentSortAsc;
            const icon = document.getElementById("filament-sort-icon");
            if (icon) {
                icon.className = _filamentSortAsc ? "bi bi-sort-alpha-down" : "bi bi-sort-alpha-up";
            }
            _renderFilaments();
        });
    }

    // Search input
    const filamentSearch = document.getElementById("filament-search");
    if (filamentSearch) {
        filamentSearch.addEventListener("input", function () { _renderFilaments(); });
    }

    // Save button: create or update
    const filamentSaveBtn = document.getElementById("filament-save-btn");
    if (filamentSaveBtn) {
        filamentSaveBtn.addEventListener("click", function () {
            const profileId = document.getElementById("filament-id").value;
            const payload   = filamentReadForm();
            if (!payload.name) {
                document.getElementById("filament-name").classList.add("is-invalid");
                return;
            }
            document.getElementById("filament-name").classList.remove("is-invalid");

            const isNew  = !profileId;
            const url    = isNew ? "/api/filaments" : `/api/filaments/${profileId}`;
            const method = isNew ? "POST" : "PUT";

            fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            })
                .then(r => r.json())
                .then(res => {
                    if (res.error) { alert("Error: " + res.error); return; }
                    if (bsFilamentModal) bsFilamentModal.hide();
                    loadFilaments();
                })
                .catch(err => console.error("Save failed:", err));
        });
    }

    const filamentNewBtn = document.getElementById("filament-new-btn");
    if (filamentNewBtn) {
        filamentNewBtn.addEventListener("click", filamentOpenNew);
    }

    // Scarf sub-section toggle
    const scarfEnabledEl = document.getElementById("filament-scarf-enabled");
    if (scarfEnabledEl) {
        scarfEnabledEl.addEventListener("change", filamentToggleScarf);
    }

    // Wipe sub-section toggle
    const wipeEnabledEl = document.getElementById("filament-wipe-enabled");
    if (wipeEnabledEl) {
        wipeEnabledEl.addEventListener("change", filamentToggleWipe);
    }

    // Load when tab becomes active
    const filamentsTabBtn = document.querySelector('button[data-bs-target="#filaments"]');
    if (filamentsTabBtn) {
        filamentsTabBtn.addEventListener("shown.bs.tab", function () {
            loadFilaments();
        });
    }

    // Printer selector — switch active printer from the navbar dropdown
    document.querySelectorAll("#printer-selector .dropdown-item").forEach(function(item) {
        item.addEventListener("click", function(e) {
            e.preventDefault();
            var newIndex = parseInt(this.getAttribute("data-printer-index"), 10);
            if (isNaN(newIndex) || this.classList.contains("active")) return;

            if (!confirm("Switch printer? All connections will be restarted.")) return;

            fetch("/api/printers/active", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({index: newIndex})
            })
            .then(function(resp) {
                return resp.json().then(function(data) { return {ok: resp.ok, data: data}; });
            })
            .then(function(r) {
                if (!r.ok) {
                    alert("Error: " + (r.data.error || "Failed to switch printer"));
                    return;
                }
                // Reload after 2.5s to allow services to restart
                setTimeout(function() { window.location.reload(); }, 2500);
            })
            .catch(function(err) {
                alert("Failed to switch printer: " + err);
            });
        });
    });

});

