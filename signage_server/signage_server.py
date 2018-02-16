"""
For python 3.5+

python requirements:
* flask
* jinja2
* yaml

other requirements:
* wkhtmltopdf
* pngcrush

its possible to do a headless server with a virtual xorg server

run:
export FLASK_APP=signage_server.py
export FLASK_DEBUG=1
flask run --host=0.0.0.0

"""

import datetime
import subprocess
from os.path import getmtime
from tempfile import NamedTemporaryFile

import yaml
from flask import Flask, send_file
from jinja2 import Template

app = Flask(__name__)

config_filename = 'config.yaml'

_last_config = 0
_config = dict()


def get_config():
    # TODO: inotify? class?
    global _last_config
    global _config
    ts = getmtime(config_filename)
    if ts > _last_config:
        _last_config = ts
        with open(config_filename) as fp:
            _config = yaml.load(fp)
    return _config


def update_image():
    """ Create new image for use as digital signage

    :rtype: str
    """
    config = get_config()

    render = config['render']
    messages = config['messages']

    # fill in messages info with current data
    now = datetime.datetime.now()
    messages['weekday'] = now.strftime("%A")
    messages['date_string'] = now.strftime(messages['date_format'])

    # read template data
    with open(render['template']) as fp:
        template = Template(fp.read())

    # use temp. file to render html and make an image
    # do not remove suffix param when using wkhtmltoimage
    with NamedTemporaryFile('w', suffix='.html') as fp:
        # record the name of the temp file
        render['temp_html'] = fp.name

        # render template as html to a temp file
        fp.write(template.render(messages))
        fp.flush()  # make sure data is truly ready to be read later

        # render to a png
        cmd = render['render_cmd'].format(**render)
        subprocess.run(cmd, shell=True)

    # change image to greyscale & optimize file size
    cmd = render['optim_cmd'].format(**render)
    subprocess.run(cmd, shell=True)

    return render['out_image']


@app.route("/kindle-signage.png")
def serve_image():
    # TODO: some kind of check so a cached image is served
    filename = update_image()
    return send_file(filename)
