let polling, connected_index, indices, ready;
initialise()

function initialise() {
    if (ready) { return }
    try {
        bridgeCommand('contanki::initialise::arg');
        // Causes a lot of console spam if we try to call bridgeCommand too early
    } catch (err) {
        setTimeout(initialise, 1000);
        return;
    }
    window.addEventListener("gamepadconnected", on_controller_connect);
    window.addEventListener("gamepaddisconnected", on_controller_disconnect);
    ready = true;
}

function on_controller_connect() {
    let controllers = window.navigator.getGamepads();
    let register = 'contanki::register';
    indices = [];
    for (let i = 0; i < controllers.length; i++) {
        let con = controllers[i];
        if (con != null && con.connected) {
            indices.push(i);
            register += `::${con.id}%%%${con.buttons.length}%%%${con.axes.length}`;
        }
    };
    if (indices.length == 0) {
        bridgeCommand('contanki::message::No controllers detected. Please reconnect your controller and try again.');
    } else {
        if (indices.length > 1) { 
            bridgeCommand(register); 
        }
        connect_controller(indices[0]);
    }
}

function connect_controller(i) {
    window.clearInterval(polling);
    let con = window.navigator.getGamepads()[i];
    if (con == null) {
        bridgeCommand('contanki::message::Could not find controller. Please reconnect your controller and try again.');;
        return;
    }
    bridgeCommand(`contanki::on_connect::${con.buttons.length}::${con.axes.length}::${con.id}`);
    connected_index = i;
    polling = setInterval(poll, 50);
}

function on_controller_disconnect(event) {
    bridgeCommand(`contanki::on_disconnect::arg`);
    window.clearInterval(polling);
    connected_index = null;
    let controllers = window.navigator.getGamepads();
    for (let i = 0; i < controllers.length; i++) {
        if (controllers[i] != null) {
            on_controller_connect(event);
            return;
        }
    }
}

function poll() {
    if (connected_index == null) {
        on_controller_disconnect();
        return;
    }

    let con = window.navigator.getGamepads()[connected_index];

    try {
        if (!con.connected) {
            on_controller_disconnect();
            return;
        }
    } catch (err) {
        on_controller_disconnect();
        return;
    }

    let buttons = con.buttons.map(button => button.pressed);
    bridgeCommand(`contanki::poll::${buttons}::${con.axes}`);
}

function get_controller_info() {
    let controllers = window.navigator.getGamepads();
    let ids = "";
    for (let i = 0; i < controllers.length; i++) {
        let con = controllers[i];
        if (con != null && con.connected) {
            ids += `%%%${con.id}%${con.buttons.length}%${con.axes.length}`;
        }
    }
    return ids
}