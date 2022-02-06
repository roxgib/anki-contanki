import json
import jsonschema
from jsonschema import ValidationError

_manifest_schema: dict = {
    "type": "object",
    "properties": {
        # the name of the folder
        "package": {"type": "string", "minLength": 1, "meta": False},
        # the displayed name to the user
        "name": {"type": "string", "meta": True},
        # the time the add-on was last modified
        "mod": {"type": "number", "meta": True},
        # a list of other packages that conflict
        "conflicts": {"type": "array", "items": {"type": "string"}, "meta": True},
        # the minimum 2.1.x version this add-on supports
        "min_point_version": {"type": "number", "meta": True},
        # if negative, abs(n) is the maximum 2.1.x version this add-on supports
        # if positive, indicates version tested on, and is ignored
        "max_point_version": {"type": "number", "meta": True},
        # AnkiWeb sends this to indicate which branch the user downloaded.
        "branch_index": {"type": "number", "meta": True},
        # version string set by the add-on creator
        "human_version": {"type": "string", "meta": True},
        # add-on page on AnkiWeb or some other webpage
        "homepage": {"type": "string", "meta": True},
    },
    "required": ["package", "name"],
}

def readManifestFile():
        try:
            with open("contanki/manifest.json") as f:
                data = json.loads(f.read())
            jsonschema.validate(data, _manifest_schema)
            # build new manifest from recognized keys
            schema = _manifest_schema["properties"]
            manifest = {key: data[key] for key in data.keys() & schema.keys()}
        except (KeyError, json.decoder.JSONDecodeError, ValidationError):
            # raised for missing manifest, invalid json, missing/invalid keys
            return {}
        return manifest

print(readManifestFile())


