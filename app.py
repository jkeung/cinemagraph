from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, ALL
import cv2
import subprocess as sp

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

    return render_template('process.html', image='static/input/{0}/{0}.png'.format(name))

def image(filename):

    file_folder = filename[0:filename.find('.')]

    command = [ 'rm',
                '-rf',
                'static/output/{0}'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    command = [ 'mkdir',
                '-pv',
                'static/output/{0}'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    command = [ FFMPEG_BIN,
                '-i', 'static/video/' + filename,
                '-r', '15',
                '-y',
                '-f', 'image2',
                'static/output/{0}/%04d.png'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    return render_template('view.html', image='static/output/{0}/0001.png'.format(file_folder))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
