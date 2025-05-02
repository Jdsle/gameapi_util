import urwid, os, sys, re
import gameapi_util_cfg as config
from enum import Enum
from pathlib import Path

# Function/Variable definitions
app = None

#
# [objectutil]
#

class objectutil_modes(Enum):
    default      = 0
    clean        = 1
    modded       = 2
    modded_clean = 3

class menuutil_listbox(urwid.ListBox):
    def __init__(self, body):
        super().__init__(body)
        self.rows = 0

    def keypress(self, size, key):
        if key in ('up', 'down', 'k', 'j'):
            return key
        return super().keypress(size, key)

    def render(self, size, focus=False):
        canvas = super().render(size, focus)
        self.rows = canvas.rows()
        return canvas

    def scroll(self, selection):
        if selection < self.focus_position or selection >= self.focus_position + self.rows:
            self.set_focus(selection)


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

    struct ModStatic {{
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

    struct ModStatic {{
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
## C modded object
##

mod_c_object = '''#include "{gameapi_inc_path}"

Object{obj_name} *{obj_name};
ModObject{obj_name} *Mod_{obj_name};

void {obj_name}_Update(void) {{}}

void {obj_name}_LateUpdate(void) {{}}

void {obj_name}_StaticUpdate(void) {{}}

void {obj_name}_Draw(void) {{}}

void {obj_name}_Create(void *data) {{}}

void {obj_name}_StageLoad(void) {{}}

#if MOD_INCLUDE_EDITOR
void {obj_name}_EditorLoad(void) {{}}

void {obj_name}_EditorDraw(void) {{}}
#endif

#if RETRO_REV0U
void {obj_name}_StaticLoad(Object{obj_name} *sVars) {{ RSDK_INIT_STATIC_VARS({obj_name}); }}
#endif

void {obj_name}_Serialize(void) {{}}
'''

##
## C modded object, without any predefined entity events
##

clean_mod_c_object = '''#include "{gameapi_inc_path}"

Object{obj_name} *{obj_name};
ModObject{obj_name} *Mod_{obj_name};
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

##
## C modded object header
##

mod_c_object_header = '''#ifndef OBJ_{obj_name_up}_H
#define OBJ_{obj_name_up}_H

#include "{gameapi_inc_path}"

// Object Class
typedef struct {{
    RSDK_OBJECT
}} Object{obj_name};


// Modded Object Class
typedef struct {{
}} Object{obj_name};


// Entity Class
typedef struct {{
    RSDK_ENTITY
}} Entity{obj_name};

// Object Struct
extern Object{obj_name} *{obj_name};
extern ModObject{obj_name} *Mod_{obj_name};

// Standard Entity Events
void {obj_name}_Update(void);
void {obj_name}_LateUpdate(void);
void {obj_name}_StaticUpdate(void);
void {obj_name}_Draw(void);
void {obj_name}_Create(void *data);
void {obj_name}_StageLoad(void);
#if MOD_INCLUDE_EDITOR
void {obj_name}_EditorLoad(void);
void {obj_name}_EditorDraw(void);
#endif
void {obj_name}_Serialize(void);

// Extra Entity Functions

#endif //! OBJ_{obj_name_up}_H
'''

##
## C object header, without any predefined entity events
##

clean_c_object_header = '''#ifndef OBJ_{obj_name_up}_H
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

#endif //! OBJ_{obj_name_up}_H
'''

##
## C modded object header, without any predefined entity events
##

clean_mod_c_object_header = '''#ifndef OBJ_{obj_name_up}_H
#define OBJ_{obj_name_up}_H

#include "{gameapi_inc_path}"

// Object Class
typedef struct {{
    RSDK_OBJECT
}} Object{obj_name};


// Modded Object Class
typedef struct {{
}} Object{obj_name};


// Entity Class
typedef struct {{
    RSDK_ENTITY
}} Entity{obj_name};

// Object Struct
extern Object{obj_name} *{obj_name};
extern ModObject{obj_name} *Mod_{obj_name};

#endif //! OBJ_{obj_name_up}_H
'''

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

        if mode == objectutil_modes.default:
            formatted_object = cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="RSDK_REGISTER_OBJECT"
            )
        elif mode == objectutil_modes.clean:
            formatted_object = clean_cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="RSDK_REGISTER_OBJECT"
            )
        elif mode == objectutil_modes.modded:
            formatted_object = cpp_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name,
                regtype="MOD_REGISTER_OBJECT"
            )
        elif mode == objectutil_modes.modded_clean:
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

        if mode == objectutil_modes.default:
            formatted_header = cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == objectutil_modes.clean:
            formatted_header = clean_cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == objectutil_modes.modded:
            formatted_header = mod_cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )
        elif mode == objectutil_modes.modded_clean:
            formatted_header = clean_mod_cpp_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                namespace=config.OBJECT_NAMESPACE,
                obj_name=name
            )

        with open(directory, "w") as out:
            out.write(formatted_header)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

# C generators
def new_c_object(name, directory, mode):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_object = ""

        if mode == objectutil_modes.default:
            formatted_object = c_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
            )
        elif mode == objectutil_modes.clean:
            formatted_object = clean_c_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
            )
        elif mode == objectutil_modes.modded:
            formatted_object = mod_c_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
            )
        elif mode == objectutil_modes.modded_clean:
            formatted_object = clean_mod_c_object.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
            )

        with open(directory, "w") as out:
            out.write(formatted_object)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

def new_c_object_header(name, directory, mode):
    directory_validate(directory)

    if os.path.exists(directory):
        app.add_line(f"Object '{name}' already exists in '{directory}'.")
        return

    try:
        formatted_header = ""

        if mode == objectutil_modes.default:
            formatted_header = c_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
                obj_name_up=name.upper()
            )
        elif mode == objectutil_modes.clean:
            formatted_header = clean_c_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
                obj_name_up=name.upper()
            )
        elif mode == objectutil_modes.modded:
            formatted_header = mod_c_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
                obj_name_up=name.upper()
            )
        elif mode == objectutil_modes.modded_clean:
            formatted_header = clean_mod_c_object_header.format(
                gameapi_inc_path=config.GAMEAPI_INC_PATH,
                obj_name=name,
                obj_name_up=name.upper()
            )

        with open(directory, "w") as out:
            out.write(formatted_header)

    except Exception as e:
        app.add_line(f"Error during file generation: {str(e)}")

#
# [projectutil]
#

def cpp_public_functions():
    events = ("Update", "LateUpdate", "StaticUpdate", "Draw", "Create", "StageLoad", "EditorDraw", "EditorLoad", "StaticLoad", "Serialize")
    exclusions = ["*", "_DECLARE"]

    app.set_terminal_progress(3, 0)

    with open(config.PUB_FNS_PATH, "w") as f:
        f.write('#pragma once\n')
        f.write(f'#include "{config.GAMEAPI_INC_PATH}"')
        f.write('\n\nusing namespace RSDK;\n\n')
        f.write('#if RETRO_USE_MOD_LOADER\n')

        f.write('#define ADD_PUBLIC_FUNC(func) GameLogic::AddPublicFunction(#func, &func)\n\n');

        f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n')

        f.write('\ntemplate <typename X, typename Type> inline static void AddPublicFunction(const char *functionName, Type(X::*functionPtr))\n{\n')
        f.write('    modTable->AddPublicFunction(functionName, reinterpret_cast<void *&>(functionPtr));\n')
        f.write('}\n')

        f.write('template <typename Type> inline static void AddPublicFunction(const char *functionName, Type(*functionPtr))\n{\n')
        f.write('    modTable->AddPublicFunction(functionName, reinterpret_cast<void *&>(functionPtr));\n')
        f.write('}\n')

        f.write('\nstatic void InitPublicFunctions()\n{\n')
        for path in Path(config.OBJECT_PATH).rglob("*.hpp"):
            done = False
            prepros = ""
            hasPrepos = False
            with open(path, "r") as file:
                for line in file:
                    line = line.rstrip()
                    if (match := re.fullmatch(r"\s*(?:static )?([a-zA-Z0-9:<>]* ?\**) *([a-zA-Z0-9_]*)\((.*)(?:,|\);)(?:\s*\/\/.*)?", line)) != None:
                        ret_type, name, args = match.groups()
                        ret_type = ret_type.strip()
                        name = name.strip()

                        for exclusion in exclusions:
                            name = name.replace(exclusion, '')
                        name = name.strip()

                        if name in events or not name:
                            continue

                        if (not done):
                            f.write(f"    // {path.parent.name}/{path.stem}\n")
                            done = True
                            if (prepros == "#endif"):
                                prepros = ""
                                hasPrepos = False

                        if prepros and (prepros != "#endif"):
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = True

                        if (prepros == "#endif" and hasPrepos == True):
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = False

                        f.write(f"    ADD_PUBLIC_FUNC({path.stem}::{name});\n")

                        if prepros == "#endif":
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = False
                    elif line.startswith("#"):
                        prepros = line
                    else:
                        prepros = ""

            if hasPrepos:
                f.write("#endif\n")
            if done:
                f.write("\n")

        f.write("} // static void InitPublicFunctions\n\n")
        f.write(f'}} // namespace {config.OBJECT_NAMESPACE}\n\n')
        f.write('#endif')

def c_public_functions():
    events = ("Update", "LateUpdate", "StaticUpdate", "Draw", "Create", "StageLoad", "EditorDraw", "EditorLoad", "StaticLoad", "Serialize")

    with open(config.PUB_FNS_PATH, "w") as f:
        f.write('#define ADD_PUBLIC_FUNC(func) Mod.AddPublicFunction(#func, (void *)(func))\n\n')
        f.write('void InitPublicFunctions()\n{\n')
        for path in Path(config.OBJECT_PATH).rglob("*.h"):
            done = False
            prepros = ""
            hasPrepos = False
            with open(path, "r") as file:
                while (line := file.readline()) != "":
                    if (line != line.lstrip() or line.startswith("//")):
                        continue
                    line = line.rstrip()
                    if (match := re.fullmatch(r"([a-zA-Z0-9]* ?\**) *([^(]*)\((.*)(,|\);)(\s*\/\/.*)?", line)) != None:
                        ret, name, args, end, comment = match.groups()
                        if name[len(path.stem) + 1:] in events:
                            continue
                        if (not done):
                            f.write(f"    // {path.parent.name}/{path.stem}\n")
                            done = True
                            if (prepros == "#endif"):
                                prepros = ""
                                hasPrepos = False
                        if prepros and (prepros != "#endif"):
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = True
                        if (prepros == "#endif" and hasPrepos == True):
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = False
                        f.write(f"    ADD_PUBLIC_FUNC({name});\n")
                        if (prepros == "#endif"):
                            f.write(f"{prepros}\n")
                            prepros = ""
                            hasPrepos = False
                    elif line.startswith("#"):
                        prepros = line
                    else:
                        prepros = ""
            if (hasPrepos):
                f.write("#endif\n")
            if (done):
                f.write('\n')
        f.write("}\n")

class gameapi_util:

    ## ---------------
    ## Menu Functions
    ## ---------------

    def __init__(self):
        self.tempVal = 0
        self.tempVal2 = 0

        self.options = []
        self.selection = 1
        self.body = urwid.SimpleListWalker([])
        header_txt = urwid.Text("gameapi_util\n", align='left')
        footer_txt = urwid.Text("1.1.0.1 - Navigate with Up/Down, Enter to select. ⏎", align='left')

        self.layout = urwid.Frame(
            header=urwid.AttrMap(header_txt, None),
            body=menuutil_listbox(self.body),
            footer=urwid.AttrMap(footer_txt, 'footer'),
        )

        self.obj_name_field = None
        self.directories = []
        self.state = self.loop_main_menu

    def run(self):
        self.menu_refresh_main()
        palette = [
            ('selected', 'standout', ''),
            ('not_selected', '', ''),
            ('item_disabled', 'dark gray', ''),
            ('footer', 'dark gray', ''),
        ]
        loop = urwid.MainLoop(self.layout, palette=palette, unhandled_input=lambda key: self.state(key))

        try:
            loop.run()
        except KeyboardInterrupt:
            pass

    def set_terminal_progress(self, state, progress):
        # https://learn.microsoft.com/en-us/windows/terminal/tutorials/progress-bar-sequences
        # 0 is the default state, and indicates that the progress bar should be hidden. Use this state when the command is complete, to clear out any progress state.
        # 1: set progress value to <progress>, in the "default" state.
        # 2: set progress value to <progress>, in the "Error" state
        # 3: set the taskbar to the "Indeterminate" state. This is useful for commands that don't have a progress value, but are still running. This state ignores the <progress> value.
        # 4: set progress value to <progress>, in the "Warning" state

        progress = max(0, min(100, progress))
        sys.stdout.write(f"\x1b]9;4;{state};{progress}\x07")
        sys.stdout.flush()

    ##
    ## [ Menu UI Items ]
    ##

    def menu_add_cpp_tools(self):
        self.add_label("[C++ Tools]")
        self.add_option('Project Update', lambda: self.project_update(0))
        self.add_option('Generate Public Functions', lambda: self.gen_pub_fns(0))
        self.add_option('New Object [default]', lambda: self.create_object(0, objectutil_modes.default))
        self.add_option('New Object [clean]', lambda: self.create_object(0, objectutil_modes.clean))
        self.add_option('New Object [modded]', lambda: self.create_object(0, objectutil_modes.modded))
        self.add_option('New Object [modded][clean]', lambda: self.create_object(0, objectutil_modes.modded_clean))

    def menu_add_c_tools(self):
        self.add_label("[C Tools]")
        self.add_option('Project Update', lambda: self.project_update(1))
        self.add_option('Generate Public Functions', lambda: self.gen_pub_fns(1))
        self.add_option('New Object [default]', lambda: self.create_object(1, objectutil_modes.default))
        self.add_option('New Object [clean]', lambda: self.create_object(1, objectutil_modes.clean))
        self.add_option('New Object [modded]', lambda: self.create_object(1, objectutil_modes.modded))
        self.add_option('New Object [modded][clean]', lambda: self.create_object(1, objectutil_modes.modded_clean))

    def spacer(self):
        self.add_label()

    def add_line(self, txt):
        self.body.append(urwid.Text(txt))

    def add_option(self, label, onSelectCB):
        self.options.append({'label': label, 'onSelectCB': onSelectCB})

    def add_label(self, label='', attr=None):
        self.options.append({'label': label, 'onSelectCB': None, 'item_skip_select': True})

    ##
    ## [ Menu Functionality ]
    ##

    def update_ui_selectable(self, option, selected=False):
        text = f"> {option['label']}" if selected else f"- {option['label']}"
        attr = 'selected' if selected else 'not_selected'
        return urwid.AttrMap(urwid.Text(text), attr)

    def menu_refresh_main(self):
        if not self.options:
            return

        self.body.clear()
        for i, option in enumerate(self.options):
            if option.get('item_skip_select'):
                divider = urwid.Text(option['label'])
                attr = option.get('attr', 'not_selected')
                self.body.append(urwid.AttrMap(divider, attr))
            else:
                self.body.append(self.update_ui_selectable(option, selected=(i == self.selection)))

    def menu_refresh_objects(self):
        directory_select_walker = urwid.SimpleListWalker(
            [urwid.AttrMap(urwid.Text(f"> {dir_name}" if i == self.selection else f"- {dir_name}"),
                        'selected' if i == self.selection else 'not_selected')
            for i, dir_name in enumerate(self.directories)]
        )
        self.layout.body = menuutil_listbox(directory_select_walker)

    def success_msg_generic(self):
        self.set_terminal_progress(0, 0)
        self.add_line('Done! Press any key to return to the main menu.')
        self.selection = 1
        self.state = self.loop_wait_for_return

    ##
    ## [ Menu States ]
    ##

    def loop_main_menu(self, key):
        self.set_terminal_progress(0, 0)

        if key in ('up', 'k'):
            self.selection = (self.selection - 1) % len(self.options)
            while self.options[self.selection].get('item_skip_select'):
                self.selection = (self.selection - 1) % len(self.options)
            self.menu_refresh_main()
            self.layout.body.scroll(self.selection)
        elif key in ('down', 'j'):
            self.selection = (self.selection + 1) % len(self.options)
            while self.options[self.selection].get('item_skip_select'):
                self.selection = (self.selection + 1) % len(self.options)
            self.menu_refresh_main()
            self.layout.body.scroll(self.selection)
        elif key == 'enter':
            if not self.options[self.selection].get('item_skip_select'):
                self.body.clear()
                _label = self.options[self.selection]['label']
                self.add_line(f"> Selected {_label}\n")
                self.options[self.selection]['onSelectCB']()
        else:
            self.menu_refresh_main()

    def loop_create_object(self, key):
        if key == 'esc':
            self.selection = 0
            self.state = self.loop_main_menu
            self.menu_refresh_main()
        elif key == 'enter':
            if not os.path.exists(config.OBJECT_PATH):
                self.set_terminal_progress(2, 100)
                self.add_line(f"{config.OBJECT_PATH} does not exist. Press any key to return to the main menu.")
                self.layout.body = menuutil_listbox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            if not os.path.isdir(config.OBJECT_PATH):
                self.set_terminal_progress(2, 100)
                self.add_line(f"{config.OBJECT_PATH} is not a directory. Press any key to return to the main menu.")
                self.layout.body = menuutil_listbox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            obj_name = self.obj_name_field.get_edit_text()
            if not obj_name:
                self.set_terminal_progress(4, 100)
                self.add_line("No name was provided. Press any key to return to the main menu.")
                self.layout.body = menuutil_listbox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            self.obj_name = obj_name

            self.directories = [d for d in os.listdir(config.OBJECT_PATH) if os.path.isdir(os.path.join(config.OBJECT_PATH, d))]
            if not self.directories:
                self.set_terminal_progress(2, 100)
                self.add_line(f"No valid object directories found. Please create a subdirectory in {config.OBJECT_PATH}")
                self.layout.body = menuutil_listbox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            directory_select_walker = urwid.SimpleListWalker([urwid.Text(f"- {dir_name}") for dir_name in self.directories])
            self.layout.body = menuutil_listbox(directory_select_walker)
            self.selection = 0
            self.menu_refresh_objects()
            self.state = self.loop_select_directory

    def loop_select_directory(self, key):
        if key in ('up', 'k'):
            self.selection = (self.selection - 1) % len(self.directories)
            self.menu_refresh_objects()
            self.layout.body.scroll(self.selection)
        elif key in ('down', 'j'):
            self.selection = (self.selection + 1) % len(self.directories)
            self.menu_refresh_objects()
            self.layout.body.scroll(self.selection)
        elif key == 'enter':
            selected_dir = self.directories[self.selection]
            object_dir = os.path.join(config.OBJECT_PATH, selected_dir)

            codePath = ""
            headerPath = ""

            if self.tempVal2 == 0: # C++
                codePath = os.path.join(object_dir, f"{self.obj_name}.cpp")
                headerPath = os.path.join(object_dir, f"{self.obj_name}.hpp")
            elif self.tempVal2 == 1: # C
                codePath = os.path.join(object_dir, f"{self.obj_name}.c")
                headerPath = os.path.join(object_dir, f"{self.obj_name}.h")

            if os.path.exists(codePath) or os.path.exists(headerPath):
                self.add_line(f"Object '{self.obj_name}' already exists in '{selected_dir}'. Press any key to return to the main menu.")
                self.layout.body = menuutil_listbox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            try:
                if self.tempVal2 == 0: # C++
                    new_cpp_object(self.obj_name, codePath, self.tempVal)
                    new_cpp_object_header(self.obj_name, headerPath, self.tempVal)
                elif self.tempVal2 == 1: # C
                    new_c_object(self.obj_name, codePath, self.tempVal)
                    new_c_object_header(self.obj_name, headerPath, self.tempVal)

                self.directories.clear()
                self.layout.body = menuutil_listbox(self.body)

                self.add_line(f"Done! Created '{self.obj_name}' in directory '{selected_dir}'.")
                self.add_line("Would you like to update the CMake project? (Y/N)")
                self.state = self.loop_create_object_update_prompt

            except Exception as e:
                self.set_terminal_progress(2, 100)
                self.add_line(f"This wasn't supposed to happen... {str(e)}")
                self.state = self.loop_main_menu

    def loop_create_object_update_prompt(self, key):
        if key in ('y', 'Y'):
            self.project_update(self.tempVal2)
            self.tempVal = 0
            self.tempVal2 = 0
            self.state = self.loop_main_menu
        else:
            self.tempVal = 0
            self.tempVal2 = 0
            self.state = self.loop_main_menu
            self.menu_refresh_main()

    def loop_wait_for_return(self, key):
        self.state = self.loop_main_menu
        self.menu_refresh_main()

    ##
    ## [ Implementation ]
    ##

    def project_update(self, mode=0):
        filenames = []
        self.add_line(f'Generating {config.ALL_CODE_NAME}, {config.ALL_HEADER_NAME}')

        codeExtension = ""
        headerExtension = ""
        if mode == 0: # C++
            codeExtension = ".cpp"
            headerExtension = ".hpp"
        elif mode == 1: # C
            codeExtension = ".c"
            headerExtension = ".h"

        for dir_, _, files in os.walk(config.OBJECT_PATH):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, config.OBJECT_PATH)
                filenames.append(f"{rel_dir}/{file_name}")

            obj_rel_dir = '' if os.path.dirname(config.ALL_CODE_PATH) == config.OBJECT_PATH else os.path.relpath(config.OBJECT_PATH, os.path.dirname(config.ALL_CODE_PATH)).replace("\\","/") + '/'
            obj_includes = [
                f'#include "{name}"\n'
                for f in filenames
                if f.endswith(codeExtension) and not f.endswith(config.ALL_CODE_NAME)
                for name in [obj_rel_dir + f]
            ]

            with open(config.ALL_CODE_PATH, "w") as f:
                f.writelines(obj_includes)

            obj_forward_decl = [
                f'typedef struct Object{name} Object{name};\ntypedef struct Entity{name} Entity{name};\n' if mode == 1 else f'struct {name};\n'
                for f in filenames
                if f.endswith(headerExtension) and not f.endswith(config.ALL_HEADER_NAME)
                for name in [os.path.splitext(os.path.basename(f))[0]]
            ]

            obj_rel_dir = '' if os.path.dirname(config.ALL_HEADER_PATH) == config.OBJECT_PATH else os.path.relpath(config.OBJECT_PATH, os.path.dirname(config.ALL_HEADER_PATH)).replace("\\","/") + '/'
            obj_includes = [
                f'#include "{name}"\n'
                for f in filenames
                if f.endswith(headerExtension) and not f.endswith(config.ALL_HEADER_NAME)
                for name in [obj_rel_dir + f]
            ]

            if mode == 0: # C++
                with open(config.ALL_HEADER_PATH, "w") as f:
                    f.write('#pragma once\n')
                    f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n\n')
                    f.writelines(obj_forward_decl)
                    f.write(f'\n}} // namespace {config.OBJECT_NAMESPACE}\n\n')
                    f.writelines(obj_includes)
            elif mode == 1: # C
                with open(config.ALL_HEADER_PATH, "w") as f:
                    f.write('// Forward Declarations\n')
                    f.writelines(obj_forward_decl)
                    f.writelines('\n')
                    f.writelines(obj_includes)

        self.add_line(f"Generating {config.CMAKE_PATH}")
        files = [f"\t{config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + cm + "\n" for cm in filenames if cm.endswith(codeExtension) and not cm.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as cm:
            cm.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.success_msg_generic()


    def gen_pub_fns(self, mode=0):
        self.add_line("WARNING: Manual fixing may be required for public function generation")

        if os.path.exists(config.PUB_FNS_PATH):
            self.add_line(f"\n'{config.PUB_FNS_PATH}' already exists. Overwrite? (Y/N)")

            def loop_confirm(key):
                if key in ('y', 'Y'):
                    self.gen_pub_dns_imp(mode)
                elif key in ('n', 'N'):
                    self.selection = 1
                    self.state = self.loop_main_menu
                    self.menu_refresh_main()

            self.state = loop_confirm
            return

        self.gen_pub_dns_imp(mode)

    def gen_pub_dns_imp(self, mode=0):
        self.set_terminal_progress(3, 0)

        if mode == 0: # C++
            cpp_public_functions()
        elif mode == 1: # C
            c_public_functions()
        self.success_msg_generic()

    def create_object(self, language=0, mode=objectutil_modes.default):
        self.state = self.loop_create_object
        self.obj_name_field = urwid.Edit("Object Name: ")
        self.tempVal = mode
        self.tempVal2 = language

        dir_lbl = urwid.AttrMap(urwid.Text("\n> Object Directories: ..."), 'item_disabled')


        input_body = urwid.SimpleListWalker([
            urwid.AttrMap(self.obj_name_field, None),
            dir_lbl
        ])
        self.layout.body = menuutil_listbox(input_body)

    def exit_util(self):
        self.set_terminal_progress(0, 0)
        raise urwid.ExitMainLoop()

def main():
    global app
    app = gameapi_util()

    if config.skipDefaultTools == False:
        app.menu_add_cpp_tools()
        app.spacer()

        app.menu_add_c_tools()
        app.spacer()

    config.init(app)
    app.add_option("Exit", app.exit_util)
    app.run()

if __name__ == '__main__':
    main()
