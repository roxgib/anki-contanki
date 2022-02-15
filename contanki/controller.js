var controller = null;
var polling = null;
var index = 0;
var ready = false
initialise()

function initialise() {
    if (ready) {return}
    try {
        bridgeCommand('pcs:message:Contanki Initialised');
    } catch (err) {
        setTimeout(initialise, 1000);
        return;
    }
    window.addEventListener("gamepadconnected", on_controller_connect);
    window.addEventListener("gamepaddisconnected", on_controller_disconnect);
    on_controller_connect();
    ready = true;
}


function on_controller_connect(e) {
    let controllers = window.navigator.getGamepads();
    if (controllers.length == 0) {
        window.clearInterval(polling);
        bridgeCommand(`pcs:on_disconnect:arg`);
    } else {
        for (let i = 0; i < controllers.length; i++) {
            if (controllers[i].connected == true) {
                bridgeCommand(`pcs:on_connect:${controllers[i].buttons.length}:${controllers[i].id}`);
                index = i;
                polling = setInterval(poll, 50);
                return;
            }
        }
    }
    window.clearInterval(polling);
}

function on_controller_disconnect(e) {
    bridgeCommand(`pcs:on_disconnect:arg`);
    window.clearInterval(polling);
    index = null;
    on_controller_connect();
}


function poll() {
    let _controller = window.navigator.getGamepads()[index];

    try{
        if (_controller.connected == false) {
            on_controller_disconnect();
            return;
        } 
    } catch (err) {
        on_controller_disconnect();
        return;
    }
    
    bridgeCommand(`pcs:update_left:${_controller.axes[0]}:${_controller.axes[1]}`);
    bridgeCommand(`pcs:update_right:${_controller.axes[2]}:${_controller.axes[3]}`);
    bridgeCommand(`pcs:update_triggers:${_controller.buttons[6].value}:${_controller.buttons[7].value}`);

    let buttons = new Array();
    for (let i = 0; i < _controller.buttons.length; i++) {
        buttons.push(_controller.buttons[i].pressed.toString());
    }
    
    bridgeCommand(`pcs:update_buttons:${buttons.toString()}`);
}
