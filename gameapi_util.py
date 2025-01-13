import os, sys, re, urwid, webbrowser

import gameapi_util_cfg as config

import util_object as objectutil
import util_project as projectutil

from pathlib import Path

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
            ('item_disabled', 'light gray', ''),
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


    def add_line(self, txt):
        self.body.append(urwid.Text(txt))

    def add_option(self, label, onSelectCB):
        self.options.append({'label': label, 'onSelectCB': onSelectCB})

    def add_label(self, label='', attr=None):
        self.options.append({'label': label, 'onSelectCB': None, 'item_skip_select': True})


    def refresh_main_menu(self):
        self.body.clear()
        for i, option in enumerate(self.options):
            if option.get('item_skip_select'):
                divider = urwid.Text(option['label'])
                attr = option.get('attr', 'not_selected')
                self.body.append(urwid.AttrMap(divider, attr))
            else:
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

    def success_msg_generic(self):
        self.set_terminal_progress(0, 0)
        self.add_line('Done! Press any key to return to the main menu.')
        self.selection = 1
        self.state = self.loop_wait_for_return

    ## ---------------
    ## Menu States
    ## ---------------

    def loop_main_menu(self, key):
        self.set_terminal_progress(0, 0)

        if key in ('up', 'k'):
            self.selection = (self.selection - 1) % len(self.options)
            while self.options[self.selection].get('item_skip_select'):
                self.selection = (self.selection - 1) % len(self.options)
            self.refresh_main_menu()
        elif key in ('down', 'j'):
            self.selection = (self.selection + 1) % len(self.options)
            while self.options[self.selection].get('item_skip_select'):
                self.selection = (self.selection + 1) % len(self.options)
            self.refresh_main_menu()
        elif key == 'enter':
            if not self.options[self.selection].get('item_skip_select'):
                self.body.clear()
                _label = self.options[self.selection]['label']
                self.add_line(f"> Selected {_label}\n")
                self.options[self.selection]['onSelectCB']()
        else:
            self.refresh_main_menu()

    def loop_create_object(self, key):
        if key == 'esc':
            self.selection = 1
            self.state = self.loop_main_menu
            self.refresh_main_menu()
        elif key == 'enter':
            if not os.path.exists(config.OBJECT_PATH):
                self.set_terminal_progress(2, 100)
                self.add_line(f"{config.OBJECT_PATH} does not exist. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            if not os.path.isdir(config.OBJECT_PATH):
                self.set_terminal_progress(2, 100)
                self.add_line(f"{config.OBJECT_PATH} is not a directory. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            obj_name = self.obj_name_field.get_edit_text()
            if not obj_name:
                self.set_terminal_progress(4, 100)
                self.add_line("No name was provided. Press any key to return to the main menu.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            self.obj_name = obj_name

            self.directories = [d for d in os.listdir(config.OBJECT_PATH) if os.path.isdir(os.path.join(config.OBJECT_PATH, d))]
            if not self.directories:
                self.set_terminal_progress(2, 100)
                self.add_line("No valid object directories found.")
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            directory_select_walker = urwid.SimpleListWalker([urwid.Text(f"- {dir_name}") for dir_name in self.directories])
            self.layout.body = urwid.ListBox(directory_select_walker)
            self.selection = 1
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
                self.layout.body = urwid.ListBox(self.body)
                self.selection = 1
                self.state = self.loop_wait_for_return
                return

            try:
                if self.tempVal2 == 0: # C++
                    objectutil.new_cpp_object(self.obj_name, codePath, self.tempVal)
                    objectutil.new_cpp_object_header(self.obj_name, headerPath, self.tempVal)
                elif self.tempVal2 == 1: # C
                    objectutil.new_c_object(self.obj_name, codePath, self.tempVal)
                    objectutil.new_c_object_header(self.obj_name, headerPath, self.tempVal)

                self.directories.clear()
                self.tempVal = 0
                self.tempVal2 = 0
                self.layout.body = urwid.ListBox(self.body)

                self.add_line(f"Done! Created '{self.obj_name}' in directory '{selected_dir}'.")
                self.add_line("Would you like to update the CMake project? (Y/N)")
                self.state = self.loop_create_object_update_prompt

            except Exception as e:
                self.set_terminal_progress(2, 100)
                self.add_line(f"This wasn't supposed to happen... {str(e)}")
                self.state = self.loop_main_menu

    def loop_create_object_update_prompt(self, key):
        if key in ('y', 'Y'):
            self.project_update()
            self.state = self.loop_main_menu
        else:
            self.state = self.loop_main_menu
            self.refresh_main_menu()

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
                f.writelines(f'#include "{f}"\n' for f in filenames if f.endswith(".cpp") and not f.endswith(config.ALL_CODE_NAME))

            obj_forward_decl = [f'struct {os.path.splitext(os.path.basename(f))[0]};\n' for f in filenames if f.endswith(".hpp") and not f.endswith(config.ALL_HEADER_NAME)]
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
                    self.refresh_main_menu()

            self.state = loop_confirm
            return

        self.gen_pub_dns_imp(mode)

    def gen_pub_dns_imp(self, mode):
        self.set_terminal_progress(3, 0)

        if mode == 0: # C++
            projectutil.cpp_public_functions()
        elif mode == 1:
            projectutil.c_public_functions()
        self.success_msg_generic()

    def create_object(self, language, mode=objectutil.modes.default):
        self.state = self.loop_create_object
        self.obj_name_field = urwid.Edit("Object Name: ")
        self.tempVal = mode
        self.tempVal2 = language

        input_body = urwid.SimpleListWalker([urwid.AttrMap(self.obj_name_field, None)])
        self.layout.body = urwid.ListBox(input_body)

    def web_github_repo(self):
        webbrowser.open("https://github.com/Jdsle/gameapi_util")
        self.state = self.loop_main_menu
        self.refresh_main_menu()

    def exit_util(self):
        self.set_terminal_progress(0, 0)
        raise urwid.ExitMainLoop()


def main():
    app = gameapi_util()

    if config.skipDefaultTools == False:
        app.add_label("[C++ Tools]")
        app.add_option('Project Update', app.project_update)
        app.add_option('Generate Public Functions', lambda: app.gen_pub_fns(0))
        app.add_option('New Object [default]', lambda: app.create_object(0, objectutil.modes.default))
        app.add_option('New Object [clean]', lambda: app.create_object(0, objectutil.modes.clean))
        app.add_option('New Object [mod]', lambda: app.create_object(0, objectutil.modes.modded))
        app.add_option('New Object [mod & clean]', lambda: app.create_object(0, objectutil.modes.modded_clean))
        app.add_label()
        app.add_label("[C Tools]")
        app.add_option('Project Update', app.project_update)
        app.add_option('Generate Public Functions', lambda: app.gen_pub_fns(1))
        app.add_option('New Object [default]', lambda: app.create_object(1, objectutil.modes.default))
        app.add_option('New Object [clean]', lambda: app.create_object(1, objectutil.modes.clean))
        app.add_option('New Object [mod]', lambda: app.create_object(1, objectutil.modes.modded))
        app.add_option('New Object [mod & clean]', lambda: app.create_object(1, objectutil.modes.modded_clean))
        app.add_label()

    config.init(app)
    objectutil.init(app)
    projectutil.init(app)

    app.add_option("Github Repo", app.web_github_repo)
    app.add_option("Exit", app.exit_util)

    app.run()

if __name__ == '__main__':
    main()
