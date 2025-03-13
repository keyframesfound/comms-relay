# Raspberry Pi Video & Stats

This project provides live video feeds and system statistics for a Raspberry Pi based setup.

## Features

- **Cameras Tab**: 
  - Displays multiple live video streams.
  - Each stream has a button to view in full screen.
  - Access via the `/?tab=cameras` URL parameter.

- **Py Cameras Tab**:  
  - Integrates Python-based camera feeds.
  - Each stream can be viewed full screen.
  - Access via the `/?tab=pycameras` URL parameter.

- **Raspberry Pi Stats Tab**:  
  - Shows real-time CPU usage, temperature, and memory statistics.
  - Auto-refreshes every 3 seconds.
  - Access via the `/?tab=stats` URL parameter.

- **Empty Tab**:  
  - Placeholder content for future enhancements.

## Usage

1. app.py refers to the normal MacOS version
2. raspberry.py refers to the RaspberryPi version 

## Setup

- Ensure your Raspberry Pi is connected to the network.
- The server must be running to serve the following routes:
  - `/video_feed` for standard camera streams.
  - `/video_feed_py` for Python camera streams.
  - `/` with appropriate query parameters for different tabs.

## Project Structure

- **Templates**
  - `/Users/ryanyeung/comms-relay/templates/index.html`: Main HTML file for rendering the interface.

- **Server Code**
  - (Refer to your project-specific files and documentation for backend implementation.)

## New Picamera2 Endpoints

- **/pi_image**  
  Captures a still image from the Pi Camera using Picamera2.

- **/pi_mjpeg**  
  Streams MJPEG video from the Pi Camera using Picamera2.

## Installation Guide

1. Connect your camera to the Raspberry Pi.
2. Install Picamera2 library:
   ```
   sudo apt-get update
   sudo apt-get install python3-picamera2
   ```
3. Set up the project environment:
   ```
   mkdir camera-app
   cd camera-app
   python3 -m venv --system-site-packages venv
   source venv/bin/activate
   ```
4. Test the camera using the sample script in `/comms-relay/main.py`:
   ```
   python main.py
   ```

## Installation

1. **Update your package list:**
   ```bash
   sudo apt-get update
   ```

2. **Install system dependencies:**
   ```bash
   sudo apt-get install python3 python3-pip libopencv-dev
   ```

3. **Install Python dependencies:**
   ```bash
   pip3 install flask opencv-python psutil
   ```

4. **Camera Setup:**
   - Make sure your Raspberry Pi cameras are connected and recognized as `/dev/video0` and `/dev/video1`.
   - The app sets a resolution of 640x480 for performance on the Pi. Adjust in the code if needed.

## Running the Application

Start the Flask server by running:
```bash
python3 app.py
```
Then access the stream at:
```
http://<your_pi_ip>:7900/video_feed/0
```
or
```
http://<your_pi_ip>:7900/video_feed/1
```

<!-- ...additional project setup information... -->
