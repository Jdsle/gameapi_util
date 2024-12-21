import os, re, urwid
import gameapi_util_cfg as config

from pathlib import Path

class gameapi_util:

    ## ---------------
    ## Menu Functions
    ## ---------------

    def __init__(self):
        self.options = []
        self.selection = 0
        self.body = urwid.SimpleListWalker([])
        header_txt = urwid.Text("gameapi_util (C)\n", align='left')
        footer_txt = urwid.Text("1.1.0 - Navigate with Up/Down, Enter to select. ⏎", align='left')
        self.layout = urwid.Frame(
            header=urwid.AttrMap(header_txt, None),
            body=urwid.ListBox(self.body),
            footer=urwid.AttrMap(footer_txt, 'footer'),
        )
        self.obj_name_field = None
        self.directories = []
        self.state = self.loop_main_menu


    def run(self):
        self.refresh_main_menu()
        palette = [
            ('selected', 'standout', ''),
            ('not_selected', '', ''),
            ('footer', 'dark gray', '')
        ]
        loop = urwid.MainLoop(self.layout, palette=palette, unhandled_input=lambda key: self.state(key))

        try:
            loop.run()
        except KeyboardInterrupt:
            pass


    def add_line(self, txt):
        self.body.append(urwid.Text(txt))


    def add_option(self, label, onSelectCB):
        self.options.append({'label': label, 'onSelectCB': onSelectCB})


    def success_msg_generic(self):
        self.add_line('Done! Press any key to return to the main menu.')
        self.selection = 0
        self.state = self.loop_wait_for_return


    def refresh_main_menu(self):
        self.body.clear()
        for i, option in enumerate(self.options):
            self.body.append(self.update_option(option, selected=(i == self.selection)))


    def refresh_obj_dir_menu(self):
        directory_select_walker = urwid.SimpleListWalker(
            [urwid.AttrMap(urwid.Text(f"> {dir_name}" if i == self.selection else f"- {dir_name}"),
                        'selected' if i == self.selection else 'not_selected')
            for i, dir_name in enumerate(self.directories)]
        )
        self.layout.body = urwid.ListBox(directory_select_walker)


    def update_option(self, option, selected=False):
        text = f"> {option['label']}" if selected else f"- {option['label']}"
        attr = 'selected' if selected else 'not_selected'
        return urwid.AttrMap(urwid.Text(text), attr)

    ## ---------------
    ## Menu States
    ## ---------------

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
            self.add_line(f"> Selected {_label}\n")
            self.options[self.selection]['onSelectCB']()
        else:
            self.refresh_main_menu()


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
            codePath = os.path.join(object_dir, f"{self.obj_name}.c")
            headerPath = os.path.join(object_dir, f"{self.obj_name}.h")

            if os.path.exists(codePath) or os.path.exists(headerPath):
                self.add_line(f"Object '{self.obj_name}' already exists in '{selected_dir}'. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 0
                self.state = self.loop_wait_for_return
                return

            obj_name_up = self.obj_name.upper()

            try:
                with open(codePath, "w") as c_out:
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
                    c_out.write('#endif\n\n')

                    c_out.write('#if RETRO_REV0U\n')
                    c_out.write(f'void {self.obj_name}_StaticLoad(Object{self.obj_name} *sVars) {{ memset(sVars, 0, sizeof(Object{self.obj_name})); }}\n')
                    c_out.write('#endif\n\n')

                    c_out.write(f'void {self.obj_name}_Serialize(void) {{}}\n')

                with open(headerPath, "w") as h_out:
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
                    h_out.write(f'void {self.obj_name}_StageLoad(void);\n')
                    h_out.write('#if GAME_INCLUDE_EDITOR\n')
                    h_out.write(f'void {self.obj_name}_EditorLoad(void);\n')
                    h_out.write(f'void {self.obj_name}_EditorDraw(void);\n')
                    h_out.write('#endif\n')
                    h_out.write('#if RETRO_REV0U\n')
                    h_out.write(f'void {self.obj_name}_StaticLoad(Object{self.obj_name} *sVars);\n')
                    h_out.write('#endif\n')
                    h_out.write(f'void {self.obj_name}_Serialize(void);\n')

                    h_out.write('// Extra Entity Functions\n\n')

                    h_out.write(f'#endif //! OBJ_{obj_name_up}_H')

                self.directories.clear()
                self.layout.body = urwid.ListBox(self.body)

                self.add_line(f"Done! Created '{self.obj_name}' in directory '{selected_dir}'.")
                self.add_line("Would you like to update the CMake project? (Y/N)")
                self.state = self.loop_create_object_update_prompt

            except Exception as e:
                self.add_line(f"This wasn't supposed to happen... {str(e)}")
                self.state = self.loop_main_menu
                self.refresh_main_menu()


    def loop_create_object_update_prompt(self, key):
        if key in ('y', 'Y'):
            self.project_update()
            self.state = self.loop_main_menu
        elif key in ('n', 'N'):
            self.add_line("Skipped project update. Press any key to return to the main menu.")
            self.state = self.loop_main_menu


    def loop_wait_for_return(self, key):
        self.state = self.loop_main_menu
        self.refresh_main_menu()

    ## ---------------
    ## Helpers
    ## ---------------

    def project_update(self):
        filenames = []
        self.add_line(f'Generating {config.ALL_CODE_NAME}, {config.ALL_HEADER_NAME}')
        for dir_, _, files in os.walk(config.OBJECT_PATH):
            for file_name in files:
                rel_dir = os.path.relpath(dir_, config.OBJECT_PATH)
                filenames.append(f"{rel_dir}/{file_name}")

            with open(f'{config.OBJECT_PATH}/{config.ALL_CODE_NAME}', "w") as f:
                f.writelines(f'#include "{f}"\n' for f in filenames if f.endswith(".c") and not f.endswith(config.ALL_CODE_NAME))

            obj_forward_decl = [f'typedef struct {os.path.splitext(os.path.basename(f))[0]} {os.path.splitext(os.path.basename(f))[0]};\n' for f in filenames if f.endswith(".h") and not f.endswith(config.ALL_HEADER_NAME)]
            obj_includes = [f'#include "{config.OBJECT_PATH_NAME}/{f}"\n' for f in filenames if f.endswith(".h") and not f.endswith(config.ALL_HEADER_NAME)]

            with open(f'{config.GAME_PATH}/{config.ALL_HEADER_NAME}', "w") as f:
                f.write('// Forward Declarations\n')
                f.writelines(obj_forward_decl)
                f.writelines('\n')
                f.writelines(obj_includes)

        self.add_line(f"Generating {config.CMAKE_PATH}")
        files = [f"\t{config.GAME_NAME}/{config.OBJECT_PATH_NAME}/" + cm + "\n" for cm in filenames if cm.endswith(".c") and not cm.endswith(config.ALL_CODE_NAME)]
        with open(config.CMAKE_PATH, "w") as cm:
            cm.writelines(["set(GENERATED_SOURCES\n"] + files + [")"])

        self.success_msg_generic()


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


    def gen_pub_dns_imp(self):
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

        self.success_msg_generic()


    def gen_obj_registration(self):
        self.add_line("Unimplemented.")


    def gen_static_objs(self):
        self.add_line("Unimplemented.")


    def create_object(self):
        self.state = self.loop_create_object
        self.obj_name_field = urwid.Edit("Object Name: ")

        input_body = urwid.SimpleListWalker([urwid.AttrMap(self.obj_name_field, None)])
        self.layout.body = urwid.ListBox(input_body)


    def exit_util(self):
        raise urwid.ExitMainLoop()


def main():
    app = gameapi_util()
    if config.skipDefaultTools == False:
        app.add_option('Project Update', app.project_update)
        app.add_option('Generate Public Functions', app.gen_pub_fns)
        #app.add_option('Generate Static Objects', app.gen_static_objs)
        #app.add_option('Generate Object Registration', app.gen_obj_registration)
        app.add_option('Create Object', app.create_object)
    config.init(app)
    app.add_option("Exit", app.exit_util)
    app.run()

if __name__ == '__main__':
    main()
