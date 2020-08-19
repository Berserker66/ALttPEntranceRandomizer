import os
import tempfile
import random
import zlib
import json
import multiprocessing

from flask import request, flash, redirect, url_for, session, render_template

from EntranceRandomizer import parse_arguments
from Main import main as ERmain
from Main import get_seed, seeddigits

from .models import *
from WebHostLib import app
from .check import get_yaml_data, roll_yamls


@app.route('/generate', methods=['GET', 'POST'])
@app.route('/generate/<race>', methods=['GET', 'POST'])
def generate(race=False):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
        else:
            file = request.files['file']
            options = get_yaml_data(file)
            if type(options) == str:
                flash(options)
            else:
                results, gen_options = roll_yamls(options)
                if any(type(result) == str for result in results.values()):
                    return render_template("checkresult.html", results=results)
                elif len(gen_options) > app.config["MAX_ROLL"]:
                    flash(f"Sorry, generating of multiworlds is limited to {app.config['MAX_ROLL']} players for now. "
                          f"If you have a larger group, please generate it yourself and upload it.")
                else:

                    gen = Generation(options={name: vars(options) for name, options in gen_options.items()},
                                     # convert to json compatible
                                     meta={"race": race, "owner": session["_id"].int}, state=STATE_QUEUED,
                                     owner=session["_id"])
                    commit()

                    return redirect(url_for("wait_seed", seed=gen.id))
    return render_template("generate.html", race=race)


def gen_game(gen_options, race=False, owner=None, sid=None):
    try:
        target = tempfile.TemporaryDirectory()
        playercount = len(gen_options)
        seed = get_seed()
        random.seed(seed)

        if race:
            random.seed()  # reset to time-based random source

        seedname = "M" + (f"{random.randint(0, pow(10, seeddigits) - 1)}".zfill(seeddigits))

        erargs = parse_arguments(['--multi', str(playercount)])
        erargs.seed = seed
        erargs.name = {x: "" for x in range(1, playercount + 1)}  # only so it can be overwrittin in mystery
        erargs.create_spoiler = not race
        erargs.race = race
        erargs.skip_playthrough = race
        erargs.outputname = seedname
        erargs.outputpath = target.name
        erargs.teams = 1
        erargs.progression_balancing = {}
        erargs.create_diff = True

        for player, (playerfile, settings) in enumerate(gen_options.items(), 1):
            for k, v in settings.items():
                if v is not None:
                    getattr(erargs, k)[player] = v

            if not erargs.name[player]:
                erargs.name[player] = os.path.split(playerfile)[-1].split(".")[0]

        erargs.names = ",".join(erargs.name[i] for i in range(1, playercount + 1))
        del (erargs.name)

        erargs.skip_progression_balancing = {player: not balanced for player, balanced in
                                             erargs.progression_balancing.items()}
        del (erargs.progression_balancing)
        ERmain(erargs, seed)

        return upload_to_db(target.name, owner, sid)
    except BaseException:
        with db_session:
            Generation.get(id=sid).state = STATE_ERROR
        raise


@app.route('/wait/<suuid:seed>')
def wait_seed(seed: UUID):
    seed_id = seed
    seed = Seed.get(id=seed_id)
    if seed:
        return redirect(url_for("view_seed", seed=seed_id))
    generation = Generation.get(id=seed_id)

    if not generation:
        return "Generation not found."
    elif generation.state == STATE_ERROR:
        return "Generation failed, please retry."
    return render_template("wait_seed.html", seed_id=seed_id)


def upload_to_db(folder, owner, sid):
    patches = set()
    spoiler = ""
    multidata = None
    for file in os.listdir(folder):
        file = os.path.join(folder, file)
        if file.endswith(".bmbp"):
            player = int(file.split("P")[1].split(".")[0].split("_")[0])
            patches.add(Patch(data=open(file, "rb").read(), player=player))
        elif file.endswith(".txt"):
            spoiler = open(file, "rt").read()
        elif file.endswith("multidata"):
            try:
                multidata = json.loads(zlib.decompress(open(file, "rb").read()))
            except Exception as e:
                flash(e)
    if multidata:
        with db_session:
            seed = Seed(multidata=multidata, spoiler=spoiler, patches=patches, owner=owner, id=sid)
            for patch in patches:
                patch.seed = seed
            Generation.get(id=sid).delete()
        return seed.id
