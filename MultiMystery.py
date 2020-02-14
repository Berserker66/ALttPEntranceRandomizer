__author__ = "Berserker55" # you can find me on the ALTTP Randomizer Discord
__version__ = 1.6

"""
This script launches a Multiplayer "Multiworld" Mystery Game

.yaml files for all participating players should be placed in a /Players folder.
For every player a mystery game is rolled and a ROM created.
After generation the server is automatically launched.
It is still up to the host to forward the correct port (38281 by default) and distribute the roms to the players.
Regular Mystery has to work for this first, such as a ALTTP Base ROM and Enemizer Setup.
A guide can be found here: https://docs.google.com/document/d/19FoqUkuyStMqhOq8uGiocskMo1KMjOW4nEeG81xrKoI/edit
Configuration can be found in host.yaml
"""

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
        print(f"{__author__}'s MultiMystery Launcher V{__version__}")
        import ModuleUpdate
        ModuleUpdate.update()

        from Utils import parse_yaml

        multi_mystery_options = parse_yaml(open("host.yaml").read())["multi_mystery_options"]
        output_path = multi_mystery_options["output_path"]
        enemizer_path = multi_mystery_options["enemizer_path"]
        player_files_path = multi_mystery_options["player_files_path"]
        race = multi_mystery_options["race"]
        create_spoiler = multi_mystery_options["create_spoiler"]
        zip_roms = multi_mystery_options["zip_roms"]
        player_name = multi_mystery_options["player_name"]
        take_first_working = multi_mystery_options["take_first_working"]

        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        if not os.path.exists(enemizer_path):
            feedback(
                f"Enemizer not found at {enemizer_path}, please adjust the path in MultiMystery.py's config or put Enemizer in the default location.")
        if not os.path.exists("Zelda no Densetsu - Kamigami no Triforce (Japan).sfc"):
            feedback(
                "Base rom is expected as Zelda no Densetsu - Kamigami no Triforce (Japan).sfc in the Multiworld root folder please place/rename it there.")
        player_files = []
        os.makedirs(player_files_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        for file in os.listdir(player_files_path):
            if file.lower().endswith(".yaml"):
                player_files.append(file)
                print(f"Player {file[:-5]} found.")
        player_count = len(player_files)
        if player_count == 0:
            feedback(f"No player files found. Please put them in a {player_files_path} folder.")
        else:
            print(player_count, "Players found.")

        player_string = ""
        for i,file in enumerate(player_files):
            player_string += f"--p{i+1} {os.path.join(player_files_path, file)} "

        player_names = list(file[:-5] for file in player_files)

        if os.path.exists("BerserkerMultiServer.exe"):
            basemysterycommand = "BerserkerMystery.exe" #compiled windows
        elif os.path.exists("BerserkerMultiServer"):
            basemysterycommand = "BerserkerMystery" # compiled linux
        else:
            basemysterycommand = f"py -{py_version} Mystery.py" #source

        spoiler_option = " --create_spoiler" if  create_spoiler else ""
        race_option = " --race" if race else ""
        basecommand = f"{basemysterycommand} --multi {len(player_files)} {player_string} " \
                  f"--names {','.join(player_names)} --enemizercli {enemizer_path}" \
                  f"{spoiler_option}{race_option}"
        print(basecommand)

        import time
        from tqdm import tqdm

        start = time.perf_counter()

        def get_working_seed():#is a function for automatic deallocation of resources that are no longer needed when the server starts            
            cpu_threads = multi_mystery_options["cpu_threads"]
            max_attempts = multi_mystery_options["max_attempts"]

            def cancel_remaining(starting_at:int = 0):
                for x in range(starting_at + 1, max_attempts + 1):
                    task_mapping[x].cancel()

            import multiprocessing
            if cpu_threads < 1:
                cpu_threads = multiprocessing.cpu_count()

            if max_attempts < 1:
                max_attempts = multiprocessing.cpu_count()

            pool = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads)
            task_mapping = {}
            for x in range(1, max_attempts+1):
                folder = tempfile.TemporaryDirectory()
                command = basecommand + f" --outputpath {folder.name}"
                task = pool.submit(subprocess.run, command, capture_output=True, shell=False, text=True)
                task.task_id = x
                task.folder = folder
                task_mapping[x] = task

            errors = []

            dead_or_alive = {}

            def check_if_done():
                for x in range(1, max_attempts+1):
                    result = dead_or_alive.get(x, None)
                    if result:
                        return x
                    elif result is None:
                        return False
                return False

            def get_alive_threads():
                still_alive = []
                for x in range(1,min(min_logical_seed,max_attempts)+1):
                    success = dead_or_alive.get(x, None)
                    if success is None:
                        still_alive.append(str(x))
                        if len(still_alive) == min(cpu_threads, 8):
                            still_alive.append("...")
                            break
                return ", ".join(still_alive) if still_alive else "None"

            min_logical_seed = max_attempts
            with tqdm(concurrent.futures.as_completed(task_mapping.values()),
                      total=len(task_mapping), unit="seed(s)",
                      desc=f"Generating: {get_alive_threads()}") as progressbar:
                for task in progressbar:
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
                    progressbar.set_description(f"Generating: {get_alive_threads()}")

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
            shutil.copy(os.path.join(task.folder.name, file), os.path.join(output_path, file))
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
                    romfilename = os.path.join(output_path, f"DR_{seedname}_P{index + 1}_{player_name}.sfc")
                    import webbrowser
                    if os.path.exists(romfilename):
                        print(f"Launching ROM file {romfilename}")
                        webbrowser.open(romfilename)

            if zip_roms:
                zipname = os.path.join(output_path, f"DR_M{seedname}.zip")
                print(f"Creating zipfile {zipname}")
                import zipfile
                with zipfile.ZipFile(zipname, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                    for file in os.listdir(output_path):
                        if file.endswith(".sfc") and seedname in file:
                            zf.write(os.path.join(output_path, file), file)
                            print(f"Packed {file} into zipfile {zipname}")
                            if zip_roms == 2 and player_name.lower() not in file.lower():
                                os.remove(file)
                                print(f"Removed file {file} that is now present in the zipfile")

            if os.path.exists("BerserkerMultiServer.exe"):
                baseservercommand = "BerserkerMultiServer.exe"  # compiled windows
            elif os.path.exists("BerserkerMultiServer"):
                baseservercommand = "BerserkerMultiServer"  # compiled linux
            else:
                baseservercommand = f"py -{py_version} MultiServer.py"  # source
            #don't have a mac to test that. If you try to run compiled on mac, good luck.

            subprocess.call(f"{baseservercommand} --multidata {os.path.join(output_path, multidataname)}")
    except:
        traceback.print_exc()
        input("Press enter to close")
