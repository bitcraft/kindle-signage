"""

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

import subprocess
from tempfile import NamedTemporaryFile
from os.path import getmtime

import arrow
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
    """ Create new image fo use as digital signage

    :return:
    """
    # TODO: some kind of check so a cached image is served
    config = get_config()

    render = config['render']
    messages = config['messages']

    now = arrow.Arrow.now()
    messages['weekday'] = now.strftime("%A")
    messages['date_string'] = now.strftime(messages['date_format'])

    # read template data
    with open(render['template']) as fp:
        template = Template(fp.read())

    # use temp. file to render html and make an image
    # do not remove suffix param when using wkhtmltoimage
    with NamedTemporaryFile('w', suffix='.html') as fp:
        # record the name of the temp file
        render['out_html'] = fp.name

        # render template as html to a temp file
        fp.write(template.render(messages))
        fp.flush()  # make sure data is truly ready to be read later

        # render to a png
        args = 'wkhtmltoimage --width {width} --height {height} {out_html} {out_image}'
        args = args.format(**render)
        args = args.split()
        subprocess.run(args)

    # change image to greyscale & optimize file size
    args = 'pngcrush -rem gAMA -rem cHRM -rem iCCP -rem sRGB -rem alla -rem text -c 0 -ow {out_image}'
    args = args.format(**render)
    args = args.split()
    subprocess.run(args)


@app.route("/kindle-signage.png")
def serve_image():
    config = get_config()
    update_image()
    return send_file(config['render']['out_image'])
