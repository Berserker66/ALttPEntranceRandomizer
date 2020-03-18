__author__ = "Berserker55" # you can find me on the ALTTP Randomizer Discord
__version__ = 1.7

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
import time
import multiprocessing
import concurrent.futures
import random


def feedback(text: str):
    print(text)
    input("Press Enter to ignore and probably crash.")


if __name__ == "__main__":
    try:
        print(f"{__author__}'s MultiMystery Launcher V{__version__}")
        import ModuleUpdate

        ModuleUpdate.update()

        from Utils import parse_yaml, get_public_ipv4
        from Patch import create_patch_file

        options = parse_yaml(open("host.yaml").read())

        multi_mystery_options = options["multi_mystery_options"]
        output_path = multi_mystery_options["output_path"]
        enemizer_path = multi_mystery_options["enemizer_path"]
        player_files_path = multi_mystery_options["player_files_path"]
        race = multi_mystery_options["race"]
        create_spoiler = multi_mystery_options["create_spoiler"]
        zip_roms = multi_mystery_options["zip_roms"]
        zip_diffs = multi_mystery_options["zip_diffs"]
        zip_spoiler = multi_mystery_options["zip_spoiler"]
        zip_multidata = multi_mystery_options["zip_multidata"]
        zip_format = multi_mystery_options["zip_format"]
        #zip_password = multi_mystery_options["zip_password"] not at this time
        player_name = multi_mystery_options["player_name"]
        take_first_working = multi_mystery_options["take_first_working"]
        meta_file_path = multi_mystery_options["meta_file_path"]
        teams = multi_mystery_options["teams"]
        rom_file = options["general_options"]["rom_file"]
        log_output_path = multi_mystery_options["log_output_path"]

        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        if not os.path.exists(enemizer_path):
            feedback(
                f"Enemizer not found at {enemizer_path}, please adjust the path in MultiMystery.py's config or put Enemizer in the default location.")
        if not os.path.exists(rom_file):
            feedback(
                f"Base rom is expected as {rom_file} in the Multiworld root folder please place/rename it there.")
        player_files = []
        os.makedirs(player_files_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        for file in os.listdir(player_files_path):
            lfile = file.lower()
            if lfile.endswith(".yaml") and lfile != meta_file_path.lower():
                player_files.append(file)
                print(f"Found player's file {file}.")
        player_count = len(player_files)
        if player_count == 0:
            feedback(f"No player files found. Please put them in a {player_files_path} folder.")
        else:
            print(player_count, "Players found.")

        player_string = ""
        for i, file in enumerate(player_files, 1):
            player_string += f"--p{i} {os.path.join(player_files_path, file)} "


        if os.path.exists("BerserkerMultiServer.exe"):
            basemysterycommand = "BerserkerMystery.exe" #compiled windows
        elif os.path.exists("BerserkerMultiServer"):
            basemysterycommand = "BerserkerMystery" # compiled linux
        else:
            basemysterycommand = f"py -{py_version} Mystery.py" #source

        command = f"{basemysterycommand} --multi {len(player_files)} {player_string} " \
                  f"--rom \"{rom_file}\" --enemizercli \"{enemizer_path}\" " \
                  f"--teams {teams} "

        if create_spoiler:
            command += " --create_spoiler"
        if race:
            command += " --race"
        if log_output_path:
            command += f" --log_output_path \"{log_output_path}\""
        if os.path.exists(os.path.join(player_files_path, meta_file_path)):
            command += f" --meta {os.path.join(player_files_path, meta_file_path)}"

        print(command)
        import time
        start = time.perf_counter()
        
        def copy_seed(task, destination: str):
            # seedname = None
            os.makedirs(destination, exist_ok=True)
            for file in os.listdir(task.folder.name):
                shutil.copy(os.path.join(task.folder.name, file), os.path.join(destination, file))
                # if not seedname and (file.endswith("_multidata") or file.endswith(".sfc") or file.endswith("_spoiler.txt")):
                #     seedname = file.split('.')[0].split('_')[1]
            return task.seedname

        def get_working_seed():#is a function for automatic deallocation of resources that are no longer needed when the server starts
            cpu_threads = multi_mystery_options["cpu_threads"]
            max_attempts = multi_mystery_options["max_attempts"]
            keep_all_seeds = multi_mystery_options["keep_all_seeds"]
            basedir = os.path.basename(tempfile.TemporaryDirectory().name) if keep_all_seeds else ""

            def cancel_remaining(starting_at:int = 0):
                for x in range(starting_at + 1, max_attempts + 1):
                    task_mapping[x].cancel()

            if cpu_threads < 1:
                cpu_threads = multiprocessing.cpu_count()

            if max_attempts < 1:
                max_attempts = multiprocessing.cpu_count()

            pool = concurrent.futures.ThreadPoolExecutor(max_workers=cpu_threads)
            task_mapping = {}

            def gen_seed(command: str):
                starttime = time.perf_counter()
                folder = tempfile.TemporaryDirectory()
                random.seed(None)
                seed = random.randint(0, 999999999)
                random.seed(seed)
                seedname = "M"+(f"{random.randint(0, 999999999)}".zfill(9))
                taskcommand = command + f" --outputpath {folder.name} --seed {seed}"
                result = subprocess.run(taskcommand, capture_output=True, shell=False, text=True)
                return result, folder, seed, seedname, time.perf_counter() - starttime

            def move_output_log(task, destination: str):
                if log_output_path:
                    try:
                        os.makedirs(os.path.join(log_output_path, destination), exist_ok=True)
                        shutil.move(os.path.join(log_output_path, f"{task.seed}.log"),
                                    os.path.join(log_output_path, destination, f"{task.seed}.log"))
                    except:
                        pass

            for x in range(1, max_attempts+1):
                task = pool.submit(gen_seed, command)
                task.task_id = x
                task.folder = None
                task.seed = None
                task.seedname = None
                task.time = float(0)
                task_mapping[x] = task

            errors = []
            dead_or_alive = {}
            alive = 0

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
            min_time = float("infinity")
            max_time = float(0)
            total_time = float(0)
            from tqdm import tqdm
            with tqdm(concurrent.futures.as_completed(task_mapping.values()),
                      total=len(task_mapping), unit="seed(s)", 
                      desc=(f"0.0% Success rate, " if keep_all_seeds else "") + f"Generating: {get_alive_threads()}") as progressbar:
                for task in progressbar:
                    try:
                        result, task.folder, task.seed, task.seedname, task.time = task.result()
                        if result.returncode:
                            raise Exception(result.stderr)
                    except concurrent.futures.CancelledError:
                        dead_or_alive[task.task_id] = False
                    except:
                        error = io.StringIO()
                        traceback.print_exc(file=error)
                        errors.append(error.getvalue())
                        task.folder.cleanup()
                        dead_or_alive[task.task_id] = False
                        move_output_log(task, "Failure")

                        if "Please fix your yaml." in error.getvalue():
                            cancel_remaining()
                            tqdm.write("YAML error")
                            tqdm.write(error.getvalue())
                            break

                        done = check_if_done()
                        if done and not keep_all_seeds:
                            break
                    else:
                        msg = f"Seed Attempt #{task.task_id:4} ({task.seedname}) was successful."
                        move_output_log(task, "Success")

                        if task.time < min_time:
                            min_time = task.time
                        if task.time > max_time:
                            max_time = task.time
                        total_time += task.time
                        dead_or_alive[task.task_id] = True
                        alive += 1
                        done = check_if_done()
                        if keep_all_seeds:
                            tqdm.write(msg)
                            copy_seed(task, os.path.join(output_path, basedir, str(task.task_id)))
                        elif done:
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
                    progressbar.set_description((f"{(alive/len(dead_or_alive))*100:.1f}% Success rate, " if keep_all_seeds else "") + f"Generating: {get_alive_threads()}")

            pool.shutdown(False)

            task_id = check_if_done()
            if not task_id:
                if not log_output_path:
                    input("No seed was successful. Press enter to get errors.")
                    for error in errors:
                        print(error)
                else:
                    print(f"Check {os.path.join(log_output_path,'Failure')} for errors.")
                sys.exit()

            if keep_all_seeds:
                print(f"Took an average of {total_time/alive:.3f} to gen each seed. Min time: {min_time:.3f}, Max time: {max_time:.3f}")

            return task_mapping[task_id]




        task = get_working_seed()
        seedname = copy_seed(task, output_path)

        print()
        print(f"Took {time.perf_counter()-start:.3f} seconds to generate rom(s).")
        multidataname = f"DR_{seedname}_multidata"
        spoilername = f"DR_{seedname}_Spoiler.txt"
        romfilename = ""

        if player_name:
            for file in os.listdir(output_path):
                if player_name in file:
                    import webbrowser
                    romfilename = os.path.join(output_path, file)
                    print(f"Launching ROM file {romfilename}")
                    webbrowser.open(romfilename)
                    break

        if any((zip_roms, zip_multidata, zip_spoiler, zip_diffs)):
            import zipfile
            compression = {1 : zipfile.ZIP_DEFLATED,
                           2 : zipfile.ZIP_LZMA,
                           3 : zipfile.ZIP_BZIP2}[zip_format]

            typical_zip_ending = {1: "zip",
                                  2: "7z",
                                  3: "bz2"}[zip_format]

            def pack_file(file: str):
                zf.write(os.path.join(output_path, file), file)
                print(f"Packed {file} into zipfile {zipname}")

            def remove_zipped_file(file: str):
                os.remove(os.path.join(output_path, file))
                print(f"Removed {file} which is now present in the zipfile")

            zipname = os.path.join(output_path, f"DR_{seedname}.{typical_zip_ending}")
            print(f"Creating zipfile {zipname}")
            ipv4 = get_public_ipv4()
            with zipfile.ZipFile(zipname, "w", compression=compression, compresslevel=9) as zf:
                for file in os.listdir(output_path):
                    if file.endswith(".sfc") and seedname in file:
                        if zip_diffs:
                            diff = os.path.split(create_patch_file(os.path.join(output_path, file), ipv4))[1]
                            pack_file(diff)
                            if zip_diffs == 2:
                                remove_zipped_file(diff)
                        if zip_roms:
                            pack_file(file)
                            if zip_roms == 2 and player_name.lower() not in file.lower():
                                remove_zipped_file(file)
                if zip_multidata and os.path.exists(os.path.join(output_path, multidataname)):
                    pack_file(multidataname)
                    if zip_multidata == 2:
                        remove_zipped_file(multidataname)
                if zip_spoiler and create_spoiler:
                    pack_file(spoilername)
                    if zip_spoiler == 2:
                        remove_zipped_file(spoilername)

        if os.path.exists(os.path.join(output_path, multidataname)):
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
