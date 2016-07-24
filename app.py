from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, ALL
import cv2
import subprocess as sp
import re
import base64
import os
from glob import glob
import numpy as np
import math
import assignment6

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
    black_img = images[0]
    black_img.astype(float)
    mask_img = cv2.imread("static/input/{0}/{0}_mask.png".format(name))
    mask_img[mask_img != 0] = 1
    mask_img.astype(float)

    for i, image in enumerate(images):
        
        white_img = image
        white_img.astype(float)

        print "Applying blending to frame {0} of {1}.".format(i, len(images))
        out_layers = []

        for channel in range(3):
              lapl_pyr_black, lapl_pyr_white, gauss_pyr_black, gauss_pyr_white, gauss_pyr_mask,\
                  outpyr, outimg = run_blend(black_img[:,:,channel], white_img[:,:,channel], \
                                   mask_img[:,:,channel])

        out_layers.append(outimg)
        outimg = cv2.merge(out_layers)

        cv2.imwrite("static/output/{0}/{1}.png".format(name, i), outimg)

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

def run_blend(black_image, white_image, mask):
    """ This function administrates the blending of the two images according to 
    mask.

    Assume all images are float dtype, and return a float dtype.
    """

    # Automatically figure out the size
    min_size = min(black_image.shape)
    depth = int(math.floor(math.log(min_size, 2))) - 4 # at least 16x16 at the highest level.

    gauss_pyr_mask = assignment6.gaussPyramid(mask, depth)
    gauss_pyr_black = assignment6.gaussPyramid(black_image, depth)
    gauss_pyr_white = assignment6.gaussPyramid(white_image, depth)

    lapl_pyr_black  = assignment6.laplPyramid(gauss_pyr_black)
    lapl_pyr_white = assignment6.laplPyramid(gauss_pyr_white)

    outpyr = assignment6.blend(lapl_pyr_white, lapl_pyr_black, gauss_pyr_mask)
    outimg = assignment6.collapse(outpyr)

    outimg[outimg < 0] = 0 # blending sometimes results in slightly out of bound numbers.
    outimg[outimg > 255] = 255
    outimg = outimg.astype(np.uint8)

    return lapl_pyr_black, lapl_pyr_white, gauss_pyr_black, gauss_pyr_white, \
      gauss_pyr_mask, outpyr, outimg

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
