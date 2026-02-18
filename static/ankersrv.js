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
            if (data.commandType == 1001) {
                // Returns Print Details
                $("#print-name").text(data.name);
                $("#time-elapsed").text(getTime(data.totalTime));
                $("#time-remain").text(getTime(data.time));
                const progress = getPercentage(data.progress);
                $("#progressbar").attr("aria-valuenow", progress);
                $("#progressbar").attr("style", `width: ${progress}%`);
                $("#progress").text(`${progress}%`);
                // Update browser tab title with print progress
                document.title = progress > 0 && progress < 100
                    ? `\u{1F5A8}\uFE0F ${progress}% | ankerctl`
                    : "ankerctl";
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
            document.title = "ankerctl";
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
    const PRINT_CONTROLS_VISIBLE = document.body.dataset.printControls === "true";
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
        STOP: 0,
        PAUSE: 1,
        RESUME: 2,
    };

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

    if (PRINT_CONTROLS_VISIBLE) {
        document.body.classList.remove("print-controls-hidden");
        $("#print-pause").on("click", function () {
            sendPrintControl(PRINT_CONTROL.PAUSE);
            sendPrinterGCode("M25");
            return false;
        });
        $("#print-resume").on("click", function () {
            sendPrintControl(PRINT_CONTROL.RESUME);
            sendPrinterGCode("M24");
            return false;
        });
        $("#print-stop").on("click", function () {
            if (confirm("Are you sure you want to stop the print? This will also turn off heaters.")) {
                sendPrintControl(PRINT_CONTROL.STOP);
                sendPrinterGCode("M25\nM104 S0\nM140 S0\nM106 S0\nM524\nM77");
            }
            return false;
        });
    } else {
        document.body.classList.add("print-controls-hidden");
    }

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
                    const row = `<tr>
                        <td class="text-truncate" style="max-width:200px;" title="${e.filename}">${e.filename}</td>
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

    // Load on tab switch
    $('button[data-bs-target="#history"]').on("shown.bs.tab", function () {
        historyOffset = 0;
        loadHistory(false);
    });

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

});
