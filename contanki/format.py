import code
import json

with open("contanki/mappings.json") as f:
    data = json.load(f)

controllers = {controller: {} for controller in data["BUTTON_NAMES"]}

for controller, d in controllers.items():
    d["name"] = controller
    d["buttons"] = {i: b for i, b in data["BUTTON_NAMES"][controller].items() if int(i) < 100}
    d["axis_buttons"] = {str(int(i) - 101): b for i, b in data["BUTTON_NAMES"][controller].items() if int(i) > 100}
    d["axes"] = data["AXES_NAMES"][controller]
    d["num_buttons"] = len([button for button in d["buttons"] if int(button) < 100])
    d["num_axes"] = len(d["axes"])
    d["has_stick"] = data["HAS_STICK"][controller]
    d["supported"] = True
    d["has_dpad"] = True
    

with open("contanki/controllers.json", "x") as f:
    json.dump(controllers, f)