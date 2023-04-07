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

    $('#light-on').on('click', function() {
        wsctrl.send(JSON.stringify({"light": true}));
        return false;
    });

    $('#light-off').on('click', function() {
        wsctrl.send(JSON.stringify({"light": false}));
        return false;
    });


    $('#configData').on('click',function(){
        navigator.clipboard.writeText("{{ configHost }}:{{ configPort }}");
        return false;
    });
});
