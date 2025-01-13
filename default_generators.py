import os
import gameapi_util_cfg as config
from enum import Enum

# Function/Variable definitions
app = None

class modes(Enum):
    default      = 0
    clean        = 1
    modded       = 2
    modded_clean = 3

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

##
## C object
##

c_object = '''#include "{gameapi_inc_path}"

Object{obj_name} *{obj_name};

void {obj_name}_Update(void) {{}}

void {obj_name}_LateUpdate(void) {{}}

void {obj_name}_StaticUpdate(void) {{}}

void {obj_name}_Draw(void) {{}}

void {obj_name}_Create(void *data) {{}}

void {obj_name}_StageLoad(void) {{}}

#if GAME_INCLUDE_EDITOR
void {obj_name}_EditorLoad(void) {{}}

void {obj_name}_EditorDraw(void) {{}}
#endif

#if RETRO_REV0U
void {obj_name}_StaticLoad(Object{obj_name} *sVars) {{ RSDK_INIT_STATIC_VARS({obj_name}); }}
#endif

void {obj_name}_Serialize(void) {{}}
'''

##
## C object, without any predefined entity events
##

clean_c_object = '''#include "{gameapi_inc_path}"

Object{obj_name} *{obj_name};
'''

##
## C object header
##

c_object_header = '''#ifndef OBJ_{obj_name_up}_H
#define OBJ_{obj_name_up}_H

#include "{gameapi_inc_path}"

// Object Class
struct Object{obj_name} {{
    RSDK_OBJECT
}};


// Entity Class
struct Entity{obj_name} {{
    RSDK_ENTITY
}};

// Object Struct
extern Object{obj_name} *{obj_name};

// Standard Entity Events
void {obj_name}_Update(void);
void {obj_name}_LateUpdate(void);
void {obj_name}_StaticUpdate(void);
void {obj_name}_Draw(void);
void {obj_name}_Create(void *data);
void {obj_name}_StageLoad(void);
#if GAME_INCLUDE_EDITOR
void {obj_name}_EditorLoad(void);
void {obj_name}_EditorDraw(void);
#endif
void {obj_name}_Serialize(void);

// Extra Entity Functions

#endif //! OBJ_{obj_name_up}_H
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
def new_cpp_object(name, directory, mode):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_object = ""

        if mode == modes.default:
            formatted_object = cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="RSDK_REGISTER_OBJECT"
            )
        elif mode == modes.clean:
            formatted_object = clean_cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="RSDK_REGISTER_OBJECT"
            )
        elif mode == modes.modded:
            formatted_object = cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="MOD_REGISTER_OBJECT"
            )
        elif mode == modes.modded_clean:
            formatted_object = clean_cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="MOD_REGISTER_OBJECT"
            )

        with open(directory, "w") as out:
            out.write(formatted_object)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

def new_cpp_object_header(name, directory, mode):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_header = ""

        if mode == modes.default:
            formatted_header = cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == modes.clean:
            formatted_header = clean_cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == modes.modded:
            formatted_header = mod_cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == modes.modded_clean:
            formatted_header = clean_mod_cpp_object_header.format(
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