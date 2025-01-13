import os
import gameapi_util_cfg as config

# Function/Variable definitions
app = None

##
## C++ object
## This also generates modded objects, with regtype
##
cpp_object = '''#include "{gameapi_inc_path}"

using namespace RSDK;

namespace {namespace}
{{

// -------------------
// Object Registration
// -------------------

{regtype}({obj_name});

// -------------
// Entity Events
// -------------

void {obj_name}::Update() {{}}

void {obj_name}::LateUpdate() {{}}

void {obj_name}::StaticUpdate() {{}}

void {obj_name}::Draw() {{}}

void {obj_name}::Create(void *data) {{}}

void {obj_name}::StageLoad() {{}}

#if GAME_INCLUDE_EDITOR
void {obj_name}::EditorLoad() {{}}

void {obj_name}::EditorDraw() {{}}
#endif

#if RETRO_REV0U
void {obj_name}::StaticLoad(Static *sVars) {{ RSDK_INIT_STATIC_VARS({obj_name}); }}
#endif

void {obj_name}::Serialize() {{}}

}} // namespace {namespace}
'''

##
## C++ object, without any predefined entity events
## This also generates modded objects, with regtype
##
clean_cpp_object = '''#include "{gameapi_inc_path}"

using namespace RSDK;

namespace {namespace}
{{

// -------------------
// Object Registration
// -------------------

{regtype}({obj_name});

}} // namespace {namespace}
'''

##
## C++ object header
##
cpp_object_header = '''#pragma once
#include "{gameapi_inc_path}"

using namespace RSDK;

// ------------------
// Macros/Definitions
// ------------------

namespace {namespace}
{{
struct {obj_name} : GameObject::Entity {{

    // ---------------
    // Enums & Structs
    // ---------------

    // ----------------
    // Static Variables
    // ----------------

    struct Static : GameObject::Static {{
    }};

    // ----------------
    // Entity Variables
    // ----------------

    // ----------------------
    // Standard Entity Events
    // ----------------------

    void Create(void* data);
    void Draw();
    void Update();
    void LateUpdate();
    static void StaticUpdate();
    static void StageLoad();
#if GAME_INCLUDE_EDITOR
    static void EditorLoad();
    void EditorDraw();
#endif
#if RETRO_REV0U
    static void StaticLoad(Static* sVars);
#endif
    static void Serialize();

    // ----------------------
    // Extra Entity Functions
    // ----------------------

    // -------------
    // Object States
    // -------------

    // ------------------
    // Object Draw States
    // ------------------

    // -------------------
    // Static Declarations
    // -------------------

    RSDK_DECLARE({obj_name});
}};
}} // namespace {namespace}
'''

##
## C++ modded object header
##
mod_cpp_object_header = '''#pragma once
#include "{gameapi_inc_path}"

using namespace RSDK;

// ------------------
// Macros/Definitions
// ------------------

namespace {namespace}
{{
struct {obj_name} : GameObject::Entity {{

    // ---------------
    // Enums & Structs
    // ---------------

    // ----------------
    // Static Variables
    // ----------------

    struct Static : GameObject::Static {{
    }};

    struct ModStatic : GameObject::Static {{
    }};

    // ----------------
    // Entity Variables
    // ----------------

    // ----------------------
    // Standard Entity Events
    // ----------------------

    void Create(void* data);
    void Draw();
    void Update();
    void LateUpdate();
    static void StaticUpdate();
    static void StageLoad();
#if GAME_INCLUDE_EDITOR
    static void EditorLoad();
    void EditorDraw();
#endif
#if RETRO_REV0U
    static void StaticLoad(Static* sVars);
#endif
    static void Serialize();

    // ----------------------
    // Extra Entity Functions
    // ----------------------

    // -------------
    // Object States
    // -------------

    // ------------------
    // Object Draw States
    // ------------------

    // -------------------
    // Static Declarations
    // -------------------

    MOD_DECLARE({obj_name});
}};
}} // namespace {namespace}
'''

##
## C++ object header, without any predefined entity events
##
clean_cpp_object_header = '''#pragma once
#include "{gameapi_inc_path}"

using namespace RSDK;

namespace {namespace}
{{
struct {obj_name} : GameObject::Entity {{

    // ----------------
    // Static Variables
    // ----------------

    struct Static : GameObject::Static {{
    }};

    // ----------------
    // Entity Variables
    // ----------------

    // -------------------
    // Static Declarations
    // -------------------

    RSDK_DECLARE({obj_name});
}};
}} // namespace {namespace}
'''

##
## C++ modded object header, without any predefined entity events
##
clean_mod_cpp_object_header = '''#pragma once
#include "{gameapi_inc_path}"

using namespace RSDK;

namespace {namespace}
{{
struct {obj_name} : GameObject::Entity {{

    // ----------------
    // Static Variables
    // ----------------

    struct Static : GameObject::Static {{
    }};

    struct ModStatic : GameObject::Static {{
    }};

    // ----------------
    // Entity Variables
    // ----------------

    // -------------------
    // Static Declarations
    // -------------------

    MOD_DECLARE({obj_name});
}};
}} // namespace {namespace}
'''

# General
def init(app_in):
    global app
    app = app_in

def directory_validate(directory):
    directory_path = os.path.dirname(directory)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

# C++ generators
def new_cpp_object(name, directory):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_object = cpp_object.format(
            gameapi_inc_path=config.GAMEAPI_INC_PATH,
            namespace=config.OBJECT_NAMESPACE,
            obj_name=name,
            regtype="RSDK_REGISTER_OBJECT"
        )

        with open(directory, "w") as out:
            out.write(formatted_object)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

def new_cpp_object_header(name, directory):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_header = cpp_object_header.format(
            gameapi_inc_path=config.GAMEAPI_INC_PATH,
            namespace=config.OBJECT_NAMESPACE,
            obj_name=name
        )

        with open(directory, "w") as out:
            out.write(formatted_header)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

def cpp_public_functions():
    return

# C generators
def new_c_object(name):
    return

def new_c_object_header(name):
    return

def c_public_functions():
    return