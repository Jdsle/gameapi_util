import os
import curses
import re
from pathlib import Path
import gameapi_util_cfg as config

class v5CPP:
    window = curses.window

    def __init__(self, window_in):
        self.window = window_in
        self.options = []
        self.selection = 0
    # __init__

    def add_option(self, name, function):
        self.options.append({"name": name, "function": function})
    # m_add_opt

    def run(self):
        curses.curs_set(0)
        self.window.clear()
        self.window.refresh()

        while True:
            self.window.clear()
            self.window.addstr('GameAPI-CPP Utilities\n\n')

            for index, option in enumerate(self.options):
                if index == self.selection:
                    self.window.addstr(f"> {option['name']}\n", curses.A_REVERSE)
                else:
                    self.window.addstr(f"- {option['name']}\n")

            key = self.window.getch()

            if key == curses.KEY_UP:
                self.selection = (self.selection - 1) % len(self.options)
            elif key == curses.KEY_DOWN:
                self.selection = (self.selection + 1) % len(self.options)
            elif key == 10 or key == 13:
                selection = self.options[self.selection]
                self.window.clear()
                self.window.addstr(f"> {selection['name']}\n")
                self.window.refresh()
                selection['function']()
                self.window.getch()
                break

    os.system('cls||clear')
    print(config.ALL_HPP_PATH)
    # run

    def project_update(self):
        filenames = []

        self.window.addstr(f'Generating {config.ALL_CODE_NAME}, {config.ALL_HEADER_NAME}\n')
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

        self.window.addstr(f"Generating {config.CMAKE_PATH}\n")
        files = [f"${config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + f + "\n" for f in filenames if f.endswith(".cpp") and not f.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as f:
            f.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.window.addstr("Done.\n")
        self.exit_option()
    # project_update

    def gen_pub_fns(self):
        self.window.addstr("WARNING: C++ Public function generation is experimental. Manual fixing may be required\n")

        if os.path.exists(config.PUB_FNS_PATH):
            self.window.addstr(f"\n'{config.PUB_FNS_PATH}' already exists. Overwrite? (Y/N)\n")

            if chr(self.window.getch()).upper() != 'Y':
                self.exit_option()
                return

        events = ("Update", "LateUpdate", "StaticUpdate", "Draw", "Create", "StageLoad", "EditorDraw", "EditorLoad", "StaticLoad", "Serialize")
        exclusions = ["*", "RSDK_DECLARE"]

        with open(config.PUB_FNS_PATH, "w") as f:
            f.write('#pragma once\n')
            f.write('#include "RSDKv5/RSDKv5.hpp"')
            f.write('\n\nusing namespace RSDK;\n\n')
            f.write('#if RETRO_USE_MOD_LOADER\n')

            f.write('namespace RSDK\n{\n')        # namespace RSDK
            f.write('namespace Mod\n{\n')         # namespace Mod

            # template <typename NS, typename Type> inline static void AddPublicFunction(const char *functionName, Type(NS::*functionPtr))
            f.write('\ntemplate <typename NS, typename Type> inline static void AddPublicFunction(const char *functionName, Type(NS::*functionPtr))\n{\n')
            f.write('    modTable->AddPublicFunction(functionName, reinterpret_cast<void *&>(functionPtr));\n')
            f.write('}\n\n')

            f.write('} // namespace Mod\n')       # // namespace Mod
            f.write('} // namespace RSDK\n\n')    # // namespace RSDK

            f.write('#define ADD_PUBLIC_FUNC(func) RSDK::Mod::AddPublicFunction(#func, &func)\n\n');

            f.write(f'namespace {config.OBJECT_NAMESPACE}\n{{\n') # namespace GameLogic

            # static void InitPublicFunctions()
            f.write(f'\nstatic void InitPublicFunctions()\n{{\n')
            for path in Path(config.OBJECT_PATH).rglob("*.hpp"):
                done = False
                prepros = ""
                hasPrepos = False
                with open(path, "r") as file:
                    for line in file:
                        line = line.rstrip()

                        if (match := re.fullmatch(r"([a-zA-Z0-9\*\s]*) ([^(]*)\((.*)\);", line)) is not None:
                            ret_type, name, args = match.groups()
                            ret_type = ret_type.strip()
                            name = name.strip()

                            for exclusion in exclusions:
                                name = name.replace(exclusion, '')
                            name = name.strip()

                            if name.endswith(events):
                                continue

                            if prepros and (prepros != "#endif"):
                                f.write(f"{prepros}\n")
                                prepros = ""
                                hasPrepos = True

                            if not done:
                                f.write(f"    // {path.parent.name}/{path.stem}\n")
                                done = True

                            if name:
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
            # // static void InitPublicFunctions()

            f.write(f'}} // namespace {config.OBJECT_NAMESPACE}\n\n')    # // namespace GameLogic

            f.write('#endif')

        self.window.addstr("Done.\n")
        self.exit_option()
    # gen_pub_fns

    def create_object(self):
        self.window.addstr("Object Name: ")
        self.window.refresh()
        curses.echo()
        obj_name = self.window.getstr().decode('utf-8').strip()
        curses.noecho()

        if not obj_name:
            self.window.addstr("You're gonna need a name for the object.\n")
            self.window.getch()
            return

        directories = [d for d in os.listdir(config.OBJECT_PATH) if os.path.isdir(os.path.join(config.OBJECT_PATH, d))]

        if not directories:
            self.window.addstr("\nNo valid object directories found.\n")
            return

        self.window.addstr(f"Where do you want '{obj_name}'? Ctrl + C to cancel:\n")

        scroll             = 0
        dir_selected       = 0
        terminal_height, _ = self.window.getmaxyx()

        while True:
            self.window.clear()
            self.window.addstr(f"Where do you want '{obj_name}'? Ctrl + C to cancel:\n")

            if dir_selected < scroll:
                scroll = dir_selected
            elif dir_selected >= scroll + (terminal_height - 4):
                scroll = dir_selected - (terminal_height - 4) + 1

            for i in range(terminal_height - 4):
                dir_index = scroll + i
                if dir_index >= len(directories):
                    break
                dir_name = directories[dir_index]
                if dir_index == dir_selected:
                    self.window.addstr(f"> {dir_name}\n", curses.A_REVERSE)
                else:
                    self.window.addstr(f"- {dir_name}\n")

            if scroll + (terminal_height - 4) < len(directories):
                self.window.addstr("  ... scroll down\n")

            self.window.refresh()

            key = self.window.getch()

            if key == curses.KEY_UP and dir_selected > 0:
                dir_selected -= 1
            elif key == curses.KEY_DOWN and dir_selected < len(directories) - 1:
                dir_selected += 1
            elif key in (10, 13):
                selected_dir = directories[dir_selected]
                break

        obj_dir = os.path.join(config.OBJECT_PATH, selected_dir)
        cpp_path = os.path.join(obj_dir, f"{obj_name}.cpp")
        hpp_path = os.path.join(obj_dir, f"{obj_name}.hpp")

        if os.path.exists(cpp_path) or os.path.exists(hpp_path):
            self.window.addstr(f"Object '{obj_name}' already exists in '{selected_dir}'.\n")
            self.exit_option()
            return

        object_cpp = f"""#include "Game.hpp"

using namespace RSDK;

namespace {config.OBJECT_NAMESPACE}
{{

// -------------------
// Object Registration
// -------------------

RSDK_REGISTER_OBJECT({obj_name});

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

}} // namespace GameLogic
"""

        object_hpp = f"""#pragma once
#include "Game.hpp"

using namespace RSDK;

// ------------------
// Macros/Definitions
// ------------------

namespace {config.OBJECT_NAMESPACE}
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

    RSDK_DECLARE({obj_name})
}};
}} // namespace GameLogic
"""

        try:
            with open(cpp_path, "w") as cpp_out:
                cpp_out.write(object_cpp)

            with open(hpp_path, "w") as hpp_out:
                hpp_out.write(object_hpp)

            self.window.addstr(f"\nDone. Created '{obj_name}' in directory '{selected_dir}'.\n")
            self.window.addstr(f'Update {config.ALL_CODE_NAME}/{config.ALL_HEADER_NAME} & CMake? (Y/N)')

            self.window.refresh()

            if self.window.getch() in (ord('y'), ord('Y')):
                self.window.clear()
                self.project_update()
            else:
                self.window.clear()
                self.exit_option()

            self.window.getch()

        except Exception as e:
            self.window.addstr(f"This wasn't supposed to happen... {str(e)}\n")
            self.window.getch()
    # create_object

    def exit_option(self):
        self.window.addstr("\nPress 'S' to return to the main menu, or press anything else to exit.")
        if chr(self.window.getch()).upper() == 'S':
            self.run()
        else:
            self.exit_util()

    def exit_util(self):
        exit(0)
    # exit_util

def main(window_in):
    util = v5CPP(window_in)
    if config.skipDefaultTools == False:
        util.add_option(f'Update {config.ALL_CODE_NAME}/{config.ALL_HEADER_NAME} & CMake Project', util.project_update)
        util.add_option("Generate public functions (experimental)", util.gen_pub_fns)
        util.add_option("Create new object", util.create_object)
    config.init(window_in, util);
    util.add_option("Exit", util.exit_util)
    util.run()
# main

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
