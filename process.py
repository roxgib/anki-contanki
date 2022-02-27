import json
import csv

with open("./controllerIDs.csv") as f:
    controllers = csv.reader(f.readlines())

_controllers = list()

for vid, vendor, pid, product in controllers:
    line = vid, vendor, pid, product
    _controllers.append(line)

vendors = dict()
controllers = dict()

for vid, vendor, pid, product in _controllers:
    if vid not in vendors or vendors[vid] == '':
        vendors[vid] = vendor
    controllers[vid] = dict()

for vid, vendor, pid, product in _controllers:
    if pid not in controllers[vid] or controllers[vid][pid] == '':
        controllers[vid][pid] = product

out = {
    'vendors': vendors,
    'devices': controllers,
}

with open("./controllerIDs.json", 'w') as f:
    json.dump(out, f)