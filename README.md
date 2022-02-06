# Contanki: Controller Support for Anki

Contanki is an add-on for [Anki](apps.ankiweb.com) which allows users to control Anki using a gamepad or other controller device.

Features:
 - Comfortably review your cards and much more using a gamepad
 - Control almost any Anki feature without a keyboard or mouse
 - Pull up a helpful overlay to remind you of the control mapping
 - Customisable key bindings
 - Support for mouse control for limited situations where the gamepad is insufficient
 - Various useful additional actions, such as navigating through due decks

## Usage Notes

Since Anki has a lot of functions to map, Contanki uses the triggers (R2 and L2) as modifier keys, meaning that the other buttons will trigger different commands when they are held down. This is similar to Shift, Control, etc on a keyboard. Holding down the trigger keys will also pull up an overlay showing the control binding for the current context. To show the overlay for unmodified keys, hold down both triggers at once. 

Controls can be reassigned using the add-ons config dialog (this dialog is still in development, and should be improved soon). You can assign controls for each context, as well as global commands that are used if a control isn't assigned to a particular context. It is suggested that you try the default control bindings to begin with, and make changes as needed. You can remove any actions you don't need if the controls overlay is too cluttered. 

### Analog Sticks
The right stick is used to move and click the mouse, and you can use L2 + right stick for a secondary click. At this time it is only possible to click within Anki. The left stick is used to select items similar to using Tab and Shift + Tab to navigate, and is also used to scroll using R2 + left stick.

### Choosing a Controller

I have been testing using a DualShock 4, which can be readily purchased secondhand at a reasonable price and otherwise makes a good choice, although cheaper options will probably work just as well.

## Issues
Please report all issues on the GitHub issue tracker. Reports about bugs on Windows or when using an Xbox controller are particularly welcome as I have been testing almost exclusively on Mac using a DualShock 4 up to now. 

### Known issues
 - Add-on doesn't function in the profile window
 - Clicking in the title bar or outside of Anki doesn't work 
 - Clicking the deck gear menu or the reviewer options menu prevents any actions from firing, until it's closed and they fire all at once
 - A number of deck-related actions require opening the overview, and will operate on the wrong deck if you try them from the deck screen
 - Overlay doesn't generate on the first attempt of each session
 - Interaction outside of the main window e.g. dialogs, browser is only partially implemented
 - Several options are not actually configurable despite appearing in the options
 - Many controllers won't be supported properly yet
 - Trackpad on DualShock 4 doesn't work, except as a button