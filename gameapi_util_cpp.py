import urwid
import gameapi_util_cfg as config
import os
from pathlib import Path
import re

class gameapi_util:
    def __init__(self):
        self.options = []
        self.selection = 0
        self.header_text = urwid.Text("gameapi_util (C++)\n", align='left')
        self.footer_text = urwid.Text("Navigate with Up/Down, Enter to select.", align='left')
        self.main_body = urwid.SimpleListWalker([])
        self.main_layout = urwid.Frame(
            header=urwid.AttrMap(self.header_text, None),
            body=urwid.ListBox(self.main_body),
            footer=urwid.AttrMap(self.footer_text, None),
        )
        self.obj_name_field = None
        self.directories = []
        self.loopState = self.loop_main_menu
    # __init__ -> (self)

    def run(self):
        self.refresh_main_menu()
        palette = [
            ('selected', 'standout', ''),
            ('not_selected', '', '')
        ]
        loop = urwid.MainLoop(self.main_layout, palette=palette, unhandled_input=lambda key: self.loopState(key))

        try:
            loop.run()
        except KeyboardInterrupt:
            pass
    # run -> (self)

    def add_line(self, txt):
        self.main_body.append(urwid.Text(txt))
    # add_line -> (self, txt)

    def add_option(self, label, onSelectCB):
        self.options.append({'label': label, 'onSelectCB': onSelectCB})
    # add_option -> (self, label, onSelectCB)

    def success_msg_generic(self):
        self.add_line('Done! Press any key to return to the main menu.')
        self.selection = 0
        self.loopState = self.loop_wait_for_return
    # success_msg_generic -> (self)

    def refresh_main_menu(self):
        self.main_body.clear()
        for i, option in enumerate(self.options):
            self.main_body.append(self.update_option(option, selected=(i == self.selection)))
    # refresh_main_menu -> (self)

    def refresh_obj_dir_menu(self):
        directory_select_walker = urwid.SimpleListWalker(
            [urwid.AttrMap(urwid.Text(f"> {dir_name}" if i == self.selection else f"- {dir_name}"), 
                        'selected' if i == self.selection else 'not_selected')
            for i, dir_name in enumerate(self.directories)]
        )
        self.main_layout.body = urwid.ListBox(directory_select_walker)
    # refresh_obj_dir_menu -> (self)

    def update_option(self, option, selected=False):
        text = f"> {option['label']}" if selected else f"- {option['label']}"
        attr = 'selected' if selected else 'not_selected'
        return urwid.AttrMap(urwid.Text(text), attr)
    # update_option -> (self, key)

    def loop_main_menu(self, key):
        if key in ('up', 'k'):
            self.selection = (self.selection - 1) % len(self.options)
            self.refresh_main_menu()
        elif key in ('down', 'j'):
            self.selection = (self.selection + 1) % len(self.options)
            self.refresh_main_menu()
        elif key == 'enter':
            self.main_body.clear()
            _label = self.options[self.selection]['label']
            self.add_line(f"> {_label}\n")
            self.options[self.selection]['onSelectCB']()
        else:
            self.refresh_main_menu()
    # loop_main_menu -> (self, key)

    def loop_create_object(self, key):
        if key == 'esc':
            self.selection = 0
            self.loopState = self.loop_main_menu
            self.refresh_main_menu()
        elif key == 'enter':
            obj_name = self.obj_name_field.get_edit_text()
            if not obj_name:
                self.add_line("You're gonna need a name for the object.\n")
                self.loopState = self.loop_main_menu
                self.refresh_main_menu()
                return

            self.obj_name = obj_name 

            self.directories = [d for d in os.listdir(config.OBJECT_PATH) if os.path.isdir(os.path.join(config.OBJECT_PATH, d))]
            if not self.directories:
                self.add_line("\nNo valid object directories found.\n")
                self.loopState = self.loop_main_menu
                self.refresh_main_menu()
                return
        
            directory_select_walker = urwid.SimpleListWalker([urwid.Text(f"- {dir_name}") for dir_name in self.directories])
            self.main_layout.body = urwid.ListBox(directory_select_walker)
            self.selection = 0
            self.refresh_obj_dir_menu()
            self.loopState = self.loop_select_directory
    # loop_create_object -> (self, key)

    def loop_select_directory(self, key):
        if key in ('up', 'k'):
            self.selection = (self.selection - 1) % len(self.directories)
            self.refresh_obj_dir_menu()
        elif key in ('down', 'j'):
            self.selection = (self.selection + 1) % len(self.directories)
            self.refresh_obj_dir_menu()
        elif key == 'enter':
            selected_dir = self.directories[self.selection]
            obj_dir = os.path.join(config.OBJECT_PATH, selected_dir)
            cpp_path = os.path.join(obj_dir, f"{self.obj_name}.cpp")
            hpp_path = os.path.join(obj_dir, f"{self.obj_name}.hpp")

            if os.path.exists(cpp_path) or os.path.exists(hpp_path):
                self.add_line(f"Object '{self.obj_name}' already exists in '{selected_dir}'. Press any key to return to the main menu.")
                self.main_layout.body = urwid.ListBox(self.main_body)
                self.selection = 0
                self.loopState = self.loop_wait_for_return
                return

            object_cpp = f"""#include "{config.GAMEAPI_INC_PATH}"

using namespace RSDK;

namespace {config.OBJECT_NAMESPACE}
{{

// -------------------
// Object Registration
// -------------------

RSDK_REGISTER_OBJECT({self.obj_name});

// -------------
// Entity Events
// -------------

void {self.obj_name}::Update() {{}}

void {self.obj_name}::LateUpdate() {{}}

void {self.obj_name}::StaticUpdate() {{}}

void {self.obj_name}::Draw() {{}}

void {self.obj_name}::Create(void *data) {{}}

void {self.obj_name}::StageLoad() {{}}

#if GAME_INCLUDE_EDITOR
void {self.obj_name}::EditorLoad() {{}}

void {self.obj_name}::EditorDraw() {{}}
#endif

#if RETRO_REV0U
void {self.obj_name}::StaticLoad(Static *sVars) {{ RSDK_INIT_STATIC_VARS({self.obj_name}); }}
#endif

void {self.obj_name}::Serialize() {{}}

}} // namespace GameLogic
"""

            object_hpp = f"""#pragma once
#include "{config.GAMEAPI_INC_PATH}"

using namespace RSDK;

// ------------------
// Macros/Definitions
// ------------------

namespace {config.OBJECT_NAMESPACE}
{{
struct {self.obj_name} : GameObject::Entity {{

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

    void Create(void *data);
    void Draw();
    void Update();
    void LateUpdate();
    static void StaticUpdate();
    static void StageLoad();
#if RETRO_REV0U
    static void StaticLoad(Static *sVars);
#endif
    static void Serialize();

#if GAME_INCLUDE_EDITOR
    static void EditorLoad();
    void EditorDraw();
#endif

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

    RSDK_DECLARE({self.obj_name})
}};
}} // namespace GameLogic
"""
            try:
                with open(cpp_path, "w") as cpp_out:
                    cpp_out.write(object_cpp)

                with open(hpp_path, "w") as hpp_out:
                    hpp_out.write(object_hpp)

                self.directories.clear()
                self.main_layout.body = urwid.ListBox(self.main_body)

                self.success_msg_generic()

            except Exception as e:
                self.add_line(f"An error occurred: {str(e)}")
                self.loopState = self.loop_main_menu
                self.refresh_main_menu()
    # loop_select_directory -> (self, key)

    def loop_wait_for_return(self, key):
        self.loopState = self.loop_main_menu
        self.refresh_main_menu()
    # loop_wait_for_return -> (self, key)

    def project_update(self):
        filenames = []
        self.add_line(f'Generating {config.ALL_CODE_NAME}, {config.ALL_HEADER_NAME}')
        for dir_, _, files in os.walk(config.OBJECT_PATH):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, config.OBJECT_PATH)
                filenames.append(f"{rel_dir}/{file_name}")

            with open(config.ALL_CPP_PATH, "w") as f:
                f.writelines(f'#include "{f}"\n' for f in filenames if f.endswith(".cpp") and not f.endswith(config.ALL_CODE_NAME))

            obj_forward_decl = [f'typedef struct {os.path.splitext(os.path.basename(f))[0]} {os.path.splitext(os.path.basename(f))[0]};\n' for f in filenames if f.endswith(".hpp") and not f.endswith(config.ALL_HEADER_NAME)]
            obj_includes = [f'#include "{config.OBJECT_PATH_NAME}/{f}"\n' for f in filenames if f.endswith(".hpp") and not f.endswith(config.ALL_HEADER_NAME)]

            with open(config.ALL_HPP_PATH, "w") as f:
                f.write('#pragma once\n')
                f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n\n')
                f.writelines(obj_forward_decl)
                f.write(f'\n}} // namespace {config.OBJECT_NAMESPACE}\n\n')
                f.writelines(obj_includes)

        self.add_line(f"Generating {config.CMAKE_PATH}")
        files = [f"${config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + f + "\n" for f in filenames if f.endswith(".cpp") and not f.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as f:
            f.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.success_msg_generic()
    # project_update -> (self)

    def gen_pub_fns(self):
        self.add_line("WARNING: C++ Public function generation is experimental. Manual fixing may be required")

        if os.path.exists(config.PUB_FNS_PATH):
            self.add_line(f"\n'{config.PUB_FNS_PATH}' already exists. Overwrite? (Y/N)")
            
            def loop_confirm(key):
                if key in ('y', 'Y'):
                    self.gen_pub_dns_imp()
                elif key in ('n', 'N'):
                    self.selection = 0
                    self.loopState = self.loop_main_menu
                    self.refresh_main_menu()

            self.loopState = loop_confirm
            return
        
        self.gen_pub_dns_imp();
    # gen_pub_fns -> (self)

    def gen_pub_dns_imp(self):
        events = ("Update", "LateUpdate", "StaticUpdate", "Draw", "Create", "StageLoad", "EditorDraw", "EditorLoad", "StaticLoad", "Serialize")
        exclusions = ["*", "_DECLARE"]

        with open(config.PUB_FNS_PATH, "w") as f:
            f.write('#pragma once\n')
            f.write(f'#include "{config.GAMEAPI_INC_PATH}"')
            f.write('\n\nusing namespace RSDK;\n\n')
            f.write('#if RETRO_USE_MOD_LOADER\n')

            f.write('#define ADD_PUBLIC_FUNC(func) GameLogic::AddPublicFunction(#func, &func)\n\n');

            f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n') # namespace GameLogic

            f.write('\ntemplate <typename X, typename Type> inline static void AddPublicFunction(const char *functionName, Type(X::*functionPtr))\n{\n')
            f.write('    modTable->AddPublicFunction(functionName, reinterpret_cast<void *&>(functionPtr));\n')
            f.write('}\n')

            f.write('template <typename Type> inline static void AddPublicFunction(const char *functionName, Type(*functionPtr))\n{\n')
            f.write('    modTable->AddPublicFunction(functionName, reinterpret_cast<void *&>(functionPtr));\n')
            f.write('}\n')

            f.write(f'\nstatic void InitPublicFunctions()\n{{\n')
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
            f.write(f'}} // namespace {config.OBJECT_NAMESPACE}\n\n')    # // namespace GameLogic
            f.write('#endif')

        self.success_msg_generic()
    # gen_pub_fns_imp -> (self)

    def create_object(self):
        self.loopState = self.loop_create_object
        self.obj_name_field = urwid.Edit("Object Name: ")

        input_body = urwid.SimpleListWalker([urwid.AttrMap(self.obj_name_field, None)])
        self.main_layout.body = urwid.ListBox(input_body)
    # create_object -> (self)

    def exit_util(self):
        raise urwid.ExitMainLoop()
    # exit_util -> (self)

def main():
    app = gameapi_util()
    if config.skipDefaultTools == False:
        app.add_option('Project Update', app.project_update)
        app.add_option('Generate Public Functions (experimental)', app.gen_pub_fns)
        app.add_option('Create Object', app.create_object)
    config.init(app);
    app.add_option("Exit", app.exit_util)
    app.run()
# main -> ()

if __name__ == '__main__':
    main()
