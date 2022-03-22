var controller = null;
var polling = null;
var index = 0;
var ready = false
initialise()

function initialise() {
    if (ready) {return}
    try {
        bridgeCommand('contanki::message::Contanki Initialised');
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
        bridgeCommand(`contanki::on_disconnect::arg`);
    } else {
        for (let i = 0; i < controllers.length; i++) {
            if (controllers[i] != null && controllers[i].connected == true) {
                bridgeCommand(`contanki::on_connect::${controllers[i].buttons.length}::${controllers[i].axes.length}::${controllers[i].id}`);
                index = i;
                polling = setInterval(poll, 50);
                return;
            }
        }
    }
    window.clearInterval(polling);
}

function on_controller_disconnect(e) {
    bridgeCommand(`contanki::on_disconnect::arg`);
    window.clearInterval(polling);
    index = null;
}


function poll() {
    if (index == null) {on_controller_disconnect()}
    
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

    let buttons = new Array();
    let axes = new Array();

    for (let i = 0; i < _controller.buttons.length; i++) {
        buttons.push(_controller.buttons[i].pressed.toString());
    }

    for (let i = 0; i < _controller.axes.length; i++) {
        axes.push(_controller.axes[i].toString());
    }
    
    bridgeCommand(`contanki::poll::${buttons.toString()}::${axes.toString()}`);
}
