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


def build_svg_mappings(bindings: dict, controller: str) -> dict:
    svg = defaultdict(dict)
    for state in bindings.keys():
        for mod in ['', 'R2', 'L2']:
            svg[state][mod] = buildSVG(controller, bindings[state], mod)

    return svg


def build_svg_content(bindings: dict, mod, controller: str = 'DualShock4') -> str:
        
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


def get_svg_file(file: str) -> str:
    addon_path = os.path.dirname(os.path.abspath(__file__))

    path = os.path.join(addon_path, 'controllers')

    if os.path.exists(os.path.join(path, file)):
        with open(os.path.join(path, file)) as f:
            return f.read()


def buildSVG(controller: str, mapping: Optional[dict] = None) -> str: # needs to insert theme colours
    svg = get_svg_file(controller)
    annotations = list()
    if mapping:
        for control, action in mapping.items():
            annotations.append(generateAnnotation(controller, action, control))
    else:
        for control in CONTROLLER_IMAGE_MAPS[controller]:
            annotations.append(generateAnnotation(controller, control))
    return svg[:-13] + '\n'.join(annotations) + svg[-13:]


def generateAnnotation(controller: str, control: int, text: Optional[str] = None):
    x1, y1, x2, y2, anchor = CONTROLLER_IMAGE_MAPS[controller][control]
    output = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
    if text:
        output += f"""\n<text text-anchor="{['start','middle','end'][anchor]}" x="{x2}" y="{y2}">{text}</text>"""

    return output


CONTROLLER_IMAGE_MAPS = {
    "DualShock 3": {
        0: (105,50,120,50,0),
        1: (113,43,120,43,0),
        2: (95,46,105,60,0),
        3: (105,36,120,36,0),
        4: (43,23,35,17,2),
        5: (105,23,115,17,0),
        6: (48,22,45,10,0),
        7: (100,22,105,10,0),
        8: (65,41,60,18,1),
        9: (85,41,90,18,1),
        10: (60,56,40,70,2),
        11: (90,56,110,70,0),
        12: (45,35,30,35,2),
        13: (45,50,30,50,2),
        14: (40,43,30,43,2),
        15: (53,45,43,60,2),
        16: (75,48,75,10,1),
        },
    "DualShock 4": {
        0: (106,46,120,46,0),
        1: (112.5,39.5,120,39.5,0),
        2: (97,42,102,53,0),
        3: (106,32.5,120,32.5,0),
        4: (48,25,35,17,2),
        5: (100,25,115,17,0),
        6: (48,25,45,8,0),
        7: (100,25,105,8,0),
        8: (56,28,58,18,1),
        9: (93,28,92,18,1),
        10: (57,53,45,62,2),
        11: (95,53,100,62,0),
        12: (45,34,30,34,2),
        13: (45,46,30,46,2),
        14: (40,40,30,40,2),
        15: (52,42,48,53,2),
        16: (75,55,75,65,1),
        17: (75,30,75,10,1),
    },
    "DualSense": {
        0: (105,45,120,45,0),
        1: (111.5,38,120,38,0),
        2: (96,41,102,52,0),
        3: (106,31,120,31,0),
        4: (48,23,30,17,2),
        5: (100,23,120,17,0),
        6: (48,23,45,10,0),
        7: (100,23,105,10,0),
        8: (56,28,55,18,1),
        9: (95,28,95,18,1),
        10: (57,53,50,60,2),
        11: (94,53,100,60,0),
        12: (45,32,30,33,2),
        13: (45,44,30,45,2),
        14: (40,38,30,39,2),
        15: (53,40,48,53,2),
        16: (75,50,75,65,1),
        17: (75,25,75,10,1),
    },
    "JoyCon": { # needs transform removed
        0: (107,42,120,45,0),
        1: (112,36,120,35,0),
        2: (100,36,81,41,2),
        3: (107,30,120,25,0),
        4: (48,22,35,17,2),
        5: (100,22,115,17,0),
        6: (48,22,45,8,0),
        7: (100,22,105,8,0),
        8: (50,27,68,30,0),
        9: (100,27,82,25,2),
        10: (45,35,30,30,2),
        11: (106,53,111,62,0),
        12: (44,46,30,44,2),
        13: (44,58,30,60,2),
        14: (38,52,30,52,2),
        15: (49.5,53,60,60,0),
        16: (46,63,46,85,1),
        17: (103,63,103,85,1),
    },
    "JoyCon Left": {
        0: (75,45,75,22,1),
        1: (69,51,60,70,2),
        2: (75,56,75,80,1),
        3: (81,51,90,70,0),
        4: (60,34,50,25,2),
        5: (85,34,100,25,0),
        6: (59,52,40,60,0),
        7: (50,44,30,50,0),
        8: (86,48,110,48,0),
    },
    "JoyCon Right": {
        0: (87,45,70,22,0),
        1: (81,51,71,70,2),
        2: (87,56,86,80,1),
        3: (93,51,101,70,0),
        4: (60,35,50,25,2),
        5: (85,35,100,25,0),
        6: (71,52,50,65,0),
        7: (60,49,35,60,0),
        8: (95,46,110,46,0),
    },
    "Switch Pro Controller": {
        0: (100,47,120,47,0),
        1: (107,39,120,39,0),
        2: (91,42,102,55,0),
        3: (100,31,120,31,0),
        4: (48,23,35,17,2),
        5: (100,23,115,17,0),
        6: (48,23,45,10,0),
        7: (100,23,105,10,0),
        8: (64,32,62,18,1),
        9: (86,32,88,18,1),
        10: (45,36,35,26,0),
        11: (90,53,107,70,2),
        12: (60,44,40,49,2),
        13: (60,57,40,63,2),
        14: (54,50.5,40,56,2),
        15: (68,53,55,70,2),
        16: (80,40,70,65,0),
        17: (69,38,75,10,1),
    },
    "Steam Controller": {
        0: (105,65,120,45,0),
        1: (111.5,58,120,38,0),
        2: (96,61,102,52,0),
        3: (106,51,106,31,0),
        4: (48,23,35,17,2),
        5: (100,23,115,17,0),
        6: (48,23,45,10,0),
        7: (100,23,105,10,0),
        8: (75,40,60,18,1),
        9: (75,40,90,18,1),
        10: (65,50,50,75,0),
        11: (110,30,130,50,2),
        12: (50,32,40,33,2),
        13: (55,44,40,45,2),
        14: (50,38,40,39,2),
        15: (63,40,58,53,2),
        16: (75,40,75,65,1),
    },
    "Wii Remote": {
        0: (80,70,100,70,0),
        1: (80,80,100,80,0),
        2: (80,33,100,40,0),
        3: (70,35,60,40,2),
        4: (85,50,100,60,0),
        5: (75,50,40,60,2),
        6: (80,50,75,40,0),
    },
    "Xbox 360 Controller": {
        0: (100,45,120,45,0),
        1: (106,38,120,38,0),
        2: (91,38,95,50,0),
        3: (100,31,120,31,0),
        4: (45,23,35,17,2),
        5: (103,23,115,17,0),
        6: (48,22,45,8,0),
        7: (100,22,105,8,0),
        8: (65,38,61,15,1),
        9: (83,38,89,15,1),
        10: (49,35,30,30,2),
        11: (85,52,85,70,1),
        12: (61,48,40,40,2),
        13: (61,55,40,60,2),
        14: (57,51,40,50,2),
        15: (65,51,65,62,1),
        16: (75,40,75,5,1),
    },
    "Xbox One Controller": {
        0: (99,44,120,44,0),
        1: (105,37,120,37,0),
        2: (90,38,95,50,0),
        3: (99,31,120,31,0),
        4: (49,23,35,17,2),
        5: (99,23,115,17,0),
        6: (49,23,45,8,0),
        7: (99,23,105,8,0),
        8: (68,37,61,15,1),
        9: (81,37,89,15,1),
        10: (55,36,30,30,2),
        11: (86,48,90,60,0),
        12: (61,47,40,40,2),
        13: (61,55,40,60,2),
        14: (57,50,40,50,2),
        15: (68,52,65,70,2),
        16: (75,28,75,5,1),
    },
    "Xbox Series Controller": {
        0: (99,44,120,44,0),
        1: (105,37,120,37,0),
        2: (90,38,95,50,0),
        3: (99,31,120,31,0),
        4: (49,23,35,17,2),
        5: (99,23,115,17,0),
        6: (49,23,45,8,0),
        7: (99,23,105,8,0),
        8: (68,37,61,15,1),
        9: (81,37,89,15,1),
        10: (55,36,30,30,2),
        11: (86,48,90,60,0),
        12: (61,47,40,40,2),
        13: (61,55,40,60,2),
        14: (57,50,40,50,2),
        15: (68,52,65,70,2),
        16: (75,28,75,5,1),
        17: (75,50,75,70,1),
    },
    "Xbox Adaptive Controller": {
        0: (105,50,0,0,0),
        1: (113,43,0,0,0),
        2: (80,30,100,5,0),
        3: (80,35,100,15,0),
        4: (80,40,100,25,0),
        5: (80,35,100,35,0),
        6: (80,50,100,45,0),
        7: (80,55,100,55,0),
        8: (80,60,100,65,0),
        9: (80,65,100,75,0),
        10: (80,70,100,85,0),
        11: (80,75,100,95,0),
        12: (61,47,40,40,2),
        13: (61,55,40,60,2),
        14: (57,50,40,50,2),
        15: (68,52,65,62,2),
        16: (75,48,0,0,0),
        17: (0,0,0,0,0),
    }
}