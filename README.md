## gameapi_util
A simple Python script to assist with managing RSDKv5/U projects.

![Screenshot of the main interface](/screenshots/main.png)

## Dependencies

urwid is used for the console interface. It can be installed using:
```
pip install urwid
```

## Default Functions

- **Project Update**
  - Generates `All.c/All.cpp`, which can be used in your Visual Studio or CMake project. This can speed up build times by compiling every object at once, instead of compiling them separately.
  - Generates `Objects.cmake`, which can be used instead of `All.c/All.cpp`, if you'd like to build the objects separately.

- **Generate public functions**
  - Generates public functions for the RSDKv5U decompilation's modding API. Entity events are not included.

- **New Object** [default]
  - Creates a new object in the specified directory.

- **New Object** [clean]
  - Same as above, without any predefined entity events.

- **New Object** [modded]
  - Creates a new modded object in the specified directory.

- **New Object** [modded][clean]
  - Same as above, without any predefined entity events.

## Configuration
`gameapi_util_cfg.py` is used for configuring various things, such as the path to your objects directory.

**Available options:**
```py
GAME_PATH        = "src"
OBJECT_PATH_NAME = "Objects"
ALL_CODE_NAME    = "All.cpp"
ALL_HEADER_NAME  = "All.hpp"
GAMEAPI_INC_PATH = "Game.hpp"
PUB_FNS_PATH     = "PublicFunctions.hpp"
OBJECT_NAMESPACE = "GameLogic"

# cmake configuration
CMAKE_PATH = "Objects.cmake"
GAME_NAME  = "${GAME_NAME}" # The game directory to look into

OBJECT_PATH = f"{GAME_PATH}/{OBJECT_PATH_NAME}"
ALL_CODE_PATH = f'{OBJECT_PATH}/{ALL_CODE_NAME}'
ALL_HEADER_PATH = f'{GAME_PATH}/{ALL_HEADER_NAME}'
```

## Extending the main menu
You can extend the main menu with the `init` function of your project's configuration file. For example:
```py
def init(app_in):
    global app
    app = app_in

    app.add_label('[Custom Tools]')
    app.add_option('Validate Objects', object_validity_check)
    app.add_option('Check Status', project_status_check)
    app.spacer()
# init -> (app_in)
```

![Screenshot of the main interface, after being extended by gameapi_util_cfg.py](/screenshots/main_extended.png)
