"""
Contanki's configuration dialog and associated classes.
"""

from __future__ import annotations
from collections import defaultdict
from copy import deepcopy

from functools import partial
from sre_parse import State
from typing import Any, Callable, Type

from aqt import mw, qconnect
from aqt.qt import QTableWidget, QTableWidgetItem, QComboBox, QFormLayout, QHeaderView
from aqt.qt import (
    QDialog,
    QWidget,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
    QIcon,
    QInputDialog,
    QKeySequenceEdit,
    QSpinBox,
    QLabel,
    QGridLayout,
    QGroupBox,
    Qt,
    QKeySequence,
    QLayout,
    QSizePolicy,
    QStyle,
)
from aqt.theme import theme_manager
from aqt.utils import showInfo, getText

from .funcs import get_debug_str
from .mappings import BUTTON_NAMES, AXES_NAMES
from .profile import (
    Profile,
    create_profile,
    delete_profile,
    get_controller_list,
    get_profile,
    get_profile_list,
    update_controllers,
)
from .actions import state_actions
from .icons import ControlButton, get_button_icon

states = {
    "all": "Default",
    "deckBrowser": "Deck Browser",
    "overview": "Deck Overview",
    "review": "Review",
    "question": "Question",
    "answer": "Answer",
    "dialog": "Dialogs",
}


class ContankiConfig(QDialog):
    """Contanki's config dialog.

    Allows the user to change the profile, settings, and bindings."""

    def __init__(self, parent: QWidget, profile: Profile) -> None:
        assert mw is not None
        if profile is None:
            showInfo(
                "Controller not detected. Connect your controller and press any button to initialise."  # pylint: disable=line-too-long
            )
            return

        # Initialise internal variables
        self.profile = profile.copy()
        self.controller = self.profile.controller
        self.to_delete: list[str] = list()

        # Initialise dialog
        super().__init__(parent)
        self.setWindowTitle("Contanki Options")
        self.setObjectName("Contanki Options")
        self.setFixedWidth(800)
        self.setMinimumHeight(660)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Initialise main tabs (Options, Controls)
        self.tab_bar = QTabWidget()
        self.options_page = OptionsPage(self)
        self.tab_bar.addTab(self.options_page, "Options")
        self.controls_page = ControlsPage(self)
        self.tab_bar.addTab(self.controls_page, "Controls")
        layout.addWidget(self.tab_bar)
        qconnect(
            self.controls_page.controller_dropdown.currentIndexChanged,
            self.options_page.update,
        )

        # Add buttons
        _buttons = [
            Button(self, "Save", self.save),
            Button(self, "Cancel", self.close),
            Button(self, "Help", self.help),
        ]
        buttons = Container(self, QHBoxLayout, _buttons)
        buttons.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.addWidget(buttons)

        # Open
        self.setLayout(layout)
        self.resize(self.sizeHint())
        self.open()

    def save(self) -> None:
        """Save changes, and load them. Used on close."""
        assert mw is not None
        options = self.options_page.get()
        mw.addonManager.writeConfig(__name__, options)

        for profile in self.to_delete:
            delete_profile(profile)

        for i, role in enumerate(self.axes_roles):
            self.profile.axes_bindings[i] = role

        self.profile.controller = self.controls_page.controller_dropdown.currentText()
        self.profile.save()
        update_controllers(self.controller, self.profile.name)
        mw.contanki.update_profile(self.profile)
        self.close()

    def help(self) -> None:
        """Open the Contanki help page."""
        showInfo(get_debug_str(), textFormat="rich")

    # FIXME: Switching profiles currently deletes changes to the previous profile
    def change_profile(self, profile: Profile = None) -> None:
        """Used when the user changes the profile in the profile list.

        Will only update the main profile if Save is chosen."""
        if isinstance(profile, str):
            profile = get_profile(profile)
        elif not profile or isinstance(profile, Profile):
            profile = get_profile(self.profile_combo.currentText())
        if not profile:
            return
        self.profile = profile
        self.options_page.update()
        self.controls_page.update()

    def get_custom_actions(self) -> list[str]:
        """Get the names of custom actions."""
        return self.options_page.custom_actions.get_actions()

    def update_binding(
        self, state: State, mod: int, button: int, index: int
    ) -> None:
        """Update the binding for the given button."""
        action = self.controls_page.get_action(state, mod, button)
        if action == 0:
            action = ""
        self.profile.update_binding(state, mod, button, action)
        if state in ("all", "review"):
            self.controls_page.update_inheritance()

    def update_controls_page(self):
        """Update the controls page."""
        try:
            self.controls_page.update()
        except AttributeError:
            pass # Controls pags not initialised yet

    def update_options_page(self):
        """Update the options page."""
        try:
            self.options_page.update()
        except AttributeError:
            pass # Options pags not initialised yet

    # def findCustomActions(self) -> None:
    #     shortcuts = [
    #         shortcut for name, shortcut in self._options["Custom Actions"].items()
    #     ]
    #     for action in mw.findChildren(QAction):
    #         if (scut := action.shortcut().toString()) != "" and scut not in shortcuts:
    #             if action.objectName() != "":
    #                 self._options["Custom Actions"][action.objectName()] = scut
    #             else:
    #                 self._options["Custom Actions"][scut] = scut

    #     for scut in mw.findChildren(QShortcut):
    #         if scut.key().toString() != "":
    #             self._options["Custom Actions"][
    #                 scut.key().toString()
    #             ] = scut.key().toString()


class Button(QPushButton):
    """A button connected to a function."""

    def __init__(self, parent: QWidget, name: str, func: Callable) -> None:
        super().__init__(parent)
        self.setText(name)
        self.setObjectName(name.lower().replace(" ", "_"))
        qconnect(self.clicked, func)


class Container(QWidget):
    """
    A container for other objects. Abstracts away the need to add
    widgets to a layout and apply the layout to a container widget.
    """

    def __init__(
        self, parent: QWidget, layout: Type[QLayout], widgets: list[QWidget]
    ) -> None:
        super().__init__(parent)
        self._layout = layout(self)
        for widget in widgets:
            self._layout.addWidget(widget)
        self.setLayout(self._layout)

    def addWidget(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)


class ControlsPage(QTabWidget):
    """A widget allowing the user to modify the bindings."""

    style_sheet = "QTabWidget::pane { border: 0px; }"

    def __init__(self, parent: ContankiConfig) -> None:
        super().__init__(parent)
        self.setStyleSheet(self.style_sheet)
        self.profile = parent.profile
        self._update_binding = parent.update_binding
        self.custom_actions = parent.get_custom_actions()
        self.setObjectName("controls_page")

        # Controller Selection Dropdown
        self.controller_dropdown = QComboBox(self)
        self.controller_dropdown.addItems(get_controller_list())
        self.controller = self.profile.controller
        self.controller_dropdown.setCurrentText(self.controller)
        self.controller_dropdown.currentIndexChanged.connect(parent.update_options_page)
        self.controller_dropdown.currentIndexChanged.connect(self.update)
        self.setCornerWidget(self.controller_dropdown)

        # Initialise tabs
        self.state_tabs: dict[str, QTabWidget] = dict()
        self.controls: dict[str, dict[int, dict[int, QComboBox]]] = dict()
        self._init_tabs()

        self.update_inheritance()

    def _init_tabs(self) -> None:
        """Initialise the tabs."""
        self.mods = {0: "No Modifier"}
        for i, mod in enumerate(self.profile.mods):
            if mod in BUTTON_NAMES[self.controller]:
                self.mods[i + 1] = BUTTON_NAMES[self.controller][mod]

        for state, state_name in states.items():
            self.state_tabs[state] = state_tab = QTabWidget(self)
            state_tab.setObjectName("state_tab")
            state_tab.mod_tabs: dict[int, QWidget] = dict()
            self.controls[state] = dict()
            for mod, mod_title in self.mods.items():
                state_tab.mod_tabs[mod] = mod_tab = self._init_controls_page(state, mod)
                mod_tab.setObjectName("mod_tab")
                self.controls[state][mod] = mod_tab.controls
                if mod == 0:
                    state_tab.addTab(mod_tab, mod_title)
                else:
                    icon = QIcon(get_button_icon(self.controller, self.mods[mod]))
                    state_tab.addTab(mod_tab, icon, mod_title)
            state_tab.setTabPosition(QTabWidget.TabPosition.South)
            self.addTab(state_tab, state_name)

    def _init_controls_page(self, state: State, mod: int) -> QWidget:
        controls_page = QWidget()
        controls_page.controls: dict[int, ControlButton] = dict()
        layout = QGridLayout()
        row = col = 0
        controller = self.profile.controller
        bindings = defaultdict(
            str,
            {
                (mod, i): action
                for (_state, mod, i), action in self.profile.bindings.items()
                if _state == state
            },
        )
        axes_bindings = self.profile.axes_bindings
        actions = state_actions[state] + self.custom_actions
        update = partial(self.update_binding, state, mod)
        for i, button_name in BUTTON_NAMES[controller].items():
            if i in self.profile.mods:
                continue
            if i >= 100:
                axis = (i - 100) // 2
                if axis > len(axes_bindings) or axes_bindings[axis] != "Buttons":
                    continue
            # FIXME: Add dependency injection to ControlButton init
            control_selector = ControlButton(button_name, controller, actions=actions)
            # Get action directly since inherited actions are added separately
            control_selector.action.setCurrentText(bindings[(mod, i)])
            qconnect(control_selector.action.currentIndexChanged, partial(update, i))
            # FIXME: Add registration to ControlButton init
            mw.contanki.register_icon(i, control_selector)
            layout.addWidget(control_selector, row, col)
            controls_page.controls[i] = control_selector
            col = (col + 1) % 3
            row += not col
        controls_page.setLayout(layout)
        return controls_page

    def update_inheritance(self):
        """Updates action selection dropdowns to reflect inherited values."""
        controls_iter = [
            (state, mod, index, control_button)
            for state, state_dict in self.controls.items()
            if state != "all"
            for mod, control_buttons in state_dict.items()
            for index, control_button in control_buttons.items()
            if index not in state_dict
        ]

        all_bindings = {
            mod: {i: control.currentText() for i, control in controls.items()}
            for mod, controls in self.controls["all"].items()
        }

        review_bindings = {
            mod: {i: control.currentText() for i, control in controls.items()}
            for mod, controls in self.controls["review"].items()
        }

        for state, mod, i, control_button in controls_iter:
            inherited = ""
            if action := all_bindings[mod][i]:
                inherited = action + " (inherited)"
            if state in ("question", "answer") and (action := review_bindings[mod][i]):
                inherited = action + " (inherited)"
            control_button.action.setItemText(0, inherited)

    def update(self):
        """Updates the bindings to reflect the chosen options."""
        self.profile.controller = self.controller_dropdown.currentText()
        for _ in self.state_tabs:
            self.removeTab(0)
        self.state_tabs.clear()
        self.controls.clear()
        self._init_tabs()
        self.update_inheritance()

    def update_binding(self, state: State, mod: int, button: int, _) -> None:
        """Updates the binding for the given state, mod, and index."""
        action =  self.controls[state][mod][button].currentText()
        if "inherit" in action:
            action = ""
        self._update_binding(state, mod, button, action)


class OptionsPage(QWidget):
    """A widget containing the main options."""

    def __init__(self, parent: ContankiConfig) -> None:
        super().__init__(parent)
        self.parent = parent
        self.profile = parent.profile
        self.update_controls_page = parent.update_controls_page
        layout = QGridLayout(parent)
        self.options: dict[str, Any] = dict()
        self.config = mw.addonManager.getConfig(__name__)
        assert self.config is not None

        # Profile Bar
        profile_bar = self.ProfileBar(parent)
        self.profile_combo: QComboBox = profile_bar.profile_combo
        layout.addWidget(profile_bar, 0, 0, 1, 3)

        # Custom Actions
        self.custom_actions = self.CustomActions(
            parent, self, self.config["Custom Actions"]
        )
        layout.addWidget(self.custom_actions, 1, 2)

        # Axes & Flags
        centre_column = QVBoxLayout()
        centre_column.setSpacing(30)
        self.axis_roles = self.AxisRoleSelector(self, self.profile.controller)
        centre_column.addWidget(self.axis_roles)

        self.flags = self.FlagsSelector(self, self.config["Flags"])
        centre_column.addWidget(self.flags)

        layout.addLayout(centre_column, 1, 1)

        # Other Options
        left_column = QVBoxLayout()
        left_column.setSpacing(30)
        form = QGroupBox("Options", self)
        form_layout = QFormLayout(self)
        # form_layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        for key, value in self.config.items():
            if isinstance(value, bool):
                widget = QCheckBox(self)
                widget.setChecked(self.config[key])
            elif isinstance(value, int):
                widget = QSpinBox(self)
                widget.setMinimumWidth(45)
                widget.setValue(value)
            else:
                continue
            form_layout.addRow(key, widget)
            self.options[key] = widget
        form.setLayout(form_layout)
        left_column.addWidget(form, alignment=Qt.AlignmentFlag.AlignTop)

        # Modifier Selectors
        self.mod_selector = self.ModSelectors(parent)
        left_column.addWidget(self.mod_selector, alignment=Qt.AlignmentFlag.AlignTop)

        layout.addLayout(left_column, 1, 0, alignment=Qt.AlignmentFlag.AlignTop)

        # Finish
        self.setLayout(layout)

    def get(self) -> dict:
        """Returns the currently selected options."""
        options = dict()
        for key, option in self.options.items():
            if isinstance(self.config[key], int):
                options[key] = option.value()
            elif isinstance(self.config[key], bool):
                options[key] = option.isChecked()
        options["Custom Actions"] = self.custom_actions.get()
        options["Flags"] = self.flags.get()
        return options

    def update(self):
        """Updates page to reflect user changess, such as the selected controller."""
        self.mod_selector.update()
        self.axis_roles.update()

    class ProfileBar(QWidget):
        """A widget allowing the user to change, rename, or delete profiles."""

        def __init__(self, parent: ContankiConfig) -> None:
            super().__init__(parent)
            layout = QHBoxLayout()
            layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
            self.profile = parent.profile
            self.to_delete = parent.to_delete

            self.profile_combo = QComboBox(self)
            self.profile_combo.addItems(p_list := get_profile_list(defaults=False))
            self.profile_combo.setCurrentIndex(p_list.index(self.profile.name))
            self.profile_combo.currentTextChanged.connect(parent.change_profile)

            for widget in (
                QLabel("Profile", self),
                self.profile_combo,
                Button(self, "Add Profile", self.add_profile),
                Button(self, "Rename Profile", self.rename_profile),
                Button(self, "Delete Profile", self.delete_profile),
            ):
                layout.addWidget(widget)
            self.setLayout(layout)

        def add_profile(self) -> None:
            """Add a new profile."""
            old, okay1 = QInputDialog().getItem(
                self,
                "Create New Profile",
                "Select an existing profile to copy:",
                get_profile_list(),
                editable=False,
            )
            if not (okay1 and old):
                return
            name, okay2 = QInputDialog().getText(
                self, "Create New Profile", "Enter the new profile name:"
            )
            if not (name and okay2):
                return
            new_profile = create_profile(old, name)
            if new_profile is None:
                return
            self.profile_combo.addItem(new_profile.name)
            self.profile_combo.setCurrentText(new_profile.name)

        def delete_profile(self) -> None:
            """Delete the current profile."""
            if len(self.profile_combo) == 1:
                showInfo("You can't delete the last profile")
                return
            self.to_delete.append(self.profile.name)
            self.profile_combo.removeItem(self.profile_combo.currentIndex())

        def rename_profile(self) -> None:
            """Rename the current profile."""
            old_name = self.profile.name
            new_name, success = getText(
                "Please enter a new profile name", self, title="New Name"
            )
            if not success:
                return
            self.profile_combo.setItemText(self.profile_combo.currentIndex(), new_name)
            self.profile.name = new_name
            self.to_delete.append(old_name)

    class CustomActions(QWidget):
        """A widget allowing the user to modify custom actions."""

        def __init__(
            self, parent: ContankiConfig, tab: QWidget, actions: dict[str, str]
        ) -> None:
            super().__init__()
            layout = QGridLayout()

            # Title
            label = QLabel("Custom Actions")
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 0, 0, 1, 2)

            # Table
            self.table = QTableWidget(len(actions), 2, tab)
            self.table.setHorizontalHeaderLabels(["Name", "Shortcut"])
            self.table.setVerticalHeaderLabels([])
            self.table.setColumnWidth(1, 70)
            self.table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            for row, (action, key_sequence) in enumerate(actions.items()):
                self.table.setItem(row, 0, QTableWidgetItem(action, 0))
                key_edit = QKeySequenceEdit(QKeySequence(key_sequence))
                self.table.setCellWidget(row, 1, key_edit)
            layout.addWidget(self.table, 1, 0, 1, 2)

            # Buttons
            add_button = Button(self, "Add", self.add_row)
            delete_button = Button(self, "Delete", self.remove_row)
            qconnect(self.table.itemChanged, parent.update_controls_page)
            layout.addWidget(add_button, 2, 0)
            layout.addWidget(delete_button, 2, 1)

            self.setLayout(layout)

        def add_row(self):
            """Add a row for a new custom action."""
            if self.table.selectedIndexes():
                current_row = self.table.currentRow() + 1
            else:
                current_row = self.table.rowCount()
            self.table.insertRow(current_row)
            self.table.setItem(current_row, 0, QTableWidgetItem("New Action", 0))
            self.table.setCellWidget(current_row, 1, QKeySequenceEdit(QKeySequence("")))
            self.table.setCurrentCell(current_row, 0)

        def remove_row(self):
            """Remove the selected row, or the last one."""
            if self.table.selectedIndexes():
                self.table.removeRow(self.table.currentRow())
            else:
                self.table.removeRow(self.table.rowCount() - 1)

        def get_row(self, row: int) -> tuple[str, str]:
            """Return the custom action name and key sequence at a given row."""
            if row > (num_rows := self.table.rowCount()):
                raise IndexError(f"Index {row} given but table has {num_rows} rows")
            return (
                self.table.item(row, 0).text(),
                self.table.cellWidget(row, 1).keySequence().toString(),
            )

        def get_actions(self) -> list[str]:
            """Return the custom action names as a list."""
            return [
                self.table.item(row, 0).text() for row in range(self.table.rowCount())
            ]

        def get_keys(self) -> list[str]:
            """Return the custom action key sequences as a list."""
            return [
                self.table.cellWidget(row, 1).keySequence().toString()
                for row in range(self.table.rowCount())
            ]

        def get(self) -> dict[str, str]:
            """Return the custom actions and key sequences as a dict."""
            return {k: v for k, v in zip(self.get_actions(), self.get_keys())}

    class FlagsSelector(QGroupBox):
        """Lets the user select which flags are cycled when reviewing."""

        def __init__(self, parent: QWidget, flags: list[int]):
            super().__init__("Flags", parent)
            layout = QFormLayout(self)
            layout.setVerticalSpacing(20)
            self.checkboxes: list[QCheckBox] = list()
            for flag in mw.flags.all():
                checkbox = QCheckBox(flag.label, self)
                checkbox.setIcon(theme_manager.icon_from_resources(flag.icon))
                if flag.index in flags:
                    checkbox.setChecked(True)
                layout.addWidget(checkbox)
                self.checkboxes.append(checkbox)
            self.setLayout(layout)

        def get(self) -> list[int]:
            """Returns the list of checked flags."""
            return [i for i, cbox in enumerate(self.checkboxes) if cbox.isChecked()]

    class ModSelectors(QGroupBox):
        """Combo boxes allowing the user to select modifier buttons."""

        def __init__(self, parent: ContankiConfig) -> None:
            super().__init__("Modifiers", parent)
            layout = QVBoxLayout(self)
            self.profile = parent.profile
            self.initialised = False
            self.combos = [
                QComboBox(self),
                QComboBox(self),
            ]
            for combo in self.combos:
                qconnect(
                    combo.currentIndexChanged,
                    partial(self.update_modifiers, parent.update_controls_page),
                )
                layout.addWidget(combo)
            self.setLayout(layout)
            self.update()
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.setFixedSize(self.sizeHint())

        def update(self):
            """Update the combo boxes to reflect the current controller."""
            current_mods = deepcopy(self.profile.mods)
            controller = self.profile.controller
            for i, combo in enumerate(self.combos):
                for _ in range(combo.count()):
                    combo.removeItem(0)
                for button in BUTTON_NAMES[controller].values():
                    combo.addItem(QIcon(get_button_icon(controller, button)), button)
                combo.setCurrentIndex(current_mods[i])
            self.profile.mods = current_mods

        def update_modifiers(self, callback: Callable) -> None:
            """Update the selected modifier buttons and refreshes the bindings table"""
            keys = list(BUTTON_NAMES[self.profile.controller].keys())
            self.profile.change_mod(
                self.profile.mods[0], keys[self.combos[0].currentIndex()]
            )
            self.profile.change_mod(
                self.profile.mods[1], keys[self.combos[1].currentIndex()]
            )
            callback()

    class AxisRoleSelector(QGroupBox):
        """Allows the user to select the role for each axis."""

        items = (
            "Unassigned",
            "Buttons",
            "Cursor Horizontal",
            "Cursor Vertical",
            "Scroll Horizontal",
            "Scroll Vertical",
        )

        def __init__(self, parent: ContankiConfig, controller: str) -> None:
            super().__init__("Axis Roles", parent)
            self.profile = parent.profile
            layout = QFormLayout(self)
            self.dropdowns: list[QComboBox] = list()

            for axis, name in AXES_NAMES[controller].items():
                dropdown = QComboBox()
                dropdown.addItems(self.items)
                dropdown.setCurrentText(parent.profile.axes_bindings[axis])
                qconnect(
                    dropdown.currentTextChanged,
                    partial(self.update_binding, parent.update_controls_page, axis),
                )
                label = QLabel()
                pixmap = get_button_icon(parent.profile.controller, name)
                label.setPixmap(
                    pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
                )
                layout.addRow(label, dropdown)
                self.dropdowns.append(dropdown)
            self.setLayout(layout)

        def update_binding(self, callback: Callable, axis: int, role: str) -> None:
            """Update the binding for the given axis."""
            self.profile.axes_bindings[axis] = role
            callback()

        def __getitem__(self, item: int) -> str:
            return self.dropdowns[item].currentText()
