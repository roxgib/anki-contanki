from collections import defaultdict
from typing import Any, Dict, Optional

from aqt import mw
from aqt.webview import AnkiWebView

from .funcs import get_state
from .funcs import get_dark_mode
from .svg import *
from .CONSTS import BUTTONS

class ControlsOverlay(AnkiWebView):
    def __init__(self, parent, path: str, bindings: dict, controller:str = 'DS4'):
        super().__init__(parent=parent)
        self.path = path
        self.svg = build_svg_mappings(bindings, controller)
        self.setFixedWidth(800)
        self.setFixedHeight(330)
        geometry = mw.geometry()
        geometry.setBottom(mw.height() - 70)
        geometry.setTop(mw.height() - self.height() - 70)
        geometry.setLeft((mw.width() - self.width()) // 2)
        geometry.setRight(mw.width() - ((mw.width() - self.width()) // 2))
        self.hide()

    def disappear(self) -> None:
        self.hide()

    def appear(self, mod: str) -> None:
        state = get_state()
        if state not in self.svg: return
        geometry = mw.geometry()
        geometry.setBottom(mw.height() - 70)
        geometry.setTop(mw.height() - self.height() - 70)
        geometry.setLeft((mw.width() - self.width()) // 2)
        geometry.setRight(mw.width() - ((mw.width() - self.width()) // 2))
        self.setGeometry(geometry)

        if mod == "L2 + R2":
            mod = ""

        body = f"""<html style="background-color: #{mw.app.palette().base().color().name()}"><body><div class="text-block" min-height="100%" style="text-align:center">
                    <div position="fixed" bottom="0" width="100%">
                    {get_svg(self.svg[state][mod], mw.app.palette().text().color().name())}
                    </div></body></html>"""

        self.stdHtml(body)

    def print_svg(self):
        # for state in mw.controller.controlsOverlay.svg.keys():
        for state in self.svg.keys():
            print(state + "\n")
            for mod, s in self.svg[state].items():
                print(mod)
                print("\n")
                print(s)
                print("\n")
                print("\n")