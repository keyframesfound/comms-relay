from flask import Flask, render_template, Response, request
import cv2
import psutil
import os

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
            'disk': psutil.disk_usage('/')
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

if __name__ == '__main__':
    # Run the Flask app on Raspberry Pi's IP address and port 5000
    app.run(host='0.0.0.0', port=7900, debug=False)
