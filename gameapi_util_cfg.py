import os
import curses

# Use this to exclude default options from the menu.
# this can be useful if you'd like to make your own
# implementations of them. True | False

# If you'd prefer to skip some options, but keep
# specific ones in, you can add them back, via the
# init function. For example:
# util.add_option("Update All.cpp/hpp & CMake Project", util.project_update)
skipDefaultTools = False

# Path configurations. By default, these are used for
# generating All.cpp/hpp & Objects.cmake, generating
# public functions, creating new objects, etc
GAME_PATH        = 'src'
OBJECT_PATH_NAME = 'Objects'
ALL_CODE_NAME    = 'All.cpp'
ALL_HEADER_NAME  = 'All.hpp'
PUB_FNS_PATH     = f'{GAME_PATH}/PublicFunctions.hpp'
OBJECT_NAMESPACE = 'GameLogic'

# cmake configuration
CMAKE_PATH = 'Objects.cmake'
GAME_NAME  = '${GAME_NAME}' # The game directory to look into

OBJECT_PATH = f'{GAME_PATH}/{OBJECT_PATH_NAME}'
ALL_CPP_PATH = f'{OBJECT_PATH}/{ALL_CODE_NAME}'
ALL_HPP_PATH = f'{GAME_PATH}/{ALL_HEADER_NAME}'

# Function/Variable definitions
window = None
util   = None

def init(window_in, util_in):
    global window, util
    window = window_in
    util   = util_in
# Init
