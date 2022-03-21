from collections import defaultdict
from typing import Any, Dict, Optional

from aqt import mw
from aqt.webview import AnkiWebView

from .funcs import get_state
from .funcs import get_dark_mode
from .svg import *
from .CONSTS import *
from .profile import Profile


class ControlsOverlay(AnkiWebView):
    def __init__(self, parent, path: str, profile: Profile):
        super().__init__(parent=parent)
        self.path = path
        self.svg = build_svg_mappings(profile.getInheritedBindings(), profile.controller)
        self.setFixedWidth(800)
        self.setFixedHeight(400)
        geometry = mw.geometry()
        geometry.setBottom(mw.height() - 70)
        geometry.setTop(mw.height() - self.height() - 70)
        geometry.setLeft((mw.width() - self.width()) // 2)
        geometry.setRight(mw.width() - ((mw.width() - self.width()) // 2))
        self.hide()

    def disappear(self) -> None:
        self.hide()

    def appear(self, mods: tuple) -> None:
        state = get_state()
        if state not in self.svg: return
        geometry = mw.geometry()
        geometry.setBottom(mw.height() - 70)
        geometry.setTop(mw.height() - self.height() - 70)
        geometry.setLeft((mw.width() - self.width()) // 2)
        geometry.setRight(mw.width() - ((mw.width() - self.width()) // 2))
        self.setGeometry(geometry)

        mod = 0 if all(mods) else mods.index(True) + 1

        body = f"""<html width="100%" background-color="#{mw.app.palette().base().color().name()}">
            <body width="100%">
                <div width="100%" >
                    {self.svg[state][mod].replace(
                        "dark", 
                        f'fill="{mw.app.palette().text().color().name()}" stroke="{mw.app.palette().text().color().name()}"')
                        }
                </div>
            </body>
            </html>
            """

        self.stdHtml(body)

    def print_svg(self) -> None:
        for state in self.svg.keys():
            print(state + "\n")
            for mod, s in self.svg[state].items():
                print(mod)
                print("\n")
                print(s)
                print("\n")
                print("\n")