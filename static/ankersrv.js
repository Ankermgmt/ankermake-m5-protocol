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
    let alert_list = document.querySelectorAll(".alert");
    alert_list.forEach(function (alert) {
        new bootstrap.Alert(alert);

        let alert_timeout = alert.getAttribute("data-timeout");
        setTimeout(() => {
            bootstrap.Alert.getInstance(alert).close();
        }, +alert_timeout);
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
     * Opens a websocket connection and outputs any incoming message data to console
     */
    socket = new WebSocket("ws://" + location.host + "/ws/mqtt");
    socket.addEventListener("message", (ev) => {
        const data = JSON.parse(ev.data);
        if (data.commandType == 1001) {
            // Returns Print Details
            $("#print-details").attr("style", "display: block;");
            $("#print-name").attr("value", data.name);
            $("#time-elapsed").attr("value", getTime(data.totalTime));
            $("#time-remain").attr("value", getTime(data.time));
            const progress = getPercentage(data.progress);
            $("#progressbar").attr("aria-valuenow", progress);
            $("#progressbar").attr("style", `width: ${progress}%`);
            $("#progress").text(`${progress}%`);
        } else if (data.commandType == 1003) {
            // Returns Nozzle Temp
            const current = getTemp(data.currentTemp);
            const target = getTemp(data.targetTemp);
            $("#nozzle-temp").attr("value", `${current}°C`);
            $("#set-nozzle-temp").attr("value", `${target}°C`);
        } else if (data.commandType == 1004) {
            // Returns Bed Temp
            const current = getTemp(data.currentTemp);
            const target = getTemp(data.targetTemp);
            $("#bed-temp").attr("value", `${current}°C`);
            $("#set-bed-temp").attr("value", `${target}°C`);
        } else if (data.commandType == 1006) {
            // Returns Print Speed
            const X = getSpeedFactor(data.value);
            $("#print-speed").attr("value", `${data.value}mm/s ${X}`);
        } else if (data.commandType == 1052) {
            // Returns Layer Info
            const layer = `${data.real_print_layer}/${data.total_layer}`;
            $("#print-layer").attr("value", layer);
        } else {
            console.log(data);
        }
    });

    /**
     * Initializing a new instance of JMuxer for video playback
     */
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
    var ws = new WebSocket("ws://" + location.host + "/ws/video");
    ws.binaryType = "arraybuffer";
    ws.addEventListener("message", function (event) {
        jmuxer.feed({
            video: new Uint8Array(event.data),
        });
    });

    ws.addEventListener("error", function (e) {
        console.log("Socket Error");
    });

    /**
     * Opens a websocket connection for controlling video and sends JSON data based on button clicks
     */
    var wsctrl = new WebSocket("ws://" + location.host + "/ws/ctrl");

    /**
     * On click of element with id "light-on", sends JSON data to wsctrl to turn light on
     */
    $("#light-on").on("click", function () {
        wsctrl.send(JSON.stringify({ light: true }));
        return false;
    });

    /**
     * On click of element with id "light-off", sends JSON data to wsctrl to turn light off
     */
    $("#light-off").on("click", function () {
        wsctrl.send(JSON.stringify({ light: false }));
        return false;
    });

    /**
     * On click of element with id "quality-low", sends JSON data to wsctrl to set video quality to low
     */
    $("#quality-low").on("click", function () {
        wsctrl.send(JSON.stringify({ quality: 0 }));
        return false;
    });

    /**
     * On click of element with id "quality-high", sends JSON data to wsctrl to set video quality to high
     */
    $("#quality-high").on("click", function () {
        wsctrl.send(JSON.stringify({ quality: 1 }));
        return false;
    });
});
