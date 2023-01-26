# Contributing

## Testing and adding new controllers
For issues with existing controllers please post in the issue tracker.

If you own a controller and would like it to be supported by Contanki, please post in the issue tracker. If you want to help with some of the leg work, the following is required to add a new controller:
- Mappings for the controls. Each button will have an index, typically from 0 to 18 or so. Same for the axes. See the examples in contanki/controllers.json. The best way to get these is to use [this site](https://gamepad-tester.com) in Chrome. It has to be from Chrome or another Chromium based browser or the mappings may not be correct.
- Icons for each of the buttons on the controller. These don't have to be perfect, so if there are existing icons that look similar enough this might be acceptable. If you take icons from the web I need to know where they come from for copyright reasons.
- The controller ID. You can get this connecting the controller while Contanki is running, pressing any button on the controller, and then going to Tools -> Controller Options -> Help. The information should appear even if Contanki didn't detect the controller - if it doesn't there may be an issue with the controller.
- Any extra details required. For example 8BitDo controllers have multiple modes, and the button mappings differ between modes.

If you don't have any of the above information, please still feel free to contact me since I managed to add most of the existing controllers without actually owning them. I may ask you to do some testing for me.

## Running tests
To run the tests, Anki must be run from source as the packaged builds do not check Python assert statements. Clone the main Anki repository and then do something like this from Contanki's repo:

```
rm -r "/path/to/Anki2/addons21/Contanki"
cp -R ./Contanki "/path/to/Anki2/addons21"
echo "Addon installed"
cd path/to/anki 
DEBUG=1 ./run
```

This will run the tests immediately after Anki start up. Note that if you have Contanki installed from AnkiWeb it needs to be disabled - the version copied over for testing will be in a separate directory so as not to conflict with the installed version or delete any saved profiles or settings.

## Architecture
The controllers are accessed using the HTML/JS Gamepad API. The Contanki class is an AnkiWebView which runs a JS script (controller.js) handles connecting, disconnecting, and polling the controller. For each of those events it calls up to the Python code, which handles the bulk of the logic. In the long run I'd like to move more of the logic into the JS code such that the interface calls only need to be made when the controller state changes rather than on every poll, but my knowledge of JS was limited when I started this project and I haven't had time to go back and refactor it.

The Profile class handles profiles, and these are saved as JSON files to the user_files folder. Profiles have caused a lot of issues so any efforts to improve profile.py would be welcome, but be careful that changes are backwards compatible. Controllers are handled by controller.py, which deals with things like identifying and mapping controllers.

The config dialog is all done in PyQt, but the UI of the dialog should really be converted to a Qt Designer .ui file. If you are familar with Qt Designer this would be helpful, and you wouldn't have to worry about the Python code.f

These are the main places to start to understand how the code is structured - the other files will hopefully be self-explanatory.

## Code style
Black
