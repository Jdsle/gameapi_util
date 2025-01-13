
import os, sys, re, urwid, webbrowser
from pathlib import Path
import gameapi_util_cfg as config

# Function/Variable definitions
app = None

# General
def init(app_in):
    global app
    app = app_in

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