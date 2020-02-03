__author__ = "Berserker55" # you can find me on the ALTTP Randomizer Discord
__version__ = 1.6

"""
This script launches a Multiplayer "Multiworld" Mystery Game

.yaml files for all participating players should be placed in a /Players folder.
For every player a mystery game is rolled and a ROM created.
After generation the server is automatically launched.
It is still up to the host to forward the correct port (38281 by default) and distribute the roms to the players.
Regular Mystery has to work for this first, such as a ALTTP Base ROM and Enemizer Setup.
"""

####config####
#location of your Enemizer CLI, available here: https://github.com/Bonta0/Enemizer/releases
enemizer_location:str = r"EnemizerCLI/EnemizerCLI.Core.exe"

#Where to place the resulting files
outputpath:str = "MultiMystery"

#folder from which the player yaml files are pulled from
player_files_folder:str = "Players"

#automatically launches {player_name}.yaml's ROM file using the OS's default program once generation completes. (likely your emulator)
#does nothing if the name is not found
#example: player_name = "Berserker"
player_name:str = ""

#Zip the resulting roms
#0 -> Don't
#1 -> Create a zip
#2 -> Create a zip and delete the ROMs that will be in it, except the hosts (requires player_name to be set correctly)
zip_roms:int = 1

#create a spoiler file
create_spoiler:bool = True

#create roms as race coms
race:bool= False

# How many seeds should be rolled in parallel. This is useful for Door Rando, since some to many of them can fail.
# set to 0 for it to mimic the amount of hardware threads you have, otherwise use a positive number for the amount of attempts it should do at once
parallel_attempts = 0

#When using parallel_attempts, this controls if the first one that works in order of starting should be taken, or the first one in order of completion time should be taken
#keep in mind, that turning this on, will skew the randomness into "simpler" seeds, as they generate quicker
take_first_working = False

#Version of python to use for Bonta Multiworld. Probably leave this as is, if you don't know what this does.
#can be tagged for bitness, for example "3.8-32" would be latest installed 3.8 on 32 bits
#special case: None -> use the python which was used to launch this file.
py_version:str = None
####end of config####

import os
import subprocess
import sys
import tempfile
import shutil
import traceback
import io
import concurrent.futures

def feedback(text:str):
    print(text)
    input("Press Enter to ignore and probably crash.")


if __name__ == "__main__":
    try:
        if not py_version:
            py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        import ModuleUpdate
        ModuleUpdate.update()
        os.makedirs(outputpath, exist_ok=True)
        print(f"{__author__}'s MultiMystery Launcher V{__version__} (DoorRando Edition)")
        if not os.path.exists(enemizer_location):
            feedback(f"Enemizer not found at {enemizer_location}, please adjust the path in MultiMystery.py's config or put Enemizer in the default location.")
        if not os.path.exists("Zelda no Densetsu - Kamigami no Triforce (Japan).sfc"):
            feedback("Base rom is expected as Zelda no Densetsu - Kamigami no Triforce (Japan).sfc in the Multiworld root folder please place/rename it there.")
        player_files = []
        os.makedirs(player_files_folder, exist_ok=True)
        for file in os.listdir(player_files_folder):
            if file.lower().endswith(".yaml"):
                player_files.append(file)
                print(f"Player {file[:-5]} found.")
        player_count = len(player_files)
        if player_count == 0:
            feedback(f"No player files found. Please put them in a {player_files_folder} folder.")
        else:
            print(player_count, "Players found.")

        player_string = ""
        for i,file in enumerate(player_files):
            player_string += f"--p{i+1} {os.path.join(player_files_folder, file)} "

        player_names = list(file[:-5] for file in player_files)

        basecommand = f"py -{py_version} Mystery.py --multi {len(player_files)} {player_string}" \
                  f" --names {','.join(player_names)} --enemizercli {enemizer_location} " \
                  " --create_spoiler" if create_spoiler else "" + " --race" if race else ""
        print(basecommand)

        import time
        from tqdm import tqdm

        start = time.perf_counter()
        def get_working_seed():#is a function for automatic deallocation of resources that are no longer needed when the server starts
            global parallel_attempts

            def cancel_remaining(starting_at:int = 0):
                for x in range(starting_at + 1, parallel_attempts + 1):
                    task_mapping[x].cancel()

            if parallel_attempts < 1:
                import multiprocessing
                parallel_attempts = multiprocessing.cpu_count()

            pool = concurrent.futures.ThreadPoolExecutor()
            task_mapping = {}
            for x in range(1, parallel_attempts+1):
                folder = tempfile.TemporaryDirectory()
                command = basecommand + f" --outputpath {folder.name}"
                task = pool.submit(subprocess.run, command, capture_output=True, shell=False, text=True)
                task.task_id = x
                task.folder = folder
                task_mapping[x] = task

            errors = []

            dead_or_alive = {}

            def check_if_done():
                for x in range(1, parallel_attempts+1):
                    result = dead_or_alive.get(x, None)
                    if result:
                        return x
                    elif result is None:
                        return False
                return False

            def get_alive_threads():
                still_alive = []
                for x in range(1,min(min_logical_seed,parallel_attempts)+1):
                    success = dead_or_alive.get(x, None)
                    if success is None:
                        still_alive.append(str(x))
                        if len(still_alive) == 8:
                            still_alive.append("...")
                            break
                return ", ".join(still_alive) if len(still_alive) > 0 else "None"

            min_logical_seed = parallel_attempts
            pbar = tqdm(concurrent.futures.as_completed(task_mapping.values()),
                                  total=len(task_mapping), unit="seeds")
            pbar.set_description(f"Generating: {get_alive_threads()}")
            for task in pbar:
                try:
                    result = task.result()
                    if result.returncode:
                        raise Exception(result.stderr)
                except concurrent.futures.CancelledError:
                    task.folder.cleanup()
                    dead_or_alive[task.task_id] = False
                except:
                    error = io.StringIO()
                    traceback.print_exc(file=error)
                    errors.append(error.getvalue())
                    task.folder.cleanup()
                    dead_or_alive[task.task_id] = False
                    #print(f"Seed Attempt #{task.task_id:4} died. ({len(dead_or_alive):4} total of {parallel_attempts})")
                    if "Please fix your yaml." in error.getvalue():
                        cancel_remaining()
                        tqdm.write("YAML error")
                        break
                    done = check_if_done()
                    if done:
                        break
                else:
                    msg = f"Seed Attempt #{task.task_id:4} was successful."

                    dead_or_alive[task.task_id] = True
                    done = check_if_done()
                    if done:
                        tqdm.write(msg)
                        cancel_remaining()
                        break
                    elif take_first_working:
                        tqdm.write(msg)
                        cancel_remaining()
                        def check_if_done():
                            return task.task_id
                        break
                    else:
                        min_logical_seed = min(min_logical_seed, task.task_id)
                        if task.task_id <= min_logical_seed:
                            tqdm.write(msg+" However, waiting for an earlier logical seed that is still generating.")
                        cancel_remaining(task.task_id)
                pbar.set_description(f"Generating: {get_alive_threads()}")
            pool.shutdown(False)

            task_id = check_if_done()
            if not task_id:
                input("No seed was successful. Press enter to get errors.")
                for error in errors:
                    print(error)
                sys.exit()

            return task_mapping[task_id]

        task = get_working_seed()
        seedname = ""
        for file in os.listdir(task.folder.name):
            shutil.copy(os.path.join(task.folder.name, file), os.path.join(outputpath, file))
            if file.endswith("_multidata"):
                seedname = file[4:-10]
        print()
        print(f"Took {time.perf_counter()-start:.3f} seconds to generate seed.")

        if player_count == 1:
            print(f"No need to start server as this is a single player seed")
        else:
            multidataname = f"DR_M{seedname}_multidata"

            romfilename = ""
            if player_name:
                try:
                    index = player_names.index(player_name)
                except IndexError:
                    print(f"Could not find Player {player_name}")
                else:
                    romfilename = os.path.join(outputpath, f"DR_{seedname}_P{index + 1}_{player_name}.sfc")
                    import webbrowser
                    if os.path.exists(romfilename):
                        print(f"Launching ROM file {romfilename}")
                        webbrowser.open(romfilename)

            if zip_roms:
                zipname = os.path.join(outputpath, f"DR_M{seedname}.zip")
                print(f"Creating zipfile {zipname}")
                import zipfile
                with zipfile.ZipFile(zipname, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                    for file in os.listdir(outputpath):
                        if file.endswith(".sfc") and seedname in file:
                            zf.write(os.path.join(outputpath, file), file)
                            print(f"Packed {file} into zipfile {zipname}")
                            if zip_roms == 2 and player_name.lower() not in file.lower():
                                os.remove(file)
                                print(f"Removed file {file} that is now present in the zipfile")

            subprocess.call(f"py -{py_version} MultiServer.py --multidata {os.path.join(outputpath, multidataname)}")
    except:
        traceback.print_exc()
        input("Press enter to close")
