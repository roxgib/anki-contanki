document.getElementById("ds4").innerHTML = "initialising";
var controller = null;
var polling = null;
window.addEventListener("gamepadconnected", on_controller_connect);
window.addEventListener("gamepaddisconnected", on_controller_connect);

function sBridgeCommand(arg) {
    try {
        bridgeCommand(arg);
    } catch (err) {
        console.log(`bridgeCommand error: ${arg}.`)
    }
}

function on_controller_connect() {
    controller = window.navigator.getGamepads()[0];
    if (controller == null) {
        window.clearInterval(polling)
        sBridgeCommand(`ds4:on_connect:None`);
        document.getElementById("ds4").innerHTML = 'Disconnected'
        return;
    }
    else {
        polling = setInterval(poll, 50);
        sBridgeCommand(`ds4:on_connect:${controller.id}`);
        document.getElementById("ds4").innerHTML = controller.id;
    }
}

// DUALSHOCK 4 Wireless Controller (STANDARD GAMEPAD)

function poll() {
    if (controller == null) {
        return;
    }

    let _controller = window.navigator.getGamepads()[0]

    for (let i = 0; i < _controller.axes.length; i++) {
        sBridgeCommand(`ds4:on_update_axis:${i}:${_controller.axes[i]}`);
    }

    sBridgeCommand(`ds4:on_update_axis:${4}:${_controller.buttons[6].value}`);
    sBridgeCommand(`ds4:on_update_axis:${5}:${_controller.buttons[7].value}`);
    
    for (let i = 0; i < _controller.buttons.length; i++) {
        if (i != 6 && i != 7){    
            if (_controller.buttons[i].pressed) {
                sBridgeCommand(`ds4:on_button_press:${i}`);
            }
        }
    }
}
