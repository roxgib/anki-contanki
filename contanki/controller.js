let polling, index, indices, ready;
initialise()

function initialise() {
    if (ready) {return}
    try {
        bridgeCommand('contanki::initialise::arg');
    } catch (err) {
        setTimeout(initialise, 1000);
        return;
    }
    window.addEventListener("gamepadconnected", on_controller_connect);
    window.addEventListener("gamepaddisconnected", on_controller_disconnect);
    ready = true;
}

function on_controller_connect(event) {
    let controllers = window.navigator.getGamepads();
    let register = 'contanki::register';
    indices = [];
    for (let i = 0; i < controllers.length; i++) {
        if (controllers[i] != null && controllers[i].connected == true) {
            indices.push(i);
            register = register + `::${controllers[i].id}%%%${controllers[i].buttons.length}%%%${controllers[i].axes.length}`;
        }
    }
    if (indices.length == 0) {
        bridgeCommand('contanki::message::Error connecting to controller. Please try again.')
    } else if (indices.length == 1) {
        connect_controller(indices[0]);
    } else {
        let most = 0;
        let i = 0;
        for (con in indices) {
            if (most < controllers[con].buttons.length) {
                most = controllers[con].buttons.length;
                i = con;
            }
        }
        bridgeCommand(register);
        connect_controller(i);
        bridgeCommand('contanki::message::Multiple controllers are not yet supported.');
    }
}

function connect_controller(i) {
    index = i
    let controllers = window.navigator.getGamepads();
    bridgeCommand(`contanki::on_connect::${controllers[index].buttons.length}::${controllers[index].axes.length}::${controllers[index].id}`);
    window.clearInterval(polling);
    polling = setInterval(poll, 50);
}

function on_controller_disconnect(event) {
    bridgeCommand(`contanki::on_disconnect::arg`);
    window.clearInterval(polling);
    index = null;
}

function poll() {
    if (index == null) {on_controller_disconnect()}
    
    let controller = window.navigator.getGamepads()[index];

    try {
        if (controller.connected == false) {
            on_controller_disconnect();
            return;
        } 
    } catch (err) {
        on_controller_disconnect();
        return;
    }

    let buttons = new Array();
    let axes = new Array();

    for (let i = 0; i < controller.buttons.length; i++) {
        buttons.push(controller.buttons[i].pressed.toString());
    }

    for (let i = 0; i < controller.axes.length; i++) {
        axes.push(controller.axes[i].toString());
    }
    
    bridgeCommand(`contanki::poll::${buttons.toString()}::${axes.toString()}`);
}
