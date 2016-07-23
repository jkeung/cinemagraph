from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, ALL
import cv2
import subprocess as sp
import re
import base64
import os
from glob import glob
import numpy as np

FFMPEG_BIN = "ffmpeg"

app = Flask(__name__)
videos = UploadSet('videos', ALL)
app.config['UPLOADED_VIDEOS_DEST'] = 'static/video/'
configure_uploads(app, videos)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' in request.files:
        filename = videos.save(request.files['file'])
        return extract_first_frame(filename)
    return render_template('500.html')

@app.route('/mask', methods=['POST'])
def mask():

    datauri = request.form['data']
    name = request.form['name'] 
    filename = request.form['filename']
    
    imgstr = re.search(r'base64,(.*)', datauri).group(1)

    with open('static/input/{0}/{0}_mask.png'.format(name), 'wb') as f:
        f.write(base64.b64decode(imgstr))

    command = [ 'mkdir',
                '-pv',
                'static/frames/{0}'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE)

    command = [ 'mkdir',
                '-pv',
                'static/output/{0}'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE)

    command = [ FFMPEG_BIN,
                '-i', 'static/video/' + filename,
                '-r', '15',
                '-y',
                '-vf', 'scale=1280:720',
                '-f', 'image2',
                'static/frames/{0}/%04d.png'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=2**16)
    pipe.wait()

    images = readImages("static/frames/{0}/".format(name))
    mask = cv2.imread("static/input/{0}/{0}_mask.png".format(name))
    mask[mask != 0] = 1

    for i, image in enumerate(images):
        cv2.imwrite("static/output/{0}/{1}.png".format(name, i), image*mask + images[0]*(1-mask))

    command = [ FFMPEG_BIN,
                '-i', 'static/output/{0}/%d.png'.format(name),
                'static/output/{0}/{0}.gif'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=2**16)
    pipe.wait()

    return render_template('view.html', image='static/output/{0}/{0}.gif'.format(name))

def readImages(image_dir):
    """ This function reads in input images from a image directory

    Note: This is implemented for you since its not really relevant to
    computational photography (+ time constraints).

    Args:
        image_dir (str): The image directory to get images from.

    Returns:
        images(list): List of images in image_dir. Each image in the list is of
                      type numpy.ndarray.

    """
    extensions = ['bmp', 'pbm', 'pgm', 'ppm', 'sr', 'ras', 'jpeg',
                  'jpg', 'jpe', 'jp2', 'tiff', 'tif', 'png']

    search_paths = [os.path.join(image_dir, '*.' + ext) for ext in extensions]
    image_files = sorted(reduce(list.__add__, map(glob, search_paths)))
    images = [cv2.imread(f, cv2.IMREAD_UNCHANGED | cv2.IMREAD_COLOR)
              for f in image_files]

    return images


def extract_first_frame(filename):
    name = filename[0:filename.find('.')]
    command = [ 'rm',
                '-rf',
                'static/input/{0}'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE)

    command = [ 'mkdir',
                '-pv',
                'static/input/{0}'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE)

    command = [ FFMPEG_BIN,
                '-i', 'static/video/' + filename,
                '-vframes', '1',
                '-vf', 'scale=1280:720',
                '-f', 'image2',
                'static/input/{0}/{0}.png'.format(name)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=2**16)
    pipe.wait()

    return render_template('process.html', image='static/input/{0}/{0}.png'.format(name), name=name, filename=filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
