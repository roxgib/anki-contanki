from aqt import mw
from aqt import gui_hooks
from aqt.qt import QDialog
from aqt.addons import ConfigEditor, AddonsDialog

from .control_map import ControlMap
from .funcs import get_state
from .funcs import get_dark_mode

from aqt import dialogs


class ControllerConfigEditor(ConfigEditor, ControlMap):
    def __init__(self):
        super().__init__(dialogs._dialogs['AddonsDialog'][1], 'ds4_support', mw.addonManager.getConfig(__name__))
        
        self.config = mw.addonManager.getConfig(__name__)

        self.states = {
            "startup":          self.config['startup'],
            "deckBrowser":      self.config['deckBrowser'],
            "overview":         self.config['overview'],
            "profileManager":   self.config['profileManager'],
            'question':         self.config['question'],
            'answer':           self.config['answer'],
        }
        
        self.form.label.setText(self.build_html()) 

    def save_config(self):
        pass

    def load_config(self):
        pass

    def update_contents(self):
        self.form.label.setText(self.build_html()) 

    def build_html(self):
        def build_tab(id, name, level):
            return f"""<button class="{level}" onclick="openTab(event, '{id}')">{name}</button>"""

        def build_tab_content(state, mod):
            return f"""
<div id="{state} | {mod}" class="tabcontent">
    {self.get_svg(state, mod)}
</div>
"""
        contents = '<div class="statetabs">'
        for state in self.states:
            contents += '\n'
            contents += build_tab(state, state, 'statetabs')
        contents += '\n</div>'

        for state in self.states:
            contents += '\n'
            contents += f'<div id="{state}" class="tabcontent">'
            contents += f'<div class="modtabs {state}">'
            for mod in ['R2', 'L2', '']:
                contents += '\n'
                contents += build_tab(f'{state} | {mod}', mod, 'modtabs')
            contents += '\n</div>'
            contents += '\n'
            for mod in ['R2', 'L2', '']:
                contents += '\n'
                contents += build_tab_content(state, mod)
                contents += '\n'
            contents += '</div>'

        javascript = self.get_javascript()

        css = self.get_css()

        html = f"""
<html>
    <head>
    <style>
    {css}
    </style>
    <body height="100%">
        <div position="fixed" bottom="0" width="100%">
            {contents}
        </div>
    </body>
    {javascript}
</head>
"""
        return html

    def get_javascript(self):
        self.js = """ 
<script>
function openTab(evt, name) {
    var i, tabcontents, tablinks;

    tabcontents = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontents.length; i++) {
        tabcontents[i].style.display = "none";
    }

    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";
}
</script>
"""

    def get_css(self):
        theme = "111111" if get_dark_mode() else "eeeeee"

        css = f"""
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
