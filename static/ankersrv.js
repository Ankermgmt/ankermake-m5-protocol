$(function () {
    /**
     * Copies provided text to the OS clipboard
     * @param {string} text
     */
    function updateClipboard(text) {
        navigator.clipboard.writeText(text);
        console.log(`Copied ${text} to clipboard`);
    }

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
     * Opens a websocket connection and outputs any incoming message data to console
     */
    socket = new WebSocket("ws://" + location.host + "/ws/mqtt");
    socket.addEventListener("message", (ev) => {
        console.log(JSON.parse(ev.data));
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
