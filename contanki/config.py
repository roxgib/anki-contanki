import json

import jsonschema
import markdown
from jsonschema.exceptions import ValidationError

from aqt import mw
from aqt import QPushButton, QWebEngineView, dialogs
from aqt.qt import QDialog
from aqt.addons import ConfigEditor
from aqt.utils import showInfo, tr, saveSplitter

from .funcs import get_dark_mode
from .svg import *

class ControllerConfigEditor(ConfigEditor):
    def __init__(self, parent, mappings):
        super().__init__(dialogs._dialogs['AddonsDialog'][1], 'ds4_support', mw.addonManager.getConfig(__name__))
        self.parent = parent
        self.mappings = mappings
        self.svg = build_svg_mappings(mappings)
        self.build_html()
        self.web = QWebEngineView(self)
        self.web.setHtml(self.build_html())
        with open('configHTML.html', 'w') as f:
            f.write(self.build_html())
        self.layout().addWidget(self.web)
        self.updateButton = QPushButton(self)
        self.updateButton.setText('Update')
        self.updateButton.clicked.connect(self.updateContents)
        self.layout().addWidget(self.updateButton)


    def updateContents(self) -> None:
        txt = self.form.editor.toPlainText()
        try:
            new_conf = json.loads(txt)
            jsonschema.validate(new_conf, self.mgr._addon_schema(self.addon))
        except ValidationError as e:
            schema = e.schema
            erroneous_conf = new_conf
            for link in e.path:
                erroneous_conf = erroneous_conf[link]
            path = "/".join(str(path) for path in e.path)
            if "error_msg" in schema:
                msg = schema["error_msg"].format(
                    problem=e.message,
                    path=path,
                    schema=str(schema),
                    erroneous_conf=erroneous_conf,
                )
            else:
                msg = tr.addons_config_validation_error(
                    problem=e.message,
                    path=path,
                    schema=str(schema),
                )
            showInfo(msg)
            return
        except Exception as e:
            showInfo(f"{tr.addons_invalid_configuration()} {repr(e)}")
            return

        if not isinstance(new_conf, dict):
            showInfo(tr.addons_invalid_configuration_top_level_object_must())
            return

        if new_conf != self.conf:
            self.mgr.writeConfig(self.addon, new_conf)
            # does the add-on define an action to be fired?
            act = self.mgr.configUpdatedAction(self.addon)
            if act:
                act(new_conf)

        saveSplitter(self.form.splitter, "addonconf")
        self.mappings = self.parent.update_config()
        self.svg = build_svg_mappings(self.mappings)
        self.web.setHtml(self.build_html())


    def build_html(self):
        def build_tab(id: str, name: str, top: bool) -> str:
            return f"""<button class="{'statelinks' if top else 'modlinks'}" onclick="{'openState' if top else 'openMap'}(event, '{id}')">{name}</button>"""

        def build_tab_content(state: str, mod: str) -> str:
            return f"""
<div id="{state}{mod}z" class="tabcontent" width = "80%">
    {get_svg(self.svg[state][mod])}
</div>
"""
        contents = '<div class="statetabs">'
        for state in self.mappings:
            contents += '\n'
            contents += build_tab(state, state, True)
        contents += '\n</div>'

        for state in self.mappings:
            contents += '\n'
            contents += f'<div id="{state}" class="modtabs {state}">'
            for mod in ['','R2','L2']:
                contents += '\n'
                contents += build_tab(f'{state}{mod}z', mod if mod else 'Base', False)
            contents += '\n'
            for mod in ['R2', 'L2', '']:
                contents += '\n'
                contents += build_tab_content(state, mod)
                contents += '\n'
            contents += '\n</div>'

        javascript = self.get_javascript()

        css = self.get_css()

        html = f"""
<html>
    <head>
    <style>
    {css}
    </style>
    </head>
    <body>
        <div position="fixed" bottom="0" width="100%">
            {contents}
        </div>
    </body>
    {javascript}
</head>
"""
        return html


    def get_javascript(self) -> str:
        js = """ 
    <script>
    function openState(evt, name) {
        var i, tabcontents, tablinks;

        tabcontents = document.getElementsByClassName("modtabs");
        for (i = 0; i < tabcontents.length; i++) {
            tabcontents[i].style.display = "none";
        }

        tablinks = document.getElementsByClassName("statelinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }

        document.getElementById(name).style.display = "block";
        evt.currentTarget.className += " active";
    }

    function openMap(evt, name) {
        var i, tabcontents, tablinks;

        tabcontents = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontents.length; i++) {
            tabcontents[i].style.display = "none";
        }

        tablinks = document.getElementsByClassName("modlinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }

        document.getElementById(name).style.display = "block";
        evt.currentTarget.className += " active";
    }
    </script>
"""
        return js


    def get_css(self) -> str:
        theme = "333333" if get_dark_mode() else "bbbbbb"

        css = f"""
            html {{
            height:100%;
            background-color: #{theme}
            }}

            .tab {{
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #{theme};
            }}

            .tab button {{
            background-color: inherit;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            }}

            .tab button:hover {{
            background-color: #ddd;
            }}

            .tab button.active {{
            background-color: #ccc;
            }}

            .tabcontent {{
            display: none;
            position: fixed;
            bottom: 0;
            width: 100%;
            }}
            """

        return css



# Dialog manager
##########################################################################
# ensures only one copy of the window is open at once, and provides
# a way for dialogs to clean up asynchronously when collection closes

# to integrate a new window:
# - add it to _dialogs
# - define close behaviour, by either:
# -- setting silentlyClose=True to have it close immediately
# -- define a closeWithCallback() method
# - have the window opened via aqt.dialogs.open(<name>, self)
# - have a method reopen(*args), called if the user ask to open the window a second time. Arguments passed are the same than for original opening.

# - make preferences modal? cmd+q does wrong thing