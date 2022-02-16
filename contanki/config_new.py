from aqt import QButtonGroup, QComboBox, QLayout, QListWidget, QPoint, mw
from aqt.qt import QDialog, QWidget, QPushButton, QRadioButton, QCheckBox, QHBoxLayout, QVBoxLayout, QTabWidget, QGroupBox
from aqt.qt import QKeySequenceEdit, QLineEdit, QSpinBox, QLabel, QGridLayout
from aqt.qt import Qt
from aqt.webview import AnkiWebView
from aqt.theme import theme_manager

from .svg import *
from .profile import *
from .funcs import *

class ContankiConfig(QDialog):
    def __init__(self, parent: QWidget = mw) -> None:
        super().__init__(parent)
        self.setWindowTitle("Contanki Options")
        self.setFixedWidth(800)
        self.setFixedHeight(660)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.mappings = build_mappings(mw.addonManager.getConfig(__name__)['mappings'])
        self.svg = build_svg_mappings(self.mappings)
        self.options = mw.addonManager.getConfig(__name__)['options']
        self.actions = func_map.keys()
        
        self.layout = QVBoxLayout(self)
        self.tabBar = QTabWidget()
        self.tabs = dict()
        self.setupOptions()
        self.setupBindings()
        
        self.layout.addWidget(self.tabBar)
        
        self.updateButton = QPushButton(self)
        self.updateButton.setText('Update')
        self.updateButton.clicked.connect(self.updateContents)
        self.layout.addWidget(self.updateButton)
        self.setLayout(self.layout)
        self.open()

    def setupOptions(self):
        tab = QWidget()
        self.tabs['main'] = tab
        tab.layout = QGridLayout(self)
        tab.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        main                    = QWidget()
        mouse                   = QWidget()
        flags                   = QGroupBox('Flags', self.tabs['main'])
        advanced                = QGroupBox('Advanced', self.tabs['main'])

        main.layout             = QVBoxLayout()
        mouse.layout            = QGridLayout()
        flags.layout            = QVBoxLayout()
        advanced.layout         = QVBoxLayout()
        
        _profiles = QWidget()
        _profiles.layout = QHBoxLayout()
        profiles = QComboBox(tab)
        profiles.addItems(getProfileList(pretty=True))
        _profiles.layout.addWidget(QLabel("Profile", tab))
        _profiles.layout.addWidget(profiles)
        _profiles.setLayout(_profiles.layout)

        profile_buttons = QWidget()
        profile_buttons.layout = QHBoxLayout()
        profile_buttons.layout.addWidget(QPushButton('Add Profile', tab))
        profile_buttons.layout.addWidget(QPushButton('Delete Profile', tab))
        profile_buttons.layout.addWidget(QPushButton('Copy Profile', tab))
        profile_buttons.setLayout(profile_buttons.layout)

        main.layout.addWidget(_profiles)
        main.layout.addWidget(profile_buttons)
        
        mouse.layout.addWidget(QLabel("Cursor Speed", tab), 0, 0)
        mouse.layout.addWidget(QSpinBox(tab), 0, 1)
        mouse.layout.addWidget(QLabel("Cursor Acceleration", tab), 1, 0)
        mouse.layout.addWidget(QSpinBox(tab), 1, 1)
        mouse.layout.addWidget(QLabel("Scroll Speed", tab), 2, 0)
        mouse.layout.addWidget(QSpinBox(tab), 2, 1)
        
        for flag in mw.flags.all():
            check = QCheckBox(flag.label, self.tabs['main'])
            check.setIcon(theme_manager.icon_from_resources(flag.icon))
            flags.layout.addWidget(check)
        
        advanced.layout.addWidget(QCheckBox('Enable Overlays', tab))
        advanced.layout.addWidget(QCheckBox('Review Tooltips', tab))
        advanced.layout.addWidget(QCheckBox("Enable Dialog/Menu Access", self.tabs['main']))
        advanced.layout.addWidget(QCheckBox("Enable Unsupported Controllers", self.tabs['main']))
        polling_rate = QWidget()
        polling_rate.layout = QHBoxLayout()
        polling_rate.layout.addWidget(QLabel("Polling Rate"))
        _polling_rate = QSpinBox(tab)
        _polling_rate.setSuffix('ms')
        _polling_rate.setValue(50)
        polling_rate.layout.addWidget(_polling_rate)
        polling_rate.setLayout(polling_rate.layout)
        advanced.layout.addWidget(polling_rate)

        main.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        main.setLayout(main.layout)
        mouse.setLayout(mouse.layout)
        flags.setLayout(flags.layout)
        advanced.setLayout(advanced.layout)
        
        self.tabs['main'].layout.addWidget(main, 0, 0)
        self.tabs['main'].layout.addWidget(mouse, 0, 1)
        self.tabs['main'].layout.addWidget(flags, 1, 0)
        self.tabs['main'].layout.addWidget(advanced, 1, 1)

        tab.setLayout(tab.layout)
        self.tabBar.addTab(tab, "Options")

    def setupBindings(self):
        tab = self.tabs['bindings'] = QTabWidget()
        corner = self.corner = QComboBox()
        for controller in getControllerList(True):
            self.corner.addItem(controller, controller)
        controller = mw.controller.profile
        self.corner.setCurrentIndex(getControllerList(False).index(controller))
        self.corner.currentIndexChanged.connect(self.updateContents)
        self.tabs['bindings'].setCornerWidget(self.corner)

        states = {
            "all": "Default",
            "deckBrowser": "Deck Browser", 
            "overview": "Deck Overview", 
            "review": "Review",
            "question": "Question", 
            "answer": "Answer",
            "dialog": "Dialogs",
        }

        mods = {
            "L2": "Left Trigger",
            "": "Default",
            "R2": "Right Trigger",
        }

        def add_buttons(widget):
            widget.buttons = list()
            for control, loc in CONTROLLER_IMAGE_MAPS[controller]['BUTTONS'].items():
                # x, y = loc[2] * 5, loc[3] * 5
                # x += (x - 375) * 0.5
                # y += (y - 375) * 0.5
                # x -= loc[4] * 16

                x, y = loc[2] * 4.58, loc[3] * 4.8
                x += (x - 375) * 0.12
                x -= loc[4] * 16

                widget.buttons.append(QComboBox(widget))
                widget.buttons[-1].addItems(self.actions)
                widget.buttons[-1].setObjectName(str(control))
                widget.buttons[-1].move(QPoint(x, y))
            for control, loc in CONTROLLER_IMAGE_MAPS[controller]['AXES'].items():
                # x, y = loc[2] * 5, loc[3] * 5
                # x -= loc[4] * 16

                x, y = loc[2] * 4.58, loc[3] * 4.8
                x += (x - 375) * 0.12
                x -= loc[4] * 16

                widget.buttons.append(QComboBox(widget))
                widget.buttons[-1].addItems(self.actions)
                widget.buttons[-1].setObjectName(str(100 + control))
                widget.buttons[-1].move(QPoint(x, y))

        tab.states = list()
        for state, title in states.items():
            tab.states.append(QTabWidget())
            tab.states[-1].widgets = list()
            for mod, mTitle in mods.items():
                tab.states[-1].widgets.append(QWidget())
                tab.states[-1].widgets[-1].layout = QVBoxLayout()
                tab.states[-1].widgets[-1].web = AnkiWebView(tab.states[-1].widgets[-1])
                tab.states[-1].widgets[-1].web.setHtml(self.build_html(controller))
                tab.states[-1].widgets[-1].layout.addWidget(tab.states[-1].widgets[-1].web)
                tab.states[-1].widgets[-1].setLayout(tab.states[-1].widgets[-1].layout)
                add_buttons(tab.states[-1].widgets[-1])
                tab.states[-1].addTab(tab.states[-1].widgets[-1], mTitle)
            tab.states[-1].setTabPosition(QTabWidget.TabPosition.South)
            tab.states[-1].setCurrentIndex(1)
            tab.addTab(tab.states[-1], title)

        self.tabBar.addTab(tab, "Controls")

    def updateContents(self):
        tab = self.tabs['bindings']
        corner = self.corner
        controller = getControllerList()[corner.currentIndex()]

        for state in tab.states:
            for widget in state.widgets:
                widget.web.setHtml(self.build_html(controller))
                for button in widget.buttons:
                    name = int(button.objectName())
                    try:
                        loc = CONTROLLER_IMAGE_MAPS[controller]['BUTTONS' if name < 100 else 'AXES'][name if name < 100 else name - 100]
                        x, y = loc[2] * 4.58, loc[3] * 4.8
                        x += (x - 375) * 0.12
                        x -= loc[4] * 16
                        button.move(QPoint(x, y))
                    except KeyError:
                        x, y = 1000, 1000
                    button.move(QPoint(x, y))


    def build_html(self, controller = 'DualShock4'):
        svg = buildSVG(controller)
        html = f"""
<html>
    <head>
    <style>
    </style>
    </head>
    <body>
        <div width="100%" >
            {svg}
        </div>
    </body>

</head>
"""
        with open('configHTML.html', 'w') as f:
            f.write(html)
        return html