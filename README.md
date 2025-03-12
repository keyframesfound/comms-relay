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

1. Open your browser and navigate to the project URL.
2. Use the navigation bar to switch between tabs.
3. For video streams, click the **Full Screen** button to enlarge the view.
4. Use the **Py Cameras** tab to access Python-based camera feeds.

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

<!-- ...additional project setup information... -->
