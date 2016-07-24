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

@app.route('/view', methods=['POST'])
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
    first = images[0]
    mask = cv2.imread("static/input/{0}/{0}_mask.png".format(name))
    mask[mask != 0] = 1

    for i, image in enumerate(images):
        print "Applying blending to frame {0} of {1}.".format(i, len(images))
        output = blend(first, image, mask)
        cv2.imwrite("static/output/{0}/{1}.png".format(name, i), output)

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

def blend(image1, image2, mask):
    # generate Gaussian pyramid for image 1
    G = image1.astype(np.float32)
    gpA = [G]
    for i in xrange(6):
        G = cv2.pyrDown(G)
        gpA.append(G.astype(np.float32))

    # generate Gaussian pyramid for image 2
    G = image2.astype(np.float32)
    gpB = [G]
    for i in xrange(6):
        G = cv2.pyrDown(G)
        gpB.append(G.astype(np.float32))

    # generate Gaussian pyramid for mask
    G = mask.astype(np.float32)
    gpM = [G]
    for i in xrange(6):
        G = cv2.pyrDown(G)
        gpM.append(G.astype(np.float32))


    # generate Laplacian Pyramid for image 1
    lpA = [gpA[5]]
    for i in xrange(5,0,-1):
        rows,cols = gpA[i-1].shape[:2]
        GE = cv2.pyrUp(gpA[i])[:rows,:cols]
        L = cv2.subtract(gpA[i-1],GE)
        lpA.append(L)

    # generate Laplacian Pyramid for image 2
    lpB = [gpB[5]]
    for i in xrange(5,0,-1):
        rows,cols = gpB[i-1].shape[:2]
        GE = cv2.pyrUp(gpB[i])[:rows,:cols]
        L = cv2.subtract(gpB[i-1],GE)
        lpB.append(L)

    # Now add the images with mask
    LS = []
    length = len(lpA)
    for i in range(length):
        LS.append(lpB[i]*gpM[length-i-1] + lpA[i]*(1-gpM[length-i-1]))

    # now reconstruct
    ls_ = LS[0]
    for i in xrange(1,6):
        rows,cols = LS[i].shape[:2]
        ls_ = cv2.pyrUp(ls_)[:rows,:cols]
        ls_ = cv2.add(ls_, LS[i])
    ls_ = np.clip(ls_, 0, 255)
    return ls_.astype(np.uint8)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
