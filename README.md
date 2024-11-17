# gameapi_util
A simple Python script to assist with managing RSDKv5/U projects.

## Default Functions

- **Update All.cpp/All.hpp & CMake Project**
  - This function generates `All.cpp` & `All.hpp` includes and `Objects.cmake`.
  - Forward declarations are included in the header.

- **Generate public functions**
  - This function generates `PublicFunctions.hpp`. Entity events are not included.

- **Create new object**
  - Creates a new object in the specified directory.
  - After creation, you can optionally run `project_update` to generate new `All.cpp` and `All.hpp` files.
