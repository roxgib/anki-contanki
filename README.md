# Contanki: Controller Support for Anki

Contanki is an add-on for [Anki](apps.ankiweb.com) which allows users to control Anki using a gamepad or other controller device.

Features:
 - Comfortably review your cards and much more using a gamepad
 - Control almost any Anki feature without a keyboard or mouse
 - Pull up a helpful overlay to remind you of the control mapping
 - Cursor control for limited situations where the gamepad is insufficient
 - Customisable control bindings

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
 - Opening certain menus or dialogs prevents any actions from firing, until it's closed and they fire all at once
 - A number of deck-related actions require opening the overview, and will operate on the wrong deck if you try them from the deck screen
 - Interaction outside of the main window e.g. browser is only partially implemented
 - Several options are not actually configurable despite appearing in the options
 - Many controllers won't be supported properly yet
 - Trackpad on DualShock 4 doesn't work, except as a button

 Version Related:
 - Alpha 3 only works on 2.1.49 and 2.1.50, but Alpha 2 will work on most earlier versions. This should be fixed soon.


## Development log

### Alpha 3

Alpha 3 is now available for download. Unfortunately it only supports 2.1.49 and 2.1.50, but this should be fixed in the next release.

New features
 - Greatly improved dialog interaction (although see below regarding the dialog/menu issue)

Fixes:
 - Message shown on controller disconnect
 - Reconnects now more reliable
 - Tentative fix for excessive CPU usage if Anki has been left open for several days
 - Compatibility fixes for earlier Anki versions (but most testing is still on 49 & 50 so far)
 
 I've been working on fixing the dialogs/menus .exec() issue, but the fixes required are in Anki's code, so it's unlikely this issue will be addressed for any current version of Anki, and it requires changes to each individual menu or dialog and a lot of testing to ensure it doesn't introduce other issues, so is likely to take some time. This add-on won't be moved to beta until these fixes make it to a main Anki release.

In the meantime users will simply have to avoid clicking the menus or opening affected dialogs. I might release a version with those features disabled, but for testing purposes they are enabled in alpha versions.

Both clicking outside Anki and touchpad support are low priority right now, as they are both likely to require a lot of work and possibly different solutions for each platform. I do intend to eventually support both however.

The following features are intended before the beta release:

 - Improved config dialog
 - Full support for Xbox controllers
 - All actions configurable
 - Compatibility back to 2.1.45 (probably without dialog access)