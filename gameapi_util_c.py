import urwid
import gameapi_util_cfg as config
import os
from pathlib import Path
import re

class gameapi_util:
    def __init__(self):
        self.options = []
        self.selection = 0
        self.header_text = urwid.Text("gameapi_util (C - WIP!)\n", align='left')
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
            cpp_path = os.path.join(obj_dir, f"{self.obj_name}.c")
            hpp_path = os.path.join(obj_dir, f"{self.obj_name}.h")

            if os.path.exists(cpp_path) or os.path.exists(hpp_path):
                self.add_line(f"Object '{self.obj_name}' already exists in '{selected_dir}'. Press any key to return to the main menu.")
                self.main_layout.body = urwid.ListBox(self.main_body)
                self.selection = 0
                self.loopState = self.loop_wait_for_return
                return
            
            obj_name_up = self.obj_name.upper()

            try:
                with open(cpp_path, "w") as c_out:
                    c_out.write(f'#include "{config.GAMEAPI_INC_PATH}"\n\n')
                    c_out.write(f'Object{self.obj_name} *{self.obj_name};\n\n')

                    c_out.write(f'void {self.obj_name}_Update(void) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_LateUpdate(void) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_StaticUpdate(void) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_Draw(void) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_Create(void* data) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_StageLoad(void) {{}}\n\n')

                    c_out.write('#if GAME_INCLUDE_EDITOR\n')
                    c_out.write(f'void {self.obj_name}_EditorLoad(void) {{}}\n\n')
                    c_out.write(f'void {self.obj_name}_EditorDraw(void) {{}}\n')
                    c_out.write('#endif\n')

                    c_out.write('#if RETRO_REV0U\n')
                    c_out.write(f'void {self.obj_name}_StaticLoad(Object{self.obj_name} *sVars) {{ memset(sVars, 0, sizeof(Object{self.obj_name})); }}\n')
                    c_out.write('#endif\n\n')

                    c_out.write(f'void {self.obj_name}_Serialize(void);\n')
                    
                with open(hpp_path, "w") as h_out:
                    h_out.write(f'#ifndef OBJ_{obj_name_up}_H\n')
                    h_out.write(f'#define OBJ_{obj_name_up}_H\n\n')
                    h_out.write(f'#include "{config.GAMEAPI_INC_PATH}"\n\n')

                    h_out.write('// Object Class\n')
                    h_out.write(f'struct Object{self.obj_name} {{\n')
                    h_out.write(f'    RSDK_OBJECT\n')
                    h_out.write(f'}};\n\n')

                    h_out.write('// Entity Class\n')
                    h_out.write(f'struct Entity{self.obj_name} {{\n')
                    h_out.write(f'    RSDK_ENTITY\n')
                    h_out.write(f'}};\n\n')

                    h_out.write('// Object Struct\n')
                    h_out.write(f'extern Object{self.obj_name} *{self.obj_name};\n\n')

                    h_out.write('// Standard Entity Events\n')
                    h_out.write(f'void {self.obj_name}_Update(void);\n')
                    h_out.write(f'void {self.obj_name}_LateUpdate(void);\n')
                    h_out.write(f'void {self.obj_name}_StaticUpdate(void);\n')
                    h_out.write(f'void {self.obj_name}_Draw(void);\n')
                    h_out.write(f'void {self.obj_name}_Create(void* data);\n')
                    h_out.write('#if GAME_INCLUDE_EDITOR\n')
                    h_out.write(f'void {self.obj_name}_EditorLoad(void);\n')
                    h_out.write(f'void {self.obj_name}_EditorDraw(void);\n')
                    h_out.write('#endif\n')
                    h_out.write(f'void {self.obj_name}_Serialize(void);\n')
                    h_out.write('#if RETRO_REV0U\n')
                    h_out.write(f'void {self.obj_name}_StaticLoad(Object{self.obj_name} *sVars);\n')
                    h_out.write('#endif\n\n')

                    h_out.write('// Extra Entity Functions\n\n')

                    h_out.write(f'#endif //! OBJ_{obj_name_up}_H')

                self.directories.clear()
                self.main_layout.body = urwid.ListBox(self.main_body)

                self.add_line(f"Done! Created '{self.obj_name}' in directory '{selected_dir}'.")
                self.add_line("Would you like to update the CMake project? (Y/N)")
                self.loopState = self.loop_create_object_update_prompt

            except Exception as e:
                self.add_line(f"This wasn't supposed to happen... {str(e)}")
                self.loopState = self.loop_main_menu
                self.refresh_main_menu()
    # loop_select_directory -> (self, key)

    def loop_create_object_update_prompt(self, key):
        if key in ('y', 'Y'):
            self.project_update()
            self.loopState = self.loop_main_menu
        elif key in ('n', 'N'):
            self.add_line("Skipped project update. Press any key to return to the main menu.")
            self.loopState = self.loop_main_menu
    # loop_create_object_update_prompt -> (self, key)

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
                f.writelines(f'#include "{f}"\n' for f in filenames if f.endswith(".c") and not f.endswith(config.ALL_CODE_NAME))

            obj_forward_decl = [f'typedef struct {os.path.splitext(os.path.basename(f))[0]} {os.path.splitext(os.path.basename(f))[0]};\n' for f in filenames if f.endswith(".h") and not f.endswith(config.ALL_HEADER_NAME)]
            obj_includes = [f'#include "{config.OBJECT_PATH_NAME}/{f}"\n' for f in filenames if f.endswith(".h") and not f.endswith(config.ALL_HEADER_NAME)]

            with open(config.ALL_HPP_PATH, "w") as f:
                f.write('// Forward Declarations\n')
                f.writelines(obj_forward_decl)
                f.writelines(f'\n{obj_includes}')

        self.add_line(f"Generating {config.CMAKE_PATH}")
        files = [f"${config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + f + "\n" for f in filenames if f.endswith(".c") and not f.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as f:
            f.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.success_msg_generic()
    # project_update -> (self)

    def gen_pub_fns(self):
        self.add_line("Unimplemented.")
        return

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
        exclusions = ["TABLE", "STATIC"]

    # gen_pub_fns_imp -> (self)

    def gen_static_objs(self):
        self.add_line("Unimplemented.")
    # gen_static_objs -> (self)

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
        app.add_option('Generate Public Functions', app.gen_pub_fns)
        app.add_option('Generate Static Objects', app.gen_static_objs)
        app.add_option('Create Object', app.create_object)
    config.init(app);
    app.add_option("Exit", app.exit_util)
    app.run()
# main -> ()

if __name__ == '__main__':
    main()
