# pose-osc

Real-time human pose estimation to OSC bridge, built for the **Movement & Music Hackathon**
organised by NTNU Music Technology and MishMash, Trondheim, October 2025.

The script at the moment uses [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker)
to detect 33 body landmarks from a standard camera feed and streams them as OSC messages
to any audio or creative coding environment — Csound, Max/MSP, Pure Data, SuperCollider, or similar.
Having [YoLo](https://docs.ultralytics.com/tasks/pose) as an alternative framework is also planned. 

---

## Hardware requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | Any modern quad-core | Intel i7/i9 or AMD Ryzen 7/9 |
| GPU | Not required (CPU inference) | NVIDIA RTX series (future GPU support) |
| RAM | 8 GB | 16 GB or more |
| Camera | Any USB webcam | Logitech C922 or similar 60fps webcam |
| OS | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11 / macOS 13+ / Ubuntu 22.04 |

**Camera placement:** position the camera 2–4 metres from the performer at roughly chest height.
Full-body landmarks (hips, knees, ankles) require the whole body to be visible in frame.
Upper-body landmarks (shoulders, elbows, wrists) work reliably at closer range.

**Two-machine setup:** if running the pose script on one machine and the audio environment
on another, connect both machines via ethernet and set static IPs on the same subnet
(e.g. `192.168.1.3` and `192.168.1.2`). See the OSC reference for network configuration notes.

---

## Software dependencies

- Python 3.10
- [Miniconda](https://www.anaconda.com/download/success) (recommended for environment management)
- mediapipe >= 1.0.1
- opencv-python >= 5.0.0
- torch >= 2.14.0 (with or without CUDA)
- python-osc >= 1.10.0
- ultralytics >= 8.4 (installed but not yet active — reserved for future YOLO backend)

---

## Installation

### 1. Install Miniconda

Download and install [Miniconda](https://www.anaconda.com/download/success) for your platform.
During installation on Windows, tick **"Add Miniconda3 to my PATH environment variable"**.

### 2. Create the environment

```bash
conda create -n pose python=3.10 -y
conda activate pose
```

### 3. Install CUDA toolkit (Windows/Linux with NVIDIA GPU)

```bash
conda install -c nvidia cuda-toolkit=12.6 -y
```

On macOS or without a GPU, skip this step — CPU inference works fine.

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
pip install mediapipe opencv-python python-osc ultralytics
```

### 6. Verify the installation

```bash
python -c "
import mediapipe, cv2, torch
from pythonosc import udp_client
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
| `--ip` | `127.0.0.1` | OSC target IP address |
| `--port` | `9000` | OSC target port |
| `--alpha` | `0.2` | Smoothing factor (0.0 = maximum smoothing, 1.0 = no smoothing) |
| `--presence` | `0.5` | Reliability threshold (landmarks below this are flagged as unreliable) |
| `--camera` | `0` | Camera device index |
| `--model` | `full` | MediaPipe model: `lite` (fastest), `full` (default), `heavy` (most accurate) |

### Examples

```bash
# Run with defaults — localhost, port 9000
python pose_osc.py

# Send to another machine
python pose_osc.py --ip 192.168.1.2 --port 9000

# More smoothing, lite model for faster machines
python pose_osc.py --alpha 0.1 --model lite

# Less smoothing for fast percussive gestures
python pose_osc.py --alpha 0.4

# Show all options
python pose_osc.py --help
```

---

## What you will see

When running, the script opens a camera window showing:
- **Green filled dots** — landmarks detected reliably (presence above threshold)
- **Red filled dots** — landmarks detected but unreliable (presence below threshold)
- **Blue hollow circles** — smoothed landmark positions

Every 3 seconds the terminal prints a summary of which landmarks are currently reliable,
which is useful for checking camera placement:

```
── Reliable landmarks ──────────────────────────────────────────
nose, left_shoulder, right_shoulder, left_elbow, right_elbow,
left_wrist, right_wrist
── Not reliable ────────────────────────────────────────────────
left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle
```

Press **q** to quit.

---

## OSC reference

See [OSC_REFERENCE.md](OSC_REFERENCE.md) for the full list of OSC addresses,
argument counts, coordinate system, and notes for Csound, Max/MSP and Pure Data.

---

## Template patches

Coming soon:
- `templates/csound/` — Csound `.csd` examples
- `templates/max/` — Max/MSP `.maxpat` examples
- `templates/pd/` — Pure Data `.pd` examples

---

## Notes for Windows users

- When activating the conda environment you may see Visual Studio 2017 warnings —
  these are harmless and can be ignored. The environment is active if `(pose)` appears
  in your prompt.
- Set your machine's **Sleep** and **Screen** to **Never** in Power & Sleep settings
  to prevent the network adapter from dropping during a session.
- If Csound cannot receive OSC, check Windows Defender Firewall and add a UDP inbound
  rule for port 9000 if needed.

---

## Acknowledgements

Developed as part of the Movement & Music Hackathon, NTNU Music Technology /
MishMash WP3: AI & Creativity for Health and Wellbeing.
Pose estimation: [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker), Google.
Script and instructions generated in dialogue with Claude.
