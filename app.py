import os
import shutil
from flask import Flask, render_template, send_from_directory, request, url_for, send_file, jsonify
from flask_socketio import SocketIO
from pdf2image import convert_from_path
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


def conversion_task(filepath, filename):
    """Converts PDF to images in a background task."""
    output_folder = os.path.join(
        app.config['UPLOAD_FOLDER'], os.path.splitext(filename)[0])
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        images = convert_from_path(filepath)
        total_pages = len(images)

        for i, image in enumerate(images):
            image.save(os.path.join(output_folder, f'page_{i+1}.png'), 'PNG')
            progress = int(((i + 1) / total_pages) * 100)
            socketio.emit('progress', {'data': f'{progress}%'})
            eventlet.sleep(0.1)

        zip_filename = f'{os.path.splitext(filename)[0]}.zip'

        downloads_dir = 'downloads'
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir)

        archive_base = os.path.join(
            downloads_dir, os.path.splitext(filename)[0])
        shutil.make_archive(archive_base, 'zip', output_folder)

        socketio.emit('progress', {'data': 'Done!'})
        with app.app_context():
            download_url = url_for('download_file', filename=zip_filename)
        socketio.emit('done', {'url': download_url})

    finally:
        shutil.rmtree(output_folder)
        os.remove(filepath)


@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.endswith('.pdf'):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        socketio.start_background_task(conversion_task, filepath, filename)

        return jsonify({'status': 'success'})

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/downloads/<filename>')
def download_file(filename):
    return send_file(os.path.join('downloads', filename), as_attachment=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
