$(function () {

    socket = new WebSocket("ws://" + location.host + "/ws/mqtt");
    socket.addEventListener('message', ev => {
        console.log(JSON.parse(ev.data));
    });


    var jmuxer;
    jmuxer = new JMuxer({
        node: 'player',
        mode: 'video',
        flushingTime: 0,
        fps: 15,
        // debug: true,
        onReady: function(data) {
            console.log(data);
        },
        onError: function(data) {
            console.log(data);
        }
    });

    var ws = new WebSocket("ws://" + location.host + "/ws/video");
    ws.binaryType = 'arraybuffer';
    ws.addEventListener('message',function(event) {
        jmuxer.feed({
            video: new Uint8Array(event.data)
        });
    });

    ws.addEventListener('error', function(e) {
        console.log('Socket Error');
    });

    var wsctrl = new WebSocket("ws://" + location.host + "/ws/ctrl");
    wsctrl.addEventListener("open", (event) => {
        // Set initial state of Light & Quality (Defaults to Off:Low)
        wsctrl.send(JSON.stringify({"light": false}));
        wsctrl.send(JSON.stringify({"quality": 0}));
    });

    $('#light-on').on('click', function() {
        wsctrl.send(JSON.stringify({"light": true}));
        return false;
    });

    $('#light-off').on('click', function() {
        wsctrl.send(JSON.stringify({"light": false}));
        return false;
    });

    $('#quality-low').on('click', function() {
        wsctrl.send(JSON.stringify({"quality": 0}));
        return false;
    });

    $('#quality-high').on('click', function() {
        wsctrl.send(JSON.stringify({"quality": 1}));
        return false;
    });
    
    $('#configData').on('click',function(){
        navigator.clipboard.writeText($('#octoPrintHost').val());
        return false;
    });

    $('#copyFilePath').on('click',function(){
        navigator.clipboard.writeText($('#loginFilePath').val());
        return false;
    });

    let alert_list = document.querySelectorAll('.alert');
    alert_list.forEach(function(alert) {
        new bootstrap.Alert(alert);

        let alert_timeout = alert.getAttribute('data-timeout');
        setTimeout(() => {
            bootstrap.Alert.getInstance(alert).close();
        }, +alert_timeout);
    });
});
