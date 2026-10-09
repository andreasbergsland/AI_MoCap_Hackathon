# pose-osc

Real-time human pose estimation to OSC bridge, built for the **Movement & Music Hackathon**
organised by NTNU Music Technology and MishMash WP3 (AI & Creativity for Health and Wellbeing),
Trondheim, October 2025.

The script uses [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker),
[YOLO](https://docs.ultralytics.com/tasks/pose/), or [RTM](https://github.com/Tau-J/rtmlib) to detect body landmarks from a standard
camera feed and streams them as OSC messages to any audio or creative coding environment —
Csound, Max/MSP, Pure Data, SuperCollider, or similar.

---

## The three tracking systems at the hackathon

| System | Machine | OSC address | Port |
|---|---|---|---|
| **pose_osc.py** (MediaPipe, YOLO, or RTM) | NTNU PC | configurable | 9000 (default) |
| **MotionComposer MC-5** (Robert Wechsler) | Robert's machine | `192.168.2.207` | `61` |
| **pose_osc.py** (MediaPipe, YOLO, or RTM) | UiO PC | configurable | 9000 (default) |

See [OSC_REFERENCE.md](OSC_REFERENCE.md) for the NTNU/UiO pipeline address list.
See [MC5_OSC_REFERENCE.md](MC5_OSC_REFERENCE.md) for Robert's MC-5 address list.

---

## Hardware requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | Any modern quad-core | Intel i7/i9 or AMD Ryzen 7/9 |
| GPU | Not required (MediaPipe runs on CPU) | NVIDIA RTX series for YOLO backend |
| RAM | 8 GB | 16 GB or more |
| Camera | Any USB webcam | Logitech C922 or similar 60fps webcam |
| OS | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11 / macOS 13+ / Ubuntu 22.04 |

**Camera placement:** 2–4 metres from the performer at roughly chest height.
Full-body landmarks (hips, knees, ankles) require the whole body visible in frame.
Upper-body landmarks (shoulders, elbows, wrists) work reliably at closer range.

**GPU laptops:** Any NVIDIA GPU with 4GB+ VRAM (GTX 1650 or newer, any RTX) will
accelerate YOLO nad RTM inference to ~10–20ms. Without a GPU, MediaPipe runs on CPU at ~30–70ms
depending on the machine — workable for continuous parameter sonification.
Apple Silicon Macs (M1/M2/M3) are also supported via the MPS backend.

**Two-machine setup:** connect via ethernet with static IPs on the same subnet
(e.g. `192.168.1.3` PC, `192.168.1.2` Mac). Set Sleep and Screen to Never on both
machines to prevent the network link dropping during a session.

---

## Software dependencies

- Python 3.10
- [Miniconda](https://www.anaconda.com/download/success)
- mediapipe >= 1.0.1
- opencv-python >= 5.0.0
- torch >= 2.14.0
- python-osc >= 1.10.0
- ultralytics >= 8.4
- rtmlib >= 0.0.16

---

## Installation

### 1. Install Miniconda

Download [Miniconda](https://www.anaconda.com/download/success) for your platform.
On Windows, tick **"Add Miniconda3 to my PATH environment variable"** during install.

### 2. Create the environment

```bash
conda create -n pose python=3.10 -y
conda activate pose
```

### 3. Install CUDA toolkit (Windows/Linux with NVIDIA GPU)

```bash
conda install -c nvidia cuda-toolkit=12.6 -y
```

Skip this step on macOS or on machines without an NVIDIA GPU.

### 4. Install PyTorch

**With CUDA (Windows/Linux, NVIDIA GPU):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

**CPU only or macOS:**
```bash
pip install torch torchvision
```

### 5. Install remaining dependencies

```bash
pip install mediapipe opencv-python python-osc ultralytics rtmlib
```

### 6. Verify the installation

```bash
python -c "
import mediapipe, cv2, torch
from pythonosc import udp_client
from ultralytics import YOLO
print('MediaPipe:', mediapipe.__version__)
print('OpenCV:', cv2.__version__)
print('Torch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('All OK')
"
```

---

## Usage

```bash
python pose_osc.py [options]
```

### Options

| Argument | Default | Description |
|---|---|---|
| `--backend` | `mediapipe` | Tracking backend: `mediapipe`, `yolo`, or `rtm` |
| `--model` | `full` | MediaPipe model: `lite`, `full`, `heavy` |
| `--yolo-model` | `yolov8n-pose` | YOLO model: `yolov8n-pose`, `yolov8s-pose`, `yolov8m-pose`, `yolov8l-pose` |
| `--max-persons` | `1` | Max persons to track — **YOLO only, must set explicitly for multi-person** |
| `--ip` | `127.0.0.1` | OSC target IP address |
| `--port` | `9000` | OSC target port |
| `--alpha` | `0.2` | Smoothing: 0.0 = maximum smoothing, 1.0 = no smoothing |
| `--presence` | `0.5` | Reliability threshold for landmarks |
| `--camera` | `0` | Camera device index |
| `--no_draw` | N/A | Flad to disable drawing |

### Examples

```bash
# MediaPipe, defaults — localhost port 9000
python pose_osc.py

# YOLO backend, single person (GPU accelerated if available)
python pose_osc.py --backend yolo

# YOLO, two persons — must pass --max-persons explicitly
python pose_osc.py --backend yolo --max-persons 2

# YOLO, two persons, send to another machine
python pose_osc.py --backend yolo --max-persons 2 --ip 192.168.1.2 --port 9000

# More smoothing for slow expressive movement
python pose_osc.py --alpha 0.1

# Less smoothing for fast percussive gestures
python pose_osc.py --alpha 0.4

# Lite model for slower machines
python pose_osc.py --model lite

# Show all options
python pose_osc.py --help
```

---

## Backends compared

| Feature | MediaPipe | YOLO/RTM |
|---|---|---|
| Landmarks | 33 (full body + face + hand detail) | 17 (COCO skeleton) |
| Inference | ~30ms on CPU | ~5–20ms on GPU |
| Multi-person | Single person only | Up to N via --max-persons |
| GPU required | No | No (but much faster with one) |
| Best for | Detailed hand/face tracking | Speed, multi-person |

OSC addresses are identical between backends — patches work with both.

---

## Multi-person tracking

Multi-person tracking is available with the YOLO and RTM backends. It is **off by default** —
you must pass `--max-persons 2` (or higher) explicitly:

```bash
python pose_osc.py --backend yolo --max-persons 2
```

The startup output will remind you if you forget:

```
Backend:     yolov8n-pose
Max persons: 1
             ↑ Use --max-persons 2 (or more) for multi-person tracking
```

**Important — no persistent identity:** YOLO/RTM detects persons in order of confidence score
per frame, not by persistent identity. This means if one performer walks out of frame and
back in, they may swap between `/pose/...` and `/pose/2/...`. For the hackathon this is
generally fine, but participants should be aware that person numbering is not guaranteed
to stay consistent across a full session.

OSC address prefixes per person:

| Person | Prefix | Example |
|---|---|---|
| Person 1 | `/pose` | `/pose/smooth/left_wrist` |
| Person 2 | `/pose/2` | `/pose/2/smooth/left_wrist` |
| Person 3 | `/pose/3` | `/pose/3/smooth/left_wrist` |

---

## What you will see

When running, the script opens a camera window showing:
- **Green filled dots** — landmarks detected reliably
- **Red filled dots** — landmarks detected but unreliable (low presence)
- **Blue hollow circles** — smoothed landmark positions
- Person 2 landmarks appear in **yellow/magenta** when multi-person is active

Every 3 seconds the terminal prints which landmarks are currently reliable:

```
── Tracking summary ──────────────────────────────────────────
  Person 1  (OSC: /pose/...)
  Reliable:   nose, left_shoulder, right_shoulder, left_wrist, right_wrist
  Unreliable: left_hip, right_hip, left_knee, right_knee
```

Press **q** to quit.

---

## OSC reference

See [OSC_REFERENCE.md](OSC_REFERENCE.md) for all addresses, argument counts,
and code examples for Csound, Max/MSP and Pure Data.

---

## Template patches

Coming soon:
- `templates/csound/` — Csound `.csd` examples
- `templates/max/` — Max/MSP `.maxpat` examples
- `templates/pd/` — Pure Data `.pd` examples

---

## Notes for Windows users

- Activating the conda environment may print Visual Studio 2017 warnings — these are
  harmless. The environment is active when `(pose)` appears in your prompt.
- Set **Sleep** and **Screen** to **Never** in Power & Sleep settings to prevent the
  network adapter dropping during a session.
- If Csound cannot receive OSC, add a UDP inbound rule for port 9000 in Windows
  Defender Firewall.

---

## Acknowledgements

Developed as part of the Movement & Music Hackathon,
NTNU Music Technology / MishMash WP3: AI & Creativity for Health and Wellbeing.

Pose estimation: [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker) (Google)
and [YOLOv8 Pose](https://docs.ultralytics.com/tasks/pose/) (Ultralytics).
