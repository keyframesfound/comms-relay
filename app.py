from flask import Flask, render_template, Response, request
import cv2
import psutil
import os
import time
from threading import Lock, Thread

app = Flask(__name__)

# Initialize our cameras for device indices 0 and 1 and optimize resolution for Raspberry Pi.
camera_0 = cv2.VideoCapture(0)
camera_1 = cv2.VideoCapture(1)
camera_0.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera_0.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
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
        time.sleep(0.03)  # slight delay to reduce CPU usage

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
        time.sleep(0.03)

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
        return Response(gen_threaded(latest_frame_1, frame_1_lock), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Invalid camera", 404

if __name__ == '__main__':
    # Start background threads to continuously capture frames.
    Thread(target=capture_frames, args=(camera_0, frame_0_lock, latest_frame_0), daemon=True).start()
    Thread(target=capture_frames, args=(camera_1, frame_1_lock, latest_frame_1), daemon=True).start()
    # Run the Flask app on Raspberry Pi's IP address and port 5000
    app.run(host='0.0.0.0', port=7900, debug=False)