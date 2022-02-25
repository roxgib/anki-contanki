import os
import json

from aqt import mw 
from aqt import QComboBox, QFormLayout, QHeaderView, QKeySequence, QLayout, QPoint, QShortcut
from aqt import QTableWidget, QTableWidgetItem
from aqt.qt import QAction, QDialog, QWidget, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout, QTabWidget
from aqt.qt import QKeySequenceEdit, QSpinBox, QLabel, QGridLayout, QGroupBox, QFont
from aqt.webview import AnkiWebView
from aqt.theme import theme_manager
from aqt.utils import showInfo

from .CONSTS import BUTTON_NAMES
from .svg import buildSVG, CONTROLLER_IMAGE_MAPS
from .profile import createProfile, getControllerList, getControllerName, getProfile, getProfileList, Profile, user_files_path
from .actions import button_actions, state_actions

class ContankiConfig(QDialog):
    def __init__(self, parent: QWidget, profile: Profile) -> None:
        if not profile:
            showInfo("Controller not detected. Connect using Bluetooth or USB, and press any button to initialise.")
        
        super().__init__(parent)
        self.setWindowTitle("Contanki Options")
        self.setFixedWidth(800)
        self.setFixedHeight(660)

        self.profile = profile
        self.layout = QVBoxLayout(self)
        self.tabBar = QTabWidget()
        self.tabs = dict()
        self.setupOptions()
        self.setupBindings()
        
        self.saveButton = QPushButton(self)
        self.cancelButton = QPushButton(self)
        self.helpButton = QPushButton(self)

        self.saveButton.setText('Save')
        self.cancelButton.setText('Cancel')
        self.helpButton.setText('Help')
        
        self.saveButton.clicked.connect(self.save)
        self.cancelButton.clicked.connect(self.close)
        self.helpButton.clicked.connect(self.help)

        self.buttons = QWidget()
        self.buttons.layout = QHBoxLayout()

        self.buttons.layout.addWidget(self.helpButton)
        self.buttons.layout.addWidget(self.cancelButton)
        self.buttons.layout.addWidget(self.saveButton)
        
        self.buttons.layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.buttons.setLayout(self.buttons.layout)
        
        self.layout.addWidget(self.tabBar)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
        self.open()


    def save(self) -> None:
        for key in self.options.keys():
            if type(self._options[key]) == int:
                self._options[key] = self.options[key].value()
            elif type(self._options[key]) == bool:
                self._options[key] = self.options[key].isChecked()
            elif key == "Custom Actions":
                for row in range(self.options[key].rowCount()):
                    self._options[self.options[key].item(row, 0).text()] = self.options[key].cellWidget(row, 1).keySequence().toString()
            elif key == "Flags":
                self._options["Flags"] = []
                for flag in self.options[key].findChildren(QCheckBox):
                    if flag.isChecked():
                        self._options["Flags"].append(int(flag.objectName()))

        mw.addonManager.writeConfig(__name__, self._options)

        states = [
            "all",
            "deckBrowser",
            "overview",
            "review",
            "question",
            "answer",
            "dialog",
        ]

        mods = {0:"Default"}
        if self.profile.controller in BUTTON_NAMES:
            for i, mod in enumerate(self.profile.mods):
                mods[i+1] = BUTTON_NAMES[self.profile.controller][mod]
        else:
            for i, mod in enumerate(self.profile.mods):
                mods[i+1] = f"Modifier {i+1}"

        controls = self.tabs['bindings']

        for key in range(self.profile.size[1]):
            self.profile.axes_bindings[key] = self.axes_bindings[key].currentText()

        for state in states:
            for mod, title in mods.items():
                for button in range(self.profile.size[0]):
                    if button in self.profile.mods:
                        continue
                    action = controls.stateTabs[state].modTabs[mod].controls[button].currentText()
                    if 'inherit' in action:
                        action = ""
                    self.profile.updateBinding(state, mod, button, action, build_actions=False)
                # for axis in range(self.profile.size[1]):
                #     if button in self.profile.mods:
                #         continue
                #     _axis = axis + self.profile.size[0]
                #     action = controls.stateTabs[state].modTabs[mod].controls[_axis].currentText()
                #     if 'inherited' in action:
                #         action = ""
                #     self.profile.updateBinding(state, mod, axis=axis, action=action, build_actions=False)

        self.profile.buildActions()
        mw.controller.profile = self.profile
        self.profile.save()

        with open(os.path.join(user_files_path, 'controllers'), 'r') as f:
            controllers = json.load(f)

        controllers[self.profile.controller] = self.profile.name

        with open(os.path.join(user_files_path, 'controllers'), 'w') as f:
            json.dump(controllers, f)

        self.close()


    def help(self) -> None:
        pass

    
    def changeProfile(self, profile: Profile = None) -> None:
        if not profile:
            profile = getProfile(self._profile.currentText())
        elif type(profile) == str:
            profile = getProfile(profile)
        if not profile:
            return
        self.profile = profile
        self.tabBar.removeTab(1)
        self.setupBindings()


    def findCustomActions(self) -> None:
        shortcuts = [shortcut for name, shortcut in self._options["Custom Actions"].items()]
        for action in mw.findChildren(QAction):
            if (scut := action.shortcut().toString()) != "" and scut not in shortcuts:
                if action.objectName() != "":
                    self._options["Custom Actions"][action.objectName()] = scut
                else:
                    self._options["Custom Actions"][scut] = scut

        for scut in mw.findChildren(QShortcut):
            if scut.key().toString() != "":
                self._options["Custom Actions"][scut.key().toString()] = scut.key().toString()


    def addProfile(self) -> None:
        new_profile = createProfile()
        if not new_profile: return
        self._profile.addItem(new_profile.name)
        self._profile.setCurrentIndex(-1)
        self.changeProfile(new_profile)


    def setupOptions(self) -> None:
        tab = QWidget()
        self.tabs['main'] = tab
        tab.layout = QGridLayout(tab)
        tab.layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)

        main                    = QWidget()
        mouse                   = QWidget()
        flags                   = QGroupBox('Flags', self.tabs['main'])
        form                    = QWidget()

        main.layout             = QVBoxLayout()
        mouse.layout            = QGridLayout()
        flags.layout            = QFormLayout()
        form.layout             = QFormLayout()
        
        _profiles = QWidget()
        _profiles.layout = QHBoxLayout()
        self._profile = profiles = QComboBox(tab)
        profiles.addItems(getProfileList(pretty=True))
        profiles.setCurrentIndex(getProfileList(pretty=True).index(self.profile.name))
        profiles.currentTextChanged.connect(self.changeProfile)
        _profiles.layout.addWidget(QLabel("Profile", tab))
        _profiles.layout.addWidget(profiles)
        
        addButton = QPushButton('Add Profile', tab)
        addButton.clicked.connect(self.addProfile)
        _profiles.layout.addWidget(addButton)
        _profiles.layout.addWidget(QPushButton('Delete Profile', tab))
        _profiles.layout.addWidget(QPushButton('Rename Profile', tab))
        _profiles.setLayout(_profiles.layout)

        self._options = mw.addonManager.getConfig(__name__)
        self.findCustomActions()
        self.options = dict()

        flags.layout.setVerticalSpacing(20)
        form.layout.setVerticalSpacing(20)

        for key, value in self._options.items():
            if type(value) == int:
                self.options[key] = QSpinBox(tab)
                self.options[key].setMinimumWidth(70)
                self.options[key].setValue(value)
                form.layout.addRow(key, self.options[key])
            elif type(value) == bool:
                self.options[key] = QCheckBox(key, tab)
                self.options[key].setChecked(self._options[key])
                form.layout.addRow(self.options[key])
            elif key == "Custom Actions":
                self.options[key] = QTableWidget(len(value),2,tab)
                self.options[key].setHorizontalHeaderLabels(["Name", "Shortcut"])
                for row, (_key, _value) in enumerate(value.items()):
                    self.options[key].setItem(row, 0, QTableWidgetItem(_key,0))
                    self.options[key].setCellWidget(row, 1, QKeySequenceEdit(QKeySequence(_value)))
                self.options[key].horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
                self.options[key].setColumnWidth(1, 70)
                tab.layout.addWidget(self.options[key],1,2)
            elif key == "Flags":
                self.options[key] = flags
                for flag in mw.flags.all():
                    check = QCheckBox(flag.label, tab)
                    check.setIcon(theme_manager.icon_from_resources(flag.icon))
                    check.setObjectName(str(flag.index))
                    if flag.index in self._options["Flags"]:
                        check.setChecked(True)
                    flags.layout.addWidget(check)
                flags.setLayout(flags.layout)
                tab.layout.addWidget(self.options[key],1,1)
            else: continue

        self.axes_bindings = list()
        for axis, value in self.profile.axes_bindings.items():
            button = QComboBox()
            button.addItems([
                "Unassigned", 
                "Buttons",
                "Cursor Horizontal",
                "Cursor Vertical",
                "Scroll Horizontal",
                "Scroll Vertical",
            ])
            button.setCurrentText(value)
            self.axes_bindings.append(button)
            form.layout.addRow(f"Axis {axis}", button)

        form.setLayout(form.layout)
        tab.layout.addWidget(_profiles,0,0,1,3)
        tab.layout.addWidget(form,1,0)
        
        tab.setLayout(tab.layout)
        self.tabBar.addTab(tab, "Options")


    def setupBindings(self) -> None:
        tab = self.tabs['bindings'] = QTabWidget()
        
        corner = self.corner = QComboBox()
        controllers = getControllerList()
        for controller in controllers:
            corner.addItem(getControllerName(controller), controller)
        controller = None # need to set up proper controller detection
        if controller:
            corner.setCurrentIndex(controllers.index(controller))
        else:
            corner.setCurrentIndex(0)
            self.profile.controller = corner.currentData()
        self.profile.controller = controller = corner.currentData()
        corner.currentIndexChanged.connect(self.updateContents)
        self.tabs['bindings'].setCornerWidget(corner)


        states = {
            "all": "Default",
            "deckBrowser": "Deck Browser", 
            "overview": "Deck Overview", 
            "review": "Review",
            "question": "Question", 
            "answer": "Answer",
            "dialog": "Dialogs",
        }

        mods = {0:"Default"}
        if controller in BUTTON_NAMES:
            for i, mod in enumerate(self.profile.mods):
                mods[i+1] = BUTTON_NAMES[controller][mod]
        else:
            for i, mod in enumerate(self.profile.mods):
                mods[i+1] = f"Modifier {i+1}"

        def addButtons(widget, state, mod, control, loc, axis = False):
            x, y = loc[2] * 4.58, loc[3] * 4.8
            x += (x - 375) * 0.12
            if control in self.profile.mods:
                y -= 5
                button = QLabel(f'<b>{mods[self.profile.mods.index(control) + 1]}</b>' if mod == self.profile.mods.index(control) + 1 else mods[self.profile.mods.index(control) + 1], widget)
                button.setFont(QFont("Helvetica", 15))
            else:
                x -= loc[4] * 40
                button = QComboBox(widget)
                button.addItems(state_actions[state])
                if str(control + 100 if axis else control) in self.profile.bindings[state][mod]:
                    button.setCurrentIndex(state_actions[state].index(self.profile.bindings[state][mod][str(control + 100 if axis else control)]))
                if state == "question" or state == "answer":
                    if button.currentIndex() == 0:
                        if str(control + 100 if axis else control) in self.profile.bindings['review'][mod]:
                            inherited = self.profile.bindings["review"][mod][str(
                                    control + 100 if axis else control
                                )]
                            if inherited != "":
                                button.addItem(inherited + " (inherited)")
                                button.setCurrentText(inherited + " (inherited)")
                if button.currentIndex() == 0:
                    if str(control + 100 if axis else control) in self.profile.bindings['all'][mod]:
                        inherited = self.profile.bindings["all"][mod][str(
                                    control + 100 if axis else control
                                )]
                        if inherited != "":
                                button.addItem(inherited + " (inherited)")
                                button.setCurrentText(inherited + " (inherited)")
                        

                button.setFixedWidth(150)
            button.setObjectName(str(control + 100 if axis else control))
            widget.controls.append(button)
            button.move(QPoint(x, y))

        tab.stateTabs = dict()
        for state, title in states.items():
            tab.stateTabs[state] = (QTabWidget())
            tab.stateTabs[state].setObjectName(state)
            tab.stateTabs[state].modTabs = dict()
            for mod, mTitle in mods.items():
                tab.stateTabs[state].modTabs[mod] = QWidget()
                tab.stateTabs[state].modTabs[mod].setObjectName(str(mod))
                tab.stateTabs[state].modTabs[mod].layout = QVBoxLayout()
                tab.stateTabs[state].modTabs[mod].web = AnkiWebView(tab.stateTabs[state].modTabs[mod])
                tab.stateTabs[state].modTabs[mod].web.setHtml(self.build_html(self.profile.controller))
                tab.stateTabs[state].modTabs[mod].layout.addWidget(tab.stateTabs[state].modTabs[mod].web)
                tab.stateTabs[state].modTabs[mod].setLayout(tab.stateTabs[state].modTabs[mod].layout)
                tab.stateTabs[state].modTabs[mod].controls = list()
                for control, loc in CONTROLLER_IMAGE_MAPS[controller]['BUTTONS'].items():
                    addButtons(tab.stateTabs[state].modTabs[mod], state, mod, control, loc)
                for control, loc in CONTROLLER_IMAGE_MAPS[controller]['AXES'].items():
                    addButtons(tab.stateTabs[state].modTabs[mod], state, mod, control, loc, True)
                tab.stateTabs[state].addTab(tab.stateTabs[state].modTabs[mod], mTitle)
            tab.stateTabs[state].setTabPosition(QTabWidget.TabPosition.South)
            tab.addTab(tab.stateTabs[state], title)
        self.tabBar.addTab(tab, "Controls")


    def updateContents(self) -> None:
        tab = self.tabs['bindings']
        corner = self.corner
        controller = getControllerList()[corner.currentIndex()]
        for state, d in tab.stateTabs.items():
            for widget, e in d.modTabs.items():
                e.web.setHtml(self.build_html(controller))
                for button in e.controls:
                    index = int(button.objectName())
                    index, control = (index, 'BUTTONS') if index < 100 else (index - 100, 'AXES')
                    try:
                        loc = CONTROLLER_IMAGE_MAPS[controller][control][index]
                        x, y = loc[2] * 4.58, loc[3] * 4.8
                        x += (x - 375) * 0.12
                        x -= loc[4] * 16
                        button.move(QPoint(x, y))
                    except KeyError:
                        x, y = 1000, 1000
                    button.move(QPoint(x, y))
        self.profile.controller = corner.currentData()


    def build_html(self, controller: str) -> str:
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