from flask import Flask, render_template, Response, request
import cv2
import psutil
import os
import time
from threading import Lock, Thread
from flask_socketio import SocketIO, emit
import base64
import threading
import subprocess

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize camera₀
camera_0 = cv2.VideoCapture(0)
camera_0.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera_0.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
if not camera_0.isOpened():
    camera_0.release()
    camera_0 = "fswebcam0"  # flag to use fswebcam for cam0

# Initialize camera₁
camera_1 = cv2.VideoCapture(1)
if not camera_1.isOpened():
    camera_1.release()
    camera_1 = "fswebcam"  # flag to use fswebcam for cam1
else:
    camera_1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera_1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Global containers for latest frames and their locks
latest_frame_0 = [None]
latest_frame_1 = [None]
frame_0_lock = Lock()
frame_1_lock = Lock()

# New function: continuously capture frames in a background thread.
def capture_frames(camera, lock, frame_container):
    while True:
        ret, frame = camera.read()
        if ret:
            with lock:
                frame_container[0] = frame
        time.sleep(0.005)  # reduced sleep for lower latency

# Updated fswebcam capture function to support different devices.
def capture_fswebcam_frames(lock, frame_container, device, tmp_file):
    while True:
        subprocess.run(["fswebcam", "-d", device, "--no-banner", "-r", "640x480", tmp_file])
        frame = cv2.imread(tmp_file)
        if frame is not None:
            with lock:
                frame_container[0] = frame
        time.sleep(0.005)

# New generator: deliver the latest captured frame.
def gen_threaded(frame_container, lock):
    while True:
        with lock:
            frame = frame_container[0]
        if frame is None:
            continue
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        time.sleep(0.005)  # reduced sleep for lower latency

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            return float(temp_str)/1000.0
    except Exception:
        return None

@app.route('/')
def index():
    tab = request.args.get('tab', 'cameras')
    system_stats = {}
    if tab == 'stats':
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory()._asdict(),
            'temperature': get_cpu_temperature(),
        }
    return render_template('index.html', tab=tab, stats=system_stats)

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    if cam_id == 0:
        return Response(gen_threaded(latest_frame_0, frame_0_lock), mimetype='multipart/x-mixed-replace; boundary=frame')
    elif cam_id == 1:
        if camera_1:
            return Response(gen_threaded(latest_frame_1, frame_1_lock), mimetype='multipart/x-mixed-replace; boundary=frame')
        else:
            return "Camera not available", 404
    else:
        return "Invalid camera", 404

# Modified background function: emits frames over SocketIO for real-time streaming with distinct events.
def emit_frames():
    while True:
        cameras = {0: (latest_frame_0, frame_0_lock)}
        if camera_1:
            cameras[1] = (latest_frame_1, frame_1_lock)
        for cam_id, (frame_container, lock) in cameras.items():
            with lock:
                frame = frame_container[0]
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    jpg_as_text = base64.b64encode(jpeg.tobytes()).decode('utf-8')
                    socketio.emit(f'video_frame_{cam_id}', {'frame': jpg_as_text})
        time.sleep(0.005)  # minimal delay for near real-time updates

# SocketIO event: start emitting frames on client connection.
@socketio.on('connect')
def handle_connect():
    threading.Thread(target=emit_frames, daemon=True).start()
    emit('message', {'data': 'Connected and streaming video'})

if __name__ == '__main__':
    # Start background threads to continuously capture frames.
    if camera_0 == "fswebcam0":
        Thread(target=capture_fswebcam_frames, args=(frame_0_lock, latest_frame_0, "/dev/video0", "/tmp/camera0.jpg"), daemon=True).start()
    else:
        Thread(target=capture_frames, args=(camera_0, frame_0_lock, latest_frame_0), daemon=True).start()
    if camera_1 == "fswebcam":
        Thread(target=capture_fswebcam_frames, args=(frame_1_lock, latest_frame_1, "/dev/video1", "/tmp/camera1.jpg"), daemon=True).start()
    else:
        Thread(target=capture_frames, args=(camera_1, frame_1_lock, latest_frame_1), daemon=True).start()
    # Run the app with SocketIO to support WebSocket communication.
    socketio.run(app, host='0.0.0.0', port=7900, debug=False)