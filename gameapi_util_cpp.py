import os
import re
import urwid
from pathlib import Path
import gameapi_util_cfg as config

class gameapi_util:
    def __init__(self):
        self.options = []
        self.selection = 0
        self.body = urwid.SimpleListWalker([])
        header_txt = urwid.Text("gameapi_util (C++)\n", align='left')
        footer_txt = urwid.Text("Navigate with Up/Down, Enter to select. ⏎", align='left')
        self.layout = urwid.Frame(
            header=urwid.AttrMap(header_txt, None),
            body=urwid.ListBox(self.body),
            footer=urwid.AttrMap(footer_txt, None),
        )
        self.obj_name_field = None
        self.directories = []
        self.state = self.loop_main_menu
    # __init__ -> (self)

    def run(self):
        self.refresh_main_menu()
        palette = [
            ('selected', 'standout', ''),
            ('not_selected', '', '')
        ]
        loop = urwid.MainLoop(self.layout, palette=palette, unhandled_input=lambda key: self.state(key))

        try:
            loop.run()
        except KeyboardInterrupt:
            pass
    # run -> (self)

    def add_line(self, txt):
        self.body.append(urwid.Text(txt))
    # add_line -> (self, txt)

    def add_option(self, label, onSelectCB):
        self.options.append({'label': label, 'onSelectCB': onSelectCB})
    # add_option -> (self, label, onSelectCB)

    def success_msg_generic(self):
        self.add_line('Done! Press any key to return to the main menu.')
        self.selection = 0
        self.state = self.loop_wait_for_return
    # success_msg_generic -> (self)

    def refresh_main_menu(self):
        self.body.clear()
        for i, option in enumerate(self.options):
            self.body.append(self.update_option(option, selected=(i == self.selection)))
    # refresh_main_menu -> (self)

    def refresh_obj_dir_menu(self):
        directory_select_walker = urwid.SimpleListWalker(
            [urwid.AttrMap(urwid.Text(f"> {dir_name}" if i == self.selection else f"- {dir_name}"), 
                        'selected' if i == self.selection else 'not_selected')
            for i, dir_name in enumerate(self.directories)]
        )
        self.layout.body = urwid.ListBox(directory_select_walker)
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
            self.body.clear()
            _label = self.options[self.selection]['label']
            self.add_line(f"> {_label}\n")
            self.options[self.selection]['onSelectCB']()
        else:
            self.refresh_main_menu()
    # loop_main_menu -> (self, key)

    def loop_create_object(self, key):
        if key == 'esc':
            self.selection = 0
            self.state = self.loop_main_menu
            self.refresh_main_menu()
        elif key == 'enter':
            if not os.path.exists(config.OBJECT_PATH):
                self.add_line(f"{config.OBJECT_PATH} does not exist. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return

            if not os.path.isdir(config.OBJECT_PATH):
                self.add_line(f"{config.OBJECT_PATH} is not a directory. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return
        
            obj_name = self.obj_name_field.get_edit_text()
            if not obj_name:
                self.add_line("You're gonna need a name for the object.\n")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return

            self.obj_name = obj_name 

            self.directories = [d for d in os.listdir(config.OBJECT_PATH) if os.path.isdir(os.path.join(config.OBJECT_PATH, d))]
            if not self.directories:
                self.add_line("\nNo valid object directories found.\n")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return
        
            directory_select_walker = urwid.SimpleListWalker([urwid.Text(f"- {dir_name}") for dir_name in self.directories])
            self.layout.body = urwid.ListBox(directory_select_walker)
            self.selection = 0
            self.refresh_obj_dir_menu()
            self.state = self.loop_select_directory
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
            object_dir = os.path.join(config.OBJECT_PATH, selected_dir)
            codePath = os.path.join(object_dir, f"{self.obj_name}.cpp")
            headerPath = os.path.join(object_dir, f"{self.obj_name}.hpp")

            if os.path.exists(codePath) or os.path.exists(headerPath):
                self.add_line(f"Object '{self.obj_name}' already exists in '{selected_dir}'. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return

            try:
                with open(codePath, "w") as cpp_out:
                    cpp_out.write(f'#include "{config.GAMEAPI_INC_PATH}"\n\n')
                    cpp_out.write('using namespace RSDK;\n\n')
                    cpp_out.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n\n')

                    cpp_out.write('// -------------------\n')
                    cpp_out.write('// Object Registration\n')
                    cpp_out.write('// -------------------\n\n')
                    cpp_out.write(f'RSDK_REGISTER_OBJECT({self.obj_name});\n\n')

                    cpp_out.write('// -------------\n')
                    cpp_out.write('// Entity Events\n')
                    cpp_out.write('// -------------\n\n')
                    cpp_out.write(f'void {self.obj_name}::Update() {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::LateUpdate() {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::StaticUpdate() {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::Draw() {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::Create(void* data) {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::StageLoad() {{}}\n\n')

                    cpp_out.write('#if GAME_INCLUDE_EDITOR\n')
                    cpp_out.write(f'void {self.obj_name}::EditorLoad() {{}}\n\n')
                    cpp_out.write(f'void {self.obj_name}::EditorDraw() {{}}\n')
                    cpp_out.write('#endif\n\n')

                    cpp_out.write('#if RETRO_REV0U\n')
                    cpp_out.write(f'void {self.obj_name}::StaticLoad(Static* sVars) {{ RSDK_INIT_STATIC_VARS({self.obj_name}); }}\n')
                    cpp_out.write('#endif\n\n')

                    cpp_out.write(f'void {self.obj_name}::Serialize() {{}}\n\n')

                    cpp_out.write(f'}} // namespace {config.OBJECT_NAMESPACE}')

                with open(headerPath, "w") as hpp_out:
                    hpp_out.write('#pragma once\n')
                    hpp_out.write(f'#include "{config.GAMEAPI_INC_PATH}"\n\n')
                    hpp_out.write('using namespace RSDK;\n\n')
                    hpp_out.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n')
                    hpp_out.write(f'struct {self.obj_name} : GameObject::Entity {{\n\n')

                    hpp_out.write('    // ---------------\n')
                    hpp_out.write('    // Enums & Structs\n')
                    hpp_out.write('    // ---------------\n\n')

                    hpp_out.write('    // ----------------\n')
                    hpp_out.write('    // Static Variables\n')
                    hpp_out.write('    // ----------------\n\n')

                    hpp_out.write('    struct Static : GameObject::Static {\n    };\n\n')

                    hpp_out.write('    // ----------------\n')
                    hpp_out.write('    // Entity Variables\n')
                    hpp_out.write('    // ----------------\n\n')

                    hpp_out.write('    // ----------------------\n')
                    hpp_out.write('    // Standard Entity Events\n')
                    hpp_out.write('    // ----------------------\n\n')

                    hpp_out.write('    void Create(void* data);\n')
                    hpp_out.write('    void Draw();\n')
                    hpp_out.write('    void Update();\n')
                    hpp_out.write('    void LateUpdate();\n')
                    hpp_out.write('    static void StaticUpdate();\n')
                    hpp_out.write('    static void StageLoad();\n')
                    hpp_out.write('#if GAME_INCLUDE_EDITOR\n')
                    hpp_out.write('    static void EditorLoad();\n')
                    hpp_out.write('    void EditorDraw();\n')
                    hpp_out.write('#endif\n')
                    hpp_out.write('#if RETRO_REV0U\n')
                    hpp_out.write('    static void StaticLoad(Static* sVars);\n')
                    hpp_out.write('#endif\n')
                    hpp_out.write('    static void Serialize();\n\n')

                    hpp_out.write('    // ----------------------\n')
                    hpp_out.write('    // Extra Entity Functions\n')
                    hpp_out.write('    // ----------------------\n\n')

                    hpp_out.write('    // -------------\n')
                    hpp_out.write('    // Object States\n')
                    hpp_out.write('    // -------------\n\n')

                    hpp_out.write('    // ------------------\n')
                    hpp_out.write('    // Object Draw States\n')
                    hpp_out.write('    // ------------------\n\n')

                    hpp_out.write('    // -------------------\n')
                    hpp_out.write('    // Static Declarations\n')
                    hpp_out.write('    // -------------------\n\n')
                    hpp_out.write(f'    RSDK_DECLARE({self.obj_name})\n')

                    hpp_out.write(f'}};\n')
                    hpp_out.write(f'}} // namespace {config.OBJECT_NAMESPACE}')

                self.directories.clear()
                self.layout.body = urwid.ListBox(self.body)

                self.add_line(f"Done! Created '{self.obj_name}' in directory '{selected_dir}'.")
                self.add_line("Would you like to update the CMake project? (Y/N)")
                self.state = self.loop_create_object_update_prompt

            except Exception as e:
                self.add_line(f"This wasn't supposed to happen... {str(e)}")
                self.state = self.loop_main_menu
                self.refresh_main_menu()
    # loop_select_directory -> (self, key)

    def loop_create_object_update_prompt(self, key):
        if key in ('y', 'Y'):
            self.project_update()
            self.state = self.loop_main_menu
        elif key in ('n', 'N'):
            self.add_line("Skipped project update. Press any key to return to the main menu.")
            self.state = self.loop_main_menu
    # loop_create_object_update_prompt -> (self, key)

    def loop_wait_for_return(self, key):
        self.state = self.loop_main_menu
        self.refresh_main_menu()
    # loop_wait_for_return -> (self, key)

    def project_update(self):
        filenames = []
        self.add_line(f'Generating {config.ALL_CODE_NAME}, {config.ALL_HEADER_NAME}')
        for dir_, _, files in os.walk(config.OBJECT_PATH):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, config.OBJECT_PATH)
                filenames.append(f"{rel_dir}/{file_name}")

            with open(f'{config.OBJECT_PATH}/{config.ALL_CODE_NAME}', "w") as f:
                f.writelines(f'#include "{f}"\n' for f in filenames if f.endswith(".cpp") and not f.endswith(config.ALL_CODE_NAME))

            obj_forward_decl = [f'typedef struct {os.path.splitext(os.path.basename(f))[0]} {os.path.splitext(os.path.basename(f))[0]};\n' for f in filenames if f.endswith(".hpp") and not f.endswith(config.ALL_HEADER_NAME)]
            obj_includes = [f'#include "{config.OBJECT_PATH_NAME}/{f}"\n' for f in filenames if f.endswith(".hpp") and not f.endswith(config.ALL_HEADER_NAME)]

            with open(f'{config.GAME_PATH}/{config.ALL_HEADER_NAME}', "w") as f:
                f.write('#pragma once\n')
                f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n\n')
                f.writelines(obj_forward_decl)
                f.write(f'\n}} // namespace {config.OBJECT_NAMESPACE}\n\n')
                f.writelines(obj_includes)

        self.add_line(f"Generating {config.CMAKE_PATH}")
        files = [f"\t{config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + cm + "\n" for cm in filenames if cm.endswith(".cpp") and not cm.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as cm:
            cm.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.success_msg_generic()
    # project_update -> (self)

    def gen_pub_fns(self):
        self.add_line("WARNING: Manual fixing may be required for public function generation")

        if os.path.exists(config.PUB_FNS_PATH):
            self.add_line(f"\n'{config.PUB_FNS_PATH}' already exists. Overwrite? (Y/N)")
            
            def loop_confirm(key):
                if key in ('y', 'Y'):
                    self.gen_pub_dns_imp()
                elif key in ('n', 'N'):
                    self.selection = 0
                    self.state = self.loop_main_menu
                    self.refresh_main_menu()

            self.state = loop_confirm
            return
        
        self.gen_pub_dns_imp()
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
            f.write(f'}} // namespace {config.OBJECT_NAMESPACE}\n\n')    # // namespace GameLogic
            f.write('#endif')

        self.success_msg_generic()
    # gen_pub_fns_imp -> (self)

    def create_object(self):
        self.state = self.loop_create_object
        self.obj_name_field = urwid.Edit("Object Name: ")

        input_body = urwid.SimpleListWalker([urwid.AttrMap(self.obj_name_field, None)])
        self.layout.body = urwid.ListBox(input_body)
    # create_object -> (self)

    def exit_util(self):
        raise urwid.ExitMainLoop()
    # exit_util -> (self)

def main():
    app = gameapi_util()
    if config.skipDefaultTools == False:
        app.add_option('Project Update', app.project_update)
        app.add_option('Generate Public Functions', app.gen_pub_fns)
        app.add_option('Create Object', app.create_object)
    config.init(app)
    app.add_option("Exit", app.exit_util)
    app.run()
# main -> ()

if __name__ == '__main__':
    main()
