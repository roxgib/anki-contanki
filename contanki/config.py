"""
Contanki's configuration dialog and associated classes.
"""

from __future__ import annotations

from functools import partial
from typing import Any, Callable, Iterable, Type

from aqt import qconnect
from aqt.qt import QTableWidget, QTableWidgetItem, QComboBox, QFormLayout, QHeaderView
from aqt.qt import (
    QDialog,
    QWidget,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QTabWidget,
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
)
from aqt.theme import theme_manager
from aqt.utils import showInfo, getText, askUser
from aqt import mw as _mw

from .controller import get_controller_list
from .funcs import get_config, get_debug_str
from .profile import (
    Profile,
    create_profile,
    delete_profile,
    get_profile,
    get_profile_list,
    update_assigned_profiles,
)
from .actions import QUICK_SELECT_ACTIONS, STATE_ACTIONS
from .icons import ButtonIcon, get_button_icon
from .utils import State

assert _mw is not None
mw = _mw


Alignment = Qt.AlignmentFlag

states: dict[State, str] = {
    "all": "Default",
    "deckBrowser": "Deck Browser",
    "overview": "Overview",
    "review": "Review",
    "question": "Question",
    "answer": "Answer",
    "dialog": "Dialogs",
}


class ContankiConfig(QDialog):
    """Contanki's config dialog.

    Allows the user to change the profile, settings, and bindings."""

    def __init__(self, parent: QWidget, profile: Profile | None) -> None:
        if profile is None:
            showInfo(
                "Controller not detected. Connect your controller and press any button to initialise."  # pylint: disable=line-too-long
            )
            return
        self.loaded = False

        # Initialise internal variables
        self._profile = profile.copy()
        self.config = get_config()
        self.to_delete: list[str] = list()
        self.profile_hash = hash(profile)

        # Initialise dialog
        super().__init__(parent)
        self.setWindowTitle("Contanki Options")
        self.setObjectName("Contanki Options")
        self.setFixedWidth(800)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        layout.setAlignment(Alignment.AlignTop)

        # Initialise main tabs (Options, Controls)
        self.tab_bar = QTabWidget()
        self.tab_bar.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum
        )
        self.options_page = OptionsPage(self)
        self.tab_bar.addTab(self.options_page, "Options")
        self.controls_page = ControlsPage(self)
        self.tab_bar.addTab(self.controls_page, "Controls")
        layout.addWidget(self.tab_bar)

        # Add buttons
        _buttons = [
            Button(self, "Save", self.save),
            Button(self, "Cancel", self.close),
            Button(self, "Help", self.help),
        ]
        _buttons[0].setDefault(True)
        buttons = Container(self, QHBoxLayout, _buttons)
        buttons.layout().setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        buttons.layout().setAlignment(Alignment.AlignRight)
        layout.addWidget(buttons)

        # Open
        self.setLayout(layout)
        self.resize(self.sizeHint())
        self.loaded = True
        self.open()

    def save(self) -> None:
        """Save changes, and load them. Used on close."""
        for profile in self.to_delete:
            delete_profile(profile)
        self.config.update(self.options_page.get())
        self.options_page.profile_bar.save_all()
        mw.addonManager.writeConfig(__name__, self.config)
        update_assigned_profiles(self._profile.controller, self._profile.name)
        mw.contanki.profile = self._profile  # type: ignore
        self.close()

    def help(self) -> None:
        """Open the Contanki help page."""
        showInfo(get_debug_str(), textFormat="rich")

    def change_profile(self, profile: Profile) -> None:
        """Changes which profile is targeted by the config window."""
        self._profile = profile
        self.reload()

    def get_profile(self) -> Profile:
        """Get the currrent profile."""
        return self._profile

    def get_custom_actions(self) -> list[str]:
        """Get the names of custom actions."""
        return self.options_page.custom_actions.get_actions()

    def update_binding(self, state: State, button: int, action: str) -> None:
        """Update the binding for the given button."""
        if self.loaded:
            self._profile.update_binding(state, button, action)
            if state in ("all", "review"):
                self.controls_page.update_inheritance()

    def reload(self):
        """Updates the page."""
        if self.loaded:
            self.controls_page.update_tabs()
            self.options_page.update()

    def update_controls_page(self):
        """Update the controls page."""
        if self.loaded:
            self.controls_page.update_tabs()


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
        self,
        parent: QWidget,
        layout: Type[QLayout],
        widgets: Iterable[QWidget | QPushButton],
    ) -> None:
        super().__init__(parent)
        self._layout = layout(self)
        for widget in widgets:
            self._layout.addWidget(widget)
        self.setLayout(self._layout)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.setFixedSize(self.sizeHint())

    def add_widget(self, widget: QWidget) -> None:
        """Add a widget to the container."""
        self._layout.addWidget(widget)


class OptionsPage(QWidget):
    """A widget containing the main options."""

    def __init__(self, parent: ContankiConfig) -> None:
        super().__init__(parent)
        self._parent = parent
        self.get_profile = parent.get_profile
        self.reload = parent.reload
        layout = QGridLayout(parent)
        self.options: dict[str, Any] = dict()
        config = get_config()
        assert config is not None
        self.config = config
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        left_column = QVBoxLayout()
        centre_column = QVBoxLayout()
        left_column.setSpacing(15)
        centre_column.setSpacing(15)

        # Profile Bar
        self.profile_bar = self.ProfileBar(parent)
        layout.addWidget(self.profile_bar, 0, 0, 1, 3, alignment=Alignment.AlignTop)

        # Main Options
        form = QGroupBox("Options", self)
        form_layout = QFormLayout(self)
        for key, value in self.config.items():
            if isinstance(value, bool):
                widget: QCheckBox | QSpinBox = QCheckBox(self)
                widget.setChecked(self.config[key])  # type: ignore
            elif isinstance(value, int):
                widget = QSpinBox(self)
                widget.setMinimumWidth(45)
                widget.setValue(value)
            else:
                continue
            form_layout.addRow(key, widget)
            self.options[key] = widget
        form.setLayout(form_layout)
        left_column.addWidget(form, alignment=Alignment.AlignTop)

        # Quick Select
        self.quick_select = self.QuickSelectSettings(parent)
        left_column.addWidget(self.quick_select, alignment=Alignment.AlignTop)

        # Axes & Flags
        self.axis_roles = self.AxisRoleSelector(parent)
        centre_column.addWidget(self.axis_roles, alignment=Alignment.AlignTop)
        self.flags = self.FlagsSelector(self._parent)
        centre_column.addWidget(self.flags, alignment=Alignment.AlignTop)

        # Custom Actions
        self.custom_actions = self.CustomActions(parent, self.config["Custom Actions"])

        layout.addLayout(left_column, 1, 0, alignment=Alignment.AlignTop)
        layout.addLayout(centre_column, 1, 1, alignment=Alignment.AlignTop)
        layout.addWidget(self.custom_actions, 1, 2)

        # Finish
        self.setLayout(layout)

    def get(self) -> dict:
        """Returns the currently selected options."""
        options = dict()
        for key, option in self.options.items():
            if isinstance(self.config[key], bool):
                options[key] = option.isChecked()
            elif isinstance(self.config[key], int):
                options[key] = option.value()
        options["Custom Actions"] = self.custom_actions.get()
        options["Flags"] = self.flags.get()
        return options

    def update(self):
        """Updates page to reflect user changess, such as the selected controller."""
        self.axis_roles.setup()
        self.quick_select.setup()

    class ProfileBar(QWidget):
        """A widget allowing the user to change, rename, or delete profiles."""

        def __init__(self, parent: ContankiConfig) -> None:
            super().__init__(parent)
            layout = QHBoxLayout()
            self.profile = parent.get_profile()
            self.to_delete = parent.to_delete
            profiles = get_profile_list(None, False)
            profiles = [p for p in profiles if p not in self.to_delete]
            self.profiles = [get_profile(name) for name in profiles]
            self.reload = parent.reload
            self._change_profile = parent.change_profile

            self.profile_combo = QComboBox(self)
            self.profile_combo.addItems(profiles)
            self.profile_combo.setCurrentIndex(profiles.index(self.profile.name))
            self.change_profile(self.profile_combo.currentIndex())
            qconnect(self.profile_combo.currentIndexChanged, self.change_profile)

            # Controller Selection Dropdown
            self.controller_combo = QComboBox(self)
            self.controller_combo.addItems(get_controller_list())
            self.controller_combo.setCurrentText(self.profile.controller.name)
            qconnect(self.controller_combo.currentTextChanged, self.update_controller)

            layout.addWidget(QLabel("Profile", self))
            layout.addWidget(self.profile_combo)
            layout.addWidget(Button(self, "Add Profile", self.add_profile))
            layout.addWidget(Button(self, "Rename Profile", self.rename_profile))
            layout.addWidget(Button(self, "Delete Profile", self.delete_profile))
            layout.addWidget(self.controller_combo)

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
            if not (old and okay1):
                return
            name, okay2 = QInputDialog().getText(
                self, "Create New Profile", "Enter the new profile name:"
            )
            if not (name and okay2):
                return
            new_profile = create_profile(old, name)
            if new_profile is None:
                return
            self.profiles.append(new_profile)
            self.profile_combo.addItem(new_profile.name)
            self.profile_combo.setCurrentText(new_profile.name)

        def delete_profile(self) -> None:
            """Delete the current profile."""
            if len(self.profiles) == 1:
                showInfo("You can't delete the last profile")
                return
            self.to_delete.append(self.profile.name)
            index = self.profile_combo.currentIndex()
            print(index)
            del self.profiles[index]
            self.profile_combo.removeItem(index)

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

        def get_profile(self) -> Profile:
            """Returns the currently selected profile."""
            return self.profiles[self.profile_combo.currentIndex()]

        def get_controller(self) -> str:
            """Returns the currently selected controller."""
            return self.controller_combo.currentText()

        def update_controller(self, controller: str) -> None:
            """Updates the dialog to reflect the chosen controller."""
            self.profile.controller = controller
            self.reload()

        def change_profile(self, index: int) -> None:
            """Changes the current profile."""
            self.profile = self.profiles[index]
            self._change_profile(self.profile)

        def save_all(self) -> None:
            """Saves all profiles."""
            for profile in self.profiles:
                profile.save()

    class CustomActions(QWidget):
        """A widget allowing the user to modify custom actions."""

        def __init__(self, parent: ContankiConfig, actions: dict[str, str]) -> None:
            super().__init__(parent)
            layout = QGridLayout()
            self.get_profile = parent.get_profile
            self.config = parent.config
            self.reload = parent.reload

            # Table
            self.table = QTableWidget(len(actions), 2, parent)
            self.table.setColumnWidth(0, 150)
            self.table.setColumnWidth(1, 100)
            self.table.setHorizontalHeaderLabels(["Custom Action", "Shortcut"])
            self.table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Stretch
            )
            self.table.verticalHeader().hide()
            self.key_edits = list()
            for row, (action, key_sequence) in enumerate(actions.items()):
                self.table.setItem(row, 0, QTableWidgetItem(action, 0))
                key_edit = QKeySequenceEdit(QKeySequence(key_sequence))
                self.key_edits.append(key_edit)
                self.table.setCellWidget(row, 1, key_edit)
            layout.addWidget(self.table, 0, 0, 1, 2)
            qconnect(self.table.cellChanged, self.update_config)

            # Buttons
            add_button = Button(self, "Add", self.add_row)
            delete_button = Button(self, "Delete", self.remove_row)
            layout.addWidget(add_button, 1, 0)
            layout.addWidget(delete_button, 1, 1)

            self.setLayout(layout)

        def add_row(self):
            """Add a row for a new custom action."""
            if self.table.selectedIndexes():
                current_row = self.table.currentRow() + 1
            else:
                current_row = self.table.rowCount()
            key_edit = QKeySequenceEdit(QKeySequence(""))
            self.key_edits.insert(current_row, key_edit)
            self.table.insertRow(current_row)
            self.table.setItem(current_row, 0, QTableWidgetItem("New Action", 0))
            self.table.setCellWidget(current_row, 1, key_edit)
            self.table.setCurrentCell(current_row, 0)
            self.update_config()

        def remove_row(self):
            """Remove the selected row, or the last one."""
            if not self.table.rowCount():
                return
            if self.table.selectedIndexes():
                self.key_edits.pop(self.table.currentRow())
                self.table.removeRow(self.table.currentRow())
            else:
                self.key_edits.pop()
                self.table.removeRow(self.table.rowCount() - 1)
            self.update_config()

        def get_row(self, row: int) -> tuple[str, str]:
            """Return the custom action name and key sequence at a given row."""
            if row > (num_rows := self.table.rowCount()):
                raise IndexError(f"Index {row} given but table has {num_rows} rows")
            return (
                self.table.item(row, 0).text(),
                self.key_edits[row].keySequence().toString(),
            )

        def get_actions(self) -> list[str]:
            """Return the custom action names as a list."""
            if not self.table.rowCount():
                return []
            return [
                self.table.item(row, 0).text() for row in range(self.table.rowCount())
            ]

        def get_keys(self) -> list[str]:
            """Return the custom action key sequences as a list."""
            if not self.table.rowCount():
                return []
            return [
                self.key_edits[row].keySequence().toString()
                for row in range(self.table.rowCount())
            ]

        def get(self) -> dict[str, str]:
            """Return the custom actions and key sequences as a dict."""
            if not self.table.rowCount():
                return {}
            return {k: v for k, v in zip(self.get_actions(), self.get_keys())}

        def update_config(self) -> None:
            """Update the profile with the custom actions."""
            self.config["Custom Actions"] = self.get()
            self.reload()

    class FlagsSelector(QGroupBox):
        """Lets the user select which flags are cycled when reviewing."""

        def __init__(self, parent: ContankiConfig):
            super().__init__("Flags", parent)
            self.config = parent.config
            layout = QFormLayout(self)
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            self.checkboxes: list[QCheckBox] = list()
            for flag in mw.flags.all():
                checkbox = QCheckBox(flag.label, self)
                checkbox.setIcon(theme_manager.icon_from_resources(flag.icon))
                checkbox.setChecked(flag.index in self.config["Flags"])
                layout.addWidget(checkbox)
                self.checkboxes.append(checkbox)
            self.setLayout(layout)

            for checkbox in self.checkboxes:
                qconnect(checkbox.stateChanged, self.update_flags)

        def update_flags(self):
            """Update the config with the selected flags."""
            print(self.get())
            self.config["Flags"] = self.get()

        def get(self) -> list[int]:
            """Returns the list of checked flags."""
            return [i + 1 for i, cbox in enumerate(self.checkboxes) if cbox.isChecked()]

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

        def __init__(self, parent: ContankiConfig) -> None:
            super().__init__("Axis Roles", parent)
            self.get_profile = parent.get_profile
            self.dropdowns: list[QComboBox] = list()
            self.update_controls_page = parent.update_controls_page
            self.setAlignment(Alignment.AlignTop)
            self.setup()

        def update_binding(self, axis: int, role: str) -> None:
            """Update the binding for the given axis."""
            self.get_profile().axes_bindings[axis] = role
            self.update_controls_page()

        def setup(self) -> None:
            """Refresh for the current controller."""
            layout = QFormLayout(self)
            layout.setFormAlignment(Alignment.AlignVCenter)
            layout.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )
            layout.setLabelAlignment(Alignment.AlignRight | Alignment.AlignVCenter)
            self.dropdowns.clear()
            for axis, name in self.get_profile().controller.axes.items():
                dropdown = QComboBox()
                dropdown.setSizePolicy(
                    QSizePolicy.Policy.MinimumExpanding,
                    QSizePolicy.Policy.MinimumExpanding,
                )
                dropdown.addItems(self.items)
                dropdown.setCurrentText(self.get_profile().axes_bindings[axis])
                qconnect(
                    dropdown.currentTextChanged,
                    partial(self.update_binding, axis),
                )
                label = QLabel()
                pixmap = get_button_icon(self.get_profile().controller, name)
                label.setPixmap(
                    pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio)
                )
                layout.addRow(label, dropdown)
                self.dropdowns.append(dropdown)
            layout.setSizeConstraint(QFormLayout.SizeConstraint.SetFixedSize)
            self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
            _temp = QWidget()
            _temp.setLayout(self.layout())
            self.setLayout(layout)

        def __getitem__(self, item: int) -> str:
            return self.dropdowns[item].currentText()

    class QuickSelectSettings(QGroupBox):
        """Settings for the Quick Select radial menu."""

        def __init__(self, parent: ContankiConfig):
            super().__init__("Quick Select", parent)
            self.get_profile = parent.get_profile
            self.config = parent.config
            self._parent = parent
            self.setup()

        def setup(self) -> None:
            """Setup the Quick Select settings."""
            layout = QFormLayout(self._parent)
            for option, value in self.get_profile().quick_select.items():
                if option == "actions":
                    continue
                checkbox = QCheckBox(self._parent)
                checkbox.setChecked(value)
                qconnect(checkbox.stateChanged, partial(self.update_option, option))
                layout.addRow(option, checkbox)
                if (
                    option == "Select with Stick"
                    and not self.get_profile().controller.has_stick
                ) or (
                    option == "Select with D-Pad"
                    and not self.get_profile().controller.has_dpad
                ):
                    checkbox.setChecked(False)
                    checkbox.setEnabled(False)
            widget = QWidget()
            if self.layout():
                widget.setLayout(self.layout())
            self.setLayout(layout)

        def update_option(self, option: str, value: bool) -> None:
            """Update the given option."""
            self.get_profile().quick_select[option] = value


class ControlsPage(QTabWidget):
    """A widget allowing the user to modify the bindings."""

    style_sheet = """
    QTabWidget::pane { border: 0px; } 
    """
    # QComboBox::dropdown { margin: auto; }

    def __init__(self, parent: ContankiConfig) -> None:
        super().__init__(parent)
        self.setStyleSheet(self.style_sheet)
        self._parent = parent
        self.get_profile = parent.get_profile
        self._update_binding = parent.update_binding
        self.get_custom_actions = parent.get_custom_actions
        self.setObjectName("controls_page")
        self.setTabPosition(QTabWidget.TabPosition.South)
        self.tabs: dict[str, self.ControlsTab] = dict()
        self.combos: dict[State, dict[int, QComboBox]] = dict()
        self.update_tabs()

    def update_inheritance(self):
        """Updates action selection dropdowns to reflect inherited values."""
        combos_iter = [
            (state, index, combo)
            for state, state_combos in self.combos.items()
            if state != "all"
            for index, combo in state_combos.items()
            if index in state_combos
        ]

        all_bindings = {
            i: action
            for (state, i), action in self.get_profile().bindings.items()
            if state == "all"
        }

        review_bindings = {
            i: action
            for (state, i), action in self.get_profile().bindings.items()
            if state == "review"
        }

        for state, i, combo in combos_iter:
            inherited = ""
            if action := all_bindings[i]:
                inherited = action + " (inherited)"
            if state in ("question", "answer") and (action := review_bindings[i]):
                inherited = action + " (inherited)"
            combo.setItemText(0, inherited)

    def update_tabs(self):
        """Redraws each tab to reflect the chosen options."""
        self.custom_actions = self.get_custom_actions()
        for _ in self.tabs:
            self.removeTab(0)
        self.tabs.clear()
        self.combos.clear()
        for state, state_name in states.items():
            self.tabs[state] = state_tab = self.ControlsTab(self, state)
            state_tab.setObjectName("state_tab")
            self.combos[state] = state_tab.combos
            self.addTab(state_tab, state_name)
        self.tabs["quick_select"] = self.QuickSelectActions(self._parent)
        self.addTab(self.tabs["quick_select"], "Quick Select")
        self.update_inheritance()

    def update_binding(self, state: State, button: int, action: str) -> None:
        """Updates the binding for the given state, mod, and index."""
        if "inherit" in action:
            action = ""
        self._update_binding(state, button, action)

    class ControlsTab(QWidget):
        """Shows control binding options for a singel state."""

        def __init__(self, parent: ControlsPage, state: State) -> None:
            super().__init__()
            axes_bindings = parent.get_profile().axes_bindings
            self.combos: dict[int, QComboBox] = dict()
            buttons = parent.get_profile().controller.buttons.copy()

            buttons.update(
                {
                    index + 100: action
                    for index, action in parent.get_profile().controller.axis_buttons.items()
                }
            )
            layout = QGridLayout(self)
            col = 0
            row = 0
            for index, button in sorted(buttons.items()):
                if index >= 100:
                    axis = (index - 100) // 2
                    if axis not in axes_bindings or axes_bindings[axis] != "Buttons":
                        continue
                icon = ButtonIcon(None, button, parent.get_profile().controller, index)
                icon.setFixedSize(60, 60)
                layout.addWidget(icon, row, col)
                col += 1
                combo = QComboBox()
                combo.addItems(STATE_ACTIONS[state] + parent.custom_actions)
                combo.setCurrentText(parent.get_profile().bindings[(state, index)])
                combo.setMaximumWidth(170)
                combo.setFixedHeight(30)
                qconnect(
                    combo.currentTextChanged,
                    partial(parent.update_binding, state, index),
                )
                layout.addWidget(combo, row, col)
                col += 1
                if col == 6:
                    col = 0
                    row += 1
                self.combos[index] = combo
            self.setLayout(layout)

    class QuickSelectActions(QWidget):
        """Contains checkboxes to add actions to quick select for a state."""

        column_count = 4

        def __init__(self, parent: ContankiConfig) -> None:
            super().__init__(parent)
            self.get_profile = parent.get_profile
            self.custom_actions = parent.get_custom_actions()
            layout = QVBoxLayout(self)
            self.checkboxes: dict[State, list[QCheckBox]] = dict()
            states: list[State] = ["deckBrowser", "overview", "review"]
            for state in states:
                layout.addWidget(self.setup_group(state))

        def setup_group(self, state: State) -> QGroupBox:
            """Adds all the checkboxes to the groupbox."""
            group = QGroupBox(states[state], self)
            combos = []
            for action in QUICK_SELECT_ACTIONS[state] + self.custom_actions:
                checkbox = QCheckBox(action, self)
                checkbox.setChecked(
                    action in self.get_profile().quick_select["actions"][state]
                )
                qconnect(checkbox.stateChanged, partial(self.on_change, action, state))
                combos.append(checkbox)
            self.checkboxes[state] = combos

            if combos:
                self.show()
            else:
                self.hide()

            layout = QGridLayout(self)
            for i, action_check in enumerate(combos):
                layout.addWidget(
                    action_check, i // self.column_count, i % self.column_count
                )
            group.setLayout(layout)
            return group

        def on_change(self, action: str, state: State, checked: bool) -> None:
            """Updates the profile with actions to include in the quick select menu."""
            actions = self.get_profile().quick_select["actions"][state]
            if checked and action not in actions:
                actions.append(action)
            elif not checked and action in actions:
                actions.remove(action)
            for combo in self.checkboxes[state]:
                combo.setEnabled(len(actions) < 8 or combo.text() in actions)
