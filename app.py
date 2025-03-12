from flask import Flask, render_template, Response, request
import cv2
import psutil
import os
import io
import numpy as np  # added for black frame generation
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import MJPEGEncoder, Quality
from picamera2.outputs import FileOutput

app = Flask(__name__)

# Initialize our cameras for device indices 0 and 1
camera_0 = cv2.VideoCapture(0)
camera_1 = cv2.VideoCapture(1)

def gen(camera):
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# New helper generator: use system camera and yield a black frame if feed fails.
def gen_system(camera):
    while True:
        success, frame = camera.read()
        if not success:
            # Create a black frame (1080p)
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Updated generator: try Picamera2 first, then fallback to system camera (with black screen on failure)
def generate_combined_frames(cam_id):
    try:
        picam2 = Picamera2()
        video_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
        picam2.configure(video_config)
        picam2.start()
        while True:
            frame_array = picam2.capture_array()
            ret, jpeg = cv2.imencode('.jpg', frame_array)
            if ret:
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        picam2.stop()
        picam2.close()
    except Exception as e:
        # Fallback: use system camera via gen_system
        fallback_camera = camera_0 if cam_id == 0 else camera_1
        yield from gen_system(fallback_camera)

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
        return Response(gen(camera_0), mimetype='multipart/x-mixed-replace; boundary=frame')
    elif cam_id == 1:
        return Response(gen(camera_1), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Invalid camera", 404

@app.route('/combined_feed/<int:cam_id>')
def combined_feed(cam_id):
    return Response(generate_combined_frames(cam_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# New endpoint: capture still image using Picamera2
@app.route('/pi_image')
def pi_image():
    picam2 = Picamera2()
    capture_config = picam2.create_still_configuration(main={"size": (1920, 1080)})
    picam2.configure(capture_config)
    data = io.BytesIO()
    picam2.start()
    picam2.capture_file(data, format="jpeg")
    picam2.stop()
    picam2.close()
    return Response(data.getvalue(), mimetype="image/jpeg")

# New helper class for streaming
class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()
    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

def generate_frames(output):
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

# New endpoint: stream MJPEG video using Picamera2
@app.route('/pi_mjpeg')
def pi_mjpeg():
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
    picam2.configure(video_config)
    output = StreamingOutput()
    picam2.start_recording(MJPEGEncoder(), FileOutput(output), Quality.VERY_HIGH)
    # Note: proper cleanup of recording is advised on disconnect.
    return Response(generate_frames(output),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    # Run the Flask app on Raspberry Pi's IP address and port 5000
    app.run(host='0.0.0.0', port=7900, debug=False)