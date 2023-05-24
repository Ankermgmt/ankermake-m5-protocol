<% import js %>\
${js.header()}

% for enum in [_mqtt.get("MqttMsgType")]:
const ${enum.name} = {
   % for const in enum.consts:
    ${const.aligned_name} : ${const.aligned_hex_value},
    % endfor
}
% endfor
