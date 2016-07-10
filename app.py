from flask import Flask, render_template, request
from flask.ext.uploads import UploadSet, configure_uploads, ALL
import cv2


app = Flask(__name__)
photos = UploadSet('photos', ALL)
app.config['UPLOADED_PHOTOS_DEST'] = 'static/img'
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
    vidcap = cv2.VideoCapture(filename)
    success, image = vidcap.read()
    print success
    cv2.imwrite('static/img/firstframe.jpg', image)
    return render_template('view.html', image='static/img/{0}'.format(filename))
if __name__ == '__main__':
    app.run(debug=True)