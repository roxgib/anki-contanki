from collections import defaultdict

from funcs import get_dark_mode, get_file

# Need to refactor to easily support other controllers

def get_svg(svg_content):
        theme = "FFFFFF" if get_dark_mode() else "000000"

        svg = f"""<svg viewBox="50 0 250 90" version="1.1">
                    <g transform="translate(60)" fill="#{theme}" stroke="#{theme}" font-family="Noto Sans JP" font-size="5px" stroke-width="0.5">
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