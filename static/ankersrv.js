$(function () {

    socket = new WebSocket("ws://" + location.host + "/mqtt");
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

    var ws = new WebSocket("ws://" + location.host + "/video");
    ws.binaryType = 'arraybuffer';
    ws.addEventListener('message',function(event) {
        jmuxer.feed({
            video: new Uint8Array(event.data)
        });
    });

    ws.addEventListener('error', function(e) {
        console.log('Socket Error');
    });


    $('#configData').on('click',function(){
        navigator.clipboard.writeText("{{ configHost }}:{{ configPort }}");
        return false;
    });
});
