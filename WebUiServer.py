import Utils
from flask import Flask, render_template
import multiprocessing


def flask_server():
    mw_gui = Flask(__name__, static_folder='webUi', template_folder='webUi')

    @mw_gui.route("/", methods=['GET'])
    def base_request():
        return render_template('index.html', version=Utils.__version__)

    Flask.run(mw_gui, None, 5050)


def start_server():
    gui_thread = multiprocessing.Process(target=flask_server)
    gui_thread.start()
