from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, ALL
import cv2
import subprocess as sp

FFMPEG_BIN = "ffmpeg"

app = Flask(__name__)
photos = UploadSet('photos', ALL)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img/source'
configure_uploads(app, photos)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        return image(filename)
    return render_template('upload.html')


def image(filename):

    file_folder = filename[0:filename.find('.')]

    command = [ 'rm',
                '-rf',
                'static/img/output/{0}'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    command = [ 'mkdir',
                '-pv',
                'static/img/output/{0}'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    command = [ FFMPEG_BIN,
                '-i', 'static/img/source/' + filename,
                '-r', '15',
                '-y',
                '-f', 'image2',
                'static/img/output/{0}/%04d.png'.format(file_folder)]
    pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

    return render_template('view.html', image='static/img/output/{0}/0001.png'.format(file_folder))


if __name__ == '__main__':
    app.run(debug=True)