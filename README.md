# Tello Crowd Density Monitor

A real-time crowd density monitoring system using a **DJI Tello drone**, **YOLOv8** for person detection, and **AprilTag** markers for dynamic area calibration.

Built as a computer vision and robotics project at **Universidad de O'Higgins (UOH)**.

---

## Demo

> *Flight demo video / GIF coming soon*

---

## How It Works

The drone flies over a delimited area marked by **AprilTag** fiducial markers placed on the ground. The system:

1. Detects the AprilTags to define the monitored polygon area
2. Uses the known real-world distance between two reference tags to dynamically calibrate pixel-to-meter conversion at any flight altitude
3. Runs **YOLOv8** to detect people in each frame
4. Counts how many people are inside the polygon
5. Calculates crowd density (people/m²) in real time
6. Overlays all telemetry data on the live video feed and saves every frame

---

## Features

- Real-time person detection with YOLOv8
- Dynamic area calibration (works at any altitude)
- Crowd density calculation (people / m²)
- Live telemetry overlay: area, density, drone height, battery, flight time
- Automatic frame saving (raw + processed)
- Safe landing on keypress or Ctrl+C
- macOS and Linux/Windows compatible

---

## Tech Stack

| Component | Technology |
|---|---|
| Drone | DJI Tello (djitellopy) |
| Person detection | YOLOv8 (Ultralytics) |
| Area markers | AprilTags - tag36h11 (pupil-apriltags) |
| Image processing | OpenCV, NumPy |
| Keyboard input | pynput (macOS) / OpenCV (Linux/Windows) |

---

## Project Structure

```
tello-crowd-monitor/
├── main.py               # Main application
├── requirements.txt      # Python dependencies
├── README.md
└── images/               # Auto-generated on first run
    └── YYYYMMDD_HHMMSS/
        ├── 000001.png    # Raw frames
        └── processed/
            └── 000001.png  # Frames with detections
```

---

## Setup

### Requirements

- Python 3.9+
- DJI Tello drone
- YOLOv8 model file (`yolo26m.pt`) in the project root
- AprilTag markers (tag36h11 family) — at least 3, ideally 4

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/tello-crowd-monitor.git
cd tello-crowd-monitor
pip install -r requirements.txt
```

### Running

1. Connect your computer to the Tello's WiFi network
2. Place AprilTag markers on the ground to define the monitored area
3. Make sure tag **ID 2** and **ID 4** are on the top edge of the area, exactly **1.50 m apart**
4. Run:

```bash
python main.py
```

5. Press `l` or `Escape` to land safely

> To enable actual takeoff, uncomment the `tello.takeoff()` lines in `main.py`

---

## Configuration

| Parameter | Location | Default | Description |
|---|---|---|---|
| `DISTANCIA_REAL_METROS` | `construir_zona_y_calcular_area()` | `1.50` | Real distance between reference tags (meters) |
| `fps` | `loop_principal()` | `5` | Frame save rate |
| Reference tag IDs | `construir_zona_y_calcular_area()` | `2` and `4` | IDs of the top-edge reference tags |

---

## Controls

| Key | Action |
|---|---|
| `l` | Safe land |
| `Escape` | Safe land |
| `Ctrl+C` | Emergency safe land |

---

## License

MIT License — free to use and modify with attribution.

---

## Author

Developed at Universidad de O'Higgins (UOH)  
Computer Vision · Robotics · Python
