import os
from collections import defaultdict
from typing import Optional

from aqt import mw

from .funcs import get_dark_mode, get_file

# Need to refactor to easily support other controllers


def get_svg(svg_content, color):

    svg = f"""<svg viewBox="50 0 250 90" version="1.1">
                <g transform="translate(60)" fill="{color}" stroke="{color}" font-family="Noto Sans JP" font-size="5px" stroke-width="0.5">
                {svg_content}
                </g></svg>"""

    return svg


def build_svg_mappings(bindings: dict, controller: str = 'DS4') -> dict:
    states: dict = {"profileManager", "deckBrowser", "overview", "question", "answer"}
    svg = defaultdict(dict)
    for state in bindings.keys():
        for mod in ['', 'R2', 'L2']:
            svg[state][mod] = build_svg_content(bindings[state], mod, controller)

    return svg


def build_svg_content(bindings: dict, mod, controller: str = 'DS4') -> str:
        
    texts = {
        "Cross":        '<text text-anchor="start" y="60.85" x="194" >',
        "Circle":       '<text text-anchor="start" y="46.28" x="190" >',
        "Square":       '<text text-anchor="start" y="74.22" x="198" >',
        "Triangle":     '<text text-anchor="start" y="33.90" x="185" >',
        "D-Pad Up":     '<text text-anchor="end" y="32.90" x="38.83" >',
        "D-Pad Down":   '<text text-anchor="end" y="57.58" x="31.03" >',
        "D-Pad Left":   '<text text-anchor="end" y="44.36" x="35.49" >',
        "D-Pad Right":  '<text text-anchor="end" y="74.01" x="28.34" >',
        "L1":           '<text text-anchor="middle" y="6.39" x="53.57" >',
        "R1":           '<text text-anchor="middle" y="6.60" x="169.93" >',
        "Share":        '<text text-anchor="middle" y="12.55" x="88.11" >',
        "Options":      '<text text-anchor="middle" y="12.55" x="135.66" >',
        "Pad":          '<text text-anchor="middle" y="6.67" x="110" >',
        "PS":           '<text text-anchor="middle" y="85" x="120" >',
        "Left Stick":   '<text text-anchor="end" y="80" x="70" >',
        "Right Stick":  '<text text-anchor="start" y="80" x="155" >',
    }

    lines = {
        "Triangle":     '<line y2="31.36" x2="184.03" y1="28.84" x1="171.26" />',
        "Circle":       '<path d="m 182.96, 41.66 5.85, 2.101" />',
        "Cross":        '<path d="m 172.35, 53.01 20.57, 4.832" />',
        "Square":       """<line y2="47.54" x2="155.02" y1="62.88" x1="161.29" />
                        <line y2="71.28" x2="196.59" y1="62.67" x1="161.29" />""",
        "D-Pad Up":     '<path d="M 55.41, 30.94 41.12, 31.154" />',
        "D-Pad Down":   '<line y2="55.10" x2="33.10" y1="50.91" x1="55.84" />',
        "D-Pad Left":   '<path d="M 46.10, 40.61 36.14, 41.66" />',
        "D-Pad Right":  """<path d="M 63.64, 63.93 29.64, 71.286" />
                        <line y2="63.72" x2="63.64" y1="45.44" x1="72.95" />""",
        "Share":        '<line y2="13.92" x2="88.98" y1="21.91" x1="81.61" />',
        "Options":      '<line y2="14.13" x2="138.34" y1="21.49" x1="144.84" />',
        "L1":           '<line y2="7.82" x2="55.63" y1="15.82" x1="63.64" />',
        "R1":           '<line y2="8.67" x2="173.21" y1="16.44" x1="166.92" />',
        "Pad":          '<line y2="8.08" x2="111.36" y1="25.19" x1="115.24" />',
        "PS":           '<line y2="70" x2="115" y1="80" x1="120" />',
        "Left Stick":   '<line y2="74.22" x2="68.84" y1="66.24" x1="77.71" />',
        "Right Stick":  '<line y2="74.01" x2="158.26" y1="65.82" x1="148.30" />',
    }

    other = {
        "L2":           '<text text-anchor="end" y="40" x="115">L2</text>',
        "R2":           """<text text-anchor="end" y="40" x="115">R2</text>
                        <text text-anchor="end" y="85" x="110" >Scroll</text>
                        <line y2="80" x2="100" y1="66.24" x1="90" />""",
        "":             """<text text-anchor="end" y="85" x="130" >Mouse</text>
                        <line y2="80" x2="125" y1="65.82" x1="130" />""",
    }

    collect = list()
    collect.append(get_file(controller))
    for key in texts.keys():
        modkey = " + ".join([mod, key]) if mod else key
        if modkey not in bindings or bindings[modkey] == '': continue
        collect.append(f"{texts[key]}{bindings[modkey]}</text>")
        collect.append(lines[key])
    collect.append(other[mod])

    return "\n".join(collect)


def buildSVG(controller: str, mapping: Optional[dict] = None) -> str: # needs to insert theme colours
    svg = get_file(controller)
    annotations = list()
    if mapping:
        for control, action in mapping.items():
            annotations.append(generateAnnotation(controller, action, control))
    else:
        for control in CONTROLLER_IMAGE_MAPS[controller]['AXES']:
            annotations.append(generateAnnotation(controller, control, axis = True))
        for control in CONTROLLER_IMAGE_MAPS[controller]['BUTTONS']:
            annotations.append(generateAnnotation(controller, control))
    return svg[:-13] + '\n'.join(annotations) + svg[-13:]


def generateAnnotation(controller: str, control: int, text: Optional[str] = None, axis: bool = False):
    x1, y1, x2, y2, anchor = CONTROLLER_IMAGE_MAPS[controller]['AXES' if axis else 'BUTTONS'][control]
    output = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
    if text:
        output += f"""\n<text text-anchor="{['start','middle','end'][anchor]}" x="{x2}" y="{y2}">{text}</text>"""

    return output


CONTROLLER_IMAGE_MAPS = {
    "DualShock3": {
        'BUTTONS': {
            0: (105,50,60,194,0),
            1: (113,43,46,190,0),
            2: (95,46,74,198,0),
            3: (105,34,33,185,0),
            4: (48,22,6,53,1),
            5: (100,22,6,169,1),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,12,88,1),
            9: (88,41,12,135,1),
            10: (60,56,80,70,2),
            11: (89,56,80,155,0),
            12: (45,35,32,38,2),
            13: (45,50,57,31,2),
            14: (40,43,44,35,2),
            15: (30,47,74,28,2),
            16: (75,48,6,110,1),
            },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
            },
        },
    "DualShock4": {
        'BUTTONS': {
            0: (106,46,120,46,0),
            1: (112.5,39.5,120,39.5,0),
            2: (97,42,102,53,0),
            3: (106,32.5,120,32.5,0),
            4: (48,25,35,17,0),
            5: (100,25,115,17,2),
            6: (48,25,45,10,0),
            7: (100,25,105,10,2),
            8: (56,28,62,18,1),
            9: (93,28,88,18,1),
            10: (57,53,45,62,0),
            11: (95,53,107,62,2),
            12: (45,34,30,34,2),
            13: (45,46,30,46,2),
            14: (40,40,30,40,2),
            15: (52,42,48,53,2),
            16: (75,55,75,60,1),
            17: (75,30,75,10,1),
        },
        'AXES': {
            0: (60,56,55,69,0),
            1: (60,56,60,76,0),
            2: (90,56,95,69,2),
            3: (90,56,90,76,2),
        },
    },
    "DualSense": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "JoyCon": { # needs transform removed
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "SwitchPro": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "Steam": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "Wii": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "XBox360": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "XBoxOne": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        },
    },
    "XBoxAdaptive": {
        'BUTTONS': {
            0: (105,50,0,0,0),
            1: (113,43,0,0,0),
            2: (95,46,0,0,0),
            3: (105,34,0,0,0),
            4: (48,22,0,0,0),
            5: (100,22,0,0,0),
            6: (48,22,0,0,0),
            7: (100,22,0,0,0),
            8: (66,41,0,0,0),
            9: (88,41,0,0,0),
            10: (60,56,0,0,0),
            11: (89,56,0,0,0),
            12: (45,35,0,0,0),
            13: (45,50,0,0,0),
            14: (40,43,0,0,0),
            15: (30,47,0,0,0),
            16: (75,48,0,0,0),
            17: (0,0,0,0,0),
        },
        'AXES': {
            0: (60,56,0,0,0),
            1: (60,56,0,0,0),
            2: (89,56,0,0,0),
            3: (89,56,0,0,0),
        }
    }
}


