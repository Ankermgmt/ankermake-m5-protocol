$(function () {
    /**
     * Updates the Copywrite year on document ready
     */
    $("#copyYear").text(new Date().getFullYear());

    /**
     * Copies provided text to the OS clipboard
     * @param {string} text
     */
    function updateClipboard(text) {
        navigator.clipboard.writeText(text);
        console.log(`Copied ${text} to clipboard`);
    }

    /**
     * Redirect page when modal dialog is shown
     */
    var popupModal = document.getElementById("popupModal");

    popupModal.addEventListener("shown.bs.modal", function (e) {
        window.location.href = $("#reload").data("href");
    });

    /**
     * On click of element with id "configData", updates clipboard with text in element with id "octoPrintHost"
     */
    $("#configData").on("click", function () {
        const value = $("#octoPrintHost").text();
        updateClipboard(value);
    });

    /**
     * On click of element with id "copyFilePath", updates clipboard with text in element with id "loginFilePath"
     */
    $("#copyFilePath").on("click", function () {
        const value = $("#loginFilePath").text();
        updateClipboard(value);
    });

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

    sockets = {};

    /**
     * Opens a websocket connection and outputs any incoming message data to console
     */
    function connect_mqtt_ws() {
        var ws = sockets.mqtt = new WebSocket("ws://" + location.host + "/ws/mqtt");

        ws.addEventListener("message", (ev) => {
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
                console.log(data);
            }
        });

        ws.addEventListener("open", (ev) => {
            $("#badge-mqtt").removeClass("text-bg-danger").addClass("text-bg-success");
        });

        ws.addEventListener("close", function (e) {
            console.log("MQTT socket close");
            $("#badge-mqtt").removeClass("text-bg-success").addClass("text-bg-danger");

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
            setTimeout(() => connect_mqtt_ws(), 1000);
        });

        ws.addEventListener("error", function (e) {
            console.log("MQTT socket error");
            ws.close();
        });
    };

    /**
     * Initializing a new instance of JMuxer for video playback
     */
    function connect_video_ws() {
        var jmuxer;
        jmuxer = new JMuxer({
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

        /**
         * Opens a websocket connection for video streaming and feeds the data to the JMuxer instance
         */
        var ws = sockets.pppp = new WebSocket("ws://" + location.host + "/ws/video");

        ws.binaryType = "arraybuffer";
        ws.addEventListener("message", function (event) {
            jmuxer.feed({
                video: new Uint8Array(event.data),
            });
        });

        ws.addEventListener("open", function (e) {
            $("#badge-pppp").removeClass("text-bg-danger").addClass("text-bg-success");
        });

        ws.addEventListener("close", function (e) {
            $("#badge-pppp").removeClass("text-bg-success").addClass("text-bg-danger");
            console.log("Video socket close");
            jmuxer.destroy();
            setTimeout(() => connect_video_ws(), 1000);
        });

        ws.addEventListener("error", function (e) {
            console.log("Video socket error");
            ws.close();
        });
    };

    function connect_ctrl_ws() {
        /**
         * Opens a websocket connection for controlling video and sends JSON data based on button clicks
         */
        var ws = sockets.ctrl = new WebSocket("ws://" + location.host + "/ws/ctrl");

        ws.addEventListener("open", function (e) {
            $("#badge-ctrl").removeClass("text-bg-danger").addClass("text-bg-success");
        });

        ws.addEventListener("close", function (e) {
            $("#badge-ctrl").removeClass("text-bg-success").addClass("text-bg-danger");
            console.log("Control socket close");
            setTimeout(() => connect_ctrl_ws(), 1000);
        });

        ws.addEventListener("close", function (e) {
            console.log("Control socket error");
            ws.close();
        });
    };

    /**
     * On click of element with id "light-on", sends JSON data to wsctrl to turn light on
     */
    $("#light-on").on("click", function () {
        sockets.ctrl.send(JSON.stringify({ light: true }));
        return false;
    });

    /**
     * On click of element with id "light-off", sends JSON data to wsctrl to turn light off
     */
    $("#light-off").on("click", function () {
        sockets.ctrl.send(JSON.stringify({ light: false }));
        return false;
    });

    /**
     * On click of element with id "quality-low", sends JSON data to wsctrl to set video quality to low
     */
    $("#quality-low").on("click", function () {
        sockets.ctrl.send(JSON.stringify({ quality: 0 }));
        return false;
    });

    /**
     * On click of element with id "quality-high", sends JSON data to wsctrl to set video quality to high
     */
    $("#quality-high").on("click", function () {
        sockets.ctrl.send(JSON.stringify({ quality: 1 }));
        return false;
    });

    connect_mqtt_ws();
    connect_video_ws();
    connect_ctrl_ws();
});
