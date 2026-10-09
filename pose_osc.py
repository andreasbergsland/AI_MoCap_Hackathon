#!/usr/bin/env python3
"""
pose_osc.py — Real-time pose estimation to OSC bridge
Supports MediaPipe (33 landmarks, CPU), YOLO (17 landmarks, GPU/CPU), and RTM (17 landmarks, GPU/CPU) backends.
NTNU Music Technology / MishMash WP3 Hackathon
"""

import cv2
import time
import argparse
import os
import urllib.request
from pythonosc import udp_client
import platform

# ── Find Nvidia DLLs ──────────────────────────────────────────────────────────
# a bit of monkey-patching...
# because onnxruntime sometimes fails to find the right DLLs on Windows, especially with conda environments
import sys
import glob

# 1. Locate the site-packages directory for the current Python environment
site_packages_path = os.path.join(sys.prefix, "Lib", "site-packages")
nvidia_base_path = os.path.join(site_packages_path, "nvidia")

# 2. Find all 'bin' folders inside the installed nvidia packages (like cudnn)
#    and register them to the Windows DLL search path
if os.path.exists(nvidia_base_path):
    for bin_dir in glob.glob(os.path.join(nvidia_base_path, "*", "bin")):
        try:
            os.add_dll_directory(bin_dir)
            print(f"Success: Registered DLL path -> {bin_dir}")
        except Exception as e:
            print(f"Failed to add {bin_dir}: {e}")

# 3. Native ONNX Runtime helper (available in newer versions)
import onnxruntime as ort
if hasattr(ort, 'preload_dlls'):
    ort.preload_dlls()

# ── ARGUMENT PARSING ──────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Pose estimation → OSC bridge')
parser.add_argument('--backend',     type=str,   default='mediapipe',
                    choices=['mediapipe', 'yolo', 'rtm'],
                    help='Tracking backend (default: mediapipe)')
parser.add_argument('--model',       type=str,   default='full',
                    choices=['lite', 'full', 'heavy'],
                    help='MediaPipe model complexity (default: full)')
parser.add_argument('--yolo-model',  type=str,   default='yolov8n-pose',
                    choices=['yolov8n-pose', 'yolov8s-pose',
                             'yolov8m-pose', 'yolov8l-pose'],
                    help='YOLO pose model (default: yolov8n-pose)')
parser.add_argument('--max-persons', type=int,   default=1,
                    help='Max persons to track — YOLO/RTM only (default: 1)')
parser.add_argument('--alpha',       type=float, default=0.2,
                    help='Smoothing 0.0-1.0 — lower=smoother (default: 0.2)')
parser.add_argument('--ip',          type=str,   default='127.0.0.1',
                    help='OSC target IP (default: 127.0.0.1)')
parser.add_argument('--port',        type=int,   default=9000,
                    help='OSC target port (default: 9000)')
parser.add_argument('--camera',      type=int,   default=0,
                    help='Camera device index (default: 0)')
parser.add_argument('--presence',    type=float, default=0.5,
                    help='Reliability threshold 0.0-1.0 (default: 0.5)')
parser.add_argument('--no_draw',        action='store_true',
                    help='Do not show camera feed with the drawn landmarks')
args = parser.parse_args()

# ── LANDMARK SCHEMAS ──────────────────────────────────────────────────────────
# 17 COCO keypoints — used by YOLO, subset of MediaPipe
COCO_LANDMARKS = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]

# 33 MediaPipe landmarks (superset — includes face detail and hand detail)
MEDIAPIPE_LANDMARKS = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
    'right_eye_inner', 'right_eye', 'right_eye_outer',
    'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
    'left_index', 'right_index', 'left_thumb', 'right_thumb',
    'left_hip', 'right_hip', 'left_knee', 'right_knee',
    'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
    'left_foot_index', 'right_foot_index'
]

# ── LANDMARK DATA CONTAINER ───────────────────────────────────────────────────
class Landmark:
    __slots__ = ['x', 'y', 'z', 'presence']
    def __init__(self, x, y, z=0.0, presence=1.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.presence = float(presence)

    def __repr__(self):
        return f'Landmark(x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f}, presence={self.presence:.3f})'

# ── MEDIAPIPE BACKEND ─────────────────────────────────────────────────────────
MODEL_URLS = {
    'lite':  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task',
    'full':  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task',
    'heavy': 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task',
}

class MediaPipeBackend:
    def __init__(self, model_name, presence_threshold):
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        self.mp        = mp
        self.names     = MEDIAPIPE_LANDMARKS
        self.threshold = presence_threshold

        model_path = f'pose_landmarker_{model_name}.task'
        if not os.path.exists(model_path):
            print(f'Downloading MediaPipe {model_name} model...')
            urllib.request.urlretrieve(MODEL_URLS[model_name], model_path)
            print('Done.')

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=presence_threshold,
            min_tracking_confidence=0.5,
            num_poses=1
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def detect(self, frame):
        """Returns list of person dicts: {landmark_name: Landmark}"""
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect(mp_img)
        persons = []
        for person_lms in result.pose_landmarks:
            person = {}
            for i, name in enumerate(self.names):
                lm = person_lms[i]
                person[name] = Landmark(lm.x, lm.y, lm.z, lm.presence)
            persons.append(person)
        return persons

# ── YOLO BACKEND ──────────────────────────────────────────────────────────────
class YOLOBackend:
    def __init__(self, model_name, presence_threshold, max_persons):
        import torch
        from ultralytics import YOLO

        print(f'Loading YOLO model {model_name}.pt (auto-downloads if needed)...')
        self.model        = YOLO(f'{model_name}.pt')
        self.names        = COCO_LANDMARKS
        self.threshold    = presence_threshold
        self.max_persons  = max_persons
        device = 'GPU' if torch.cuda.is_available() else 'CPU'
        print(f'YOLO inference device: {device}')

    def detect(self, frame):
        """Returns list of person dicts: {landmark_name: Landmark}"""
        results = self.model(frame, verbose=False)
        persons = []
        kps = results[0].keypoints
        if kps is None or kps.xyn is None:
            return persons

        xyn  = kps.xyn.cpu().numpy()                                  # (n, 17, 2)
        conf = kps.conf.cpu().numpy() if kps.conf is not None else None  # (n, 17)
        n    = min(len(xyn), self.max_persons)

        for p in range(n):
            person = {}
            for i, name in enumerate(COCO_LANDMARKS):
                x = float(xyn[p, i, 0])
                y = float(xyn[p, i, 1])
                c = float(conf[p, i]) if conf is not None else 1.0
                person[name] = Landmark(x, y, 0.0, c)
            persons.append(person)
        return persons

# ── RTM BACKEND ──────────────────────────────────────────────────────────────

model_tiers_mediapipe2rtm = {
    'lite':  'lightweight',
    'full':  'balanced',
    'heavy': 'performance'
}

class RTMBackend:
    def __init__(self, model_name: str = "full", presence_threshold: float = 0.5, max_persons: int = 1):
        # only NOW import the rtmlib modules, after the DLLs are registered
        from rtmlib import Body, PoseTracker
        import numpy as np
        import onnxruntime as ort
        print(f'onnxruntime version: {ort.__version__}, available providers: {ort.get_available_providers()}')

        self.names = COCO_LANDMARKS
        self.threshold = presence_threshold
        self.max_persons = max_persons

        self.model = PoseTracker(
            Body,
            det_frequency=1,
            backend='onnxruntime',
            device='cuda' if ort.get_device() == 'GPU' else 'cpu',
            to_openpose=False,
            tracking=False,
            mode=model_tiers_mediapipe2rtm[model_name]
        )

        det_providers = self.model.det_model.session.get_providers()
        print(f'detection model providers: {det_providers}')

        pose_providers = self.model.pose_model.session.get_providers()
        print(f'pose model providers: {pose_providers}')

    def detect(self, frame):
        """Returns list of person dicts: {landmark_name: Landmark}"""

        keypoints, scores = None, None # keypoints is (n, 17, 2), scores is (n, 17)
        results = self.model(frame)
        if results is None:
            return []
        elif len(results) == 2:
            keypoints, scores = results
            if keypoints is None or len(keypoints) == 0:
                return []
        else:
            raise ValueError(f"Unexpected number of results: {len(results)}")

        n_detected = keypoints.shape[0]
        persons = []
        n = min(n_detected, self.max_persons)

        frame_height, frame_width = frame.shape[:2]

        for p in range(n):
            person = {}
            for i, name in enumerate(COCO_LANDMARKS):
                x = float(keypoints[p, i, 0]) / frame_width
                y = float(keypoints[p, i, 1]) / frame_height
                c = float(scores[p, i]) if scores is not None else 1.0
                person[name] = Landmark(x, y, 0.0, c)
            persons.append(person)
        return persons

# ── PER-PERSON EMA SMOOTHER ───────────────────────────────────────────────────
class Smoother:
    def __init__(self, alpha):
        self.alpha  = alpha
        self._state = {}   # (person_idx, name) -> [x, y, z]

    def update(self, person_idx, name, x, y, z):
        key = (person_idx, name)
        if key not in self._state:
            self._state[key] = [x, y, z]
        else:
            a, s = self.alpha, self._state[key]
            s[0] = a * x + (1 - a) * s[0]
            s[1] = a * y + (1 - a) * s[1]
            s[2] = a * z + (1 - a) * s[2]

    def get(self, person_idx, name):
        return self._state.get((person_idx, name), [0.0, 0.0, 0.0])

    def person_state(self, person_idx):
        """Dict of name -> [x,y,z] for one person (used for drawing)."""
        return {k[1]: v for k, v in self._state.items() if k[0] == person_idx}

    def clear_person(self, person_idx):
        for k in [k for k in self._state if k[0] == person_idx]:
            del self._state[k]

    def clear_all(self):
        self._state.clear()

# ── SETUP ─────────────────────────────────────────────────────────────────────
osc = udp_client.SimpleUDPClient(args.ip, args.port)

if args.backend == 'mediapipe':
    backend       = MediaPipeBackend(args.model, args.presence)
    backend_label = f'mediapipe-{args.model}'
elif args.backend == 'yolo':
    backend       = YOLOBackend(args.yolo_model, args.presence, args.max_persons)
    backend_label = args.yolo_model
elif args.backend == 'rtm':
    backend = RTMBackend(args.model, args.presence, args.max_persons)
    backend_label = 'rtm'
else:
    raise ValueError(f'Unknown backend: {args.backend}')

smoother      = Smoother(args.alpha)
prev_persons  = {}   # person_idx -> {name: Landmark}
prev_time     = None
frame_times   = []
last_summary  = time.perf_counter()
SUMMARY_SECS  = 3.0

cap = cv2.VideoCapture(args.camera)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS,          60)
cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)

print(f'\nBackend:     {backend_label}')
print(f'OSC target:  {args.ip}:{args.port}')
print(f'Alpha:       {args.alpha}')
print(f'Presence:    {args.presence}')
if args.backend == 'yolo':
    print(f'Max persons: {args.max_persons}')
    if args.max_persons == 1:
        print('             ↑ Use --max-persons 2 (or more) for multi-person tracking')
    print('             Note: persons tracked by detection confidence order,')
    print('             not persistent identity — /pose/... may switch performers')
print('Press q to quit\n')

# ── HELPERS ───────────────────────────────────────────────────────────────────
def is_reliable(lm):
    return lm.presence >= args.presence

def midpoint(a, b):
    return (a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2

def pose_similarity(p1, p2):
    """Returns a similarity score between two persons (dicts of landmarks)."""
    if not p1 or not p2:
        return 0.0
    total = 0.0
    count = 0
    for name in p1:
        if name in p2 and is_reliable(p1[name]) and is_reliable(p2[name]):
            dx = p1[name].x - p2[name].x
            dy = p1[name].y - p2[name].y
            dz = p1[name].z - p2[name].z
            dist_sq = dx*dx + dy*dy + dz*dz
            total += 1.0 / (dist_sq + 1e-6)  # inverse distance squared
            count += 1
    return total / count if count > 0 else 0.0

def osc_prefix(person_idx):
    """
    Person 0 → /pose        (backward compatible with previous patches)
    Person 1 → /pose/2
    Person 2 → /pose/3  etc.
    All persons also receive /pose/<N+1>/... explicitly.
    """
    return '/pose' if person_idx == 0 else f'/pose/{person_idx + 1}'

# ── OSC SENDING ───────────────────────────────────────────────────────────────
def send_person(person, person_idx, now, prev_p, prev_t):
    pre = osc_prefix(person_idx)

    # 1. Update landmark smoothers (once per landmark per frame)
    for name, lm in person.items():
        smoother.update(person_idx, name, lm.x, lm.y, lm.z)

    # 2. Compute velocities and update velocity smoothers
    velocities = {}
    if prev_p is not None and prev_t is not None:
        dt = now - prev_t
        if dt > 0:
            for name, lm in person.items():
                if name in prev_p and is_reliable(lm):
                    vx = (lm.x - prev_p[name].x) / dt
                    vy = (lm.y - prev_p[name].y) / dt
                    vz = (lm.z - prev_p[name].z) / dt
                    speed = (vx**2 + vy**2 + vz**2) ** 0.5
                    smoother.update(person_idx, f'vel_{name}', vx, vy, vz)
                    velocities[name] = (vx, vy, vz, speed)

    # 3. Individual landmarks — raw and smooth
    for name, lm in person.items():
        sx, sy, sz = smoother.get(person_idx, name)
        osc.send_message(f'{pre}/raw/{name}',
                         [lm.x, lm.y, lm.z, lm.presence])
        osc.send_message(f'{pre}/smooth/{name}',
                         [sx, sy, sz, lm.presence])

    # 4. Derived: wrists
    for side in ('left', 'right'):
        wname = f'{side}_wrist'
        if wname in person:
            w  = person[wname]
            sx, sy, sz = smoother.get(person_idx, wname)
            rel = 1 if is_reliable(w) else 0
            osc.send_message(f'{pre}/raw/wrist/{side}',
                             [w.x, w.y, w.z, w.presence, rel])
            osc.send_message(f'{pre}/smooth/wrist/{side}',
                             [sx, sy, sz, w.presence, rel])

    # 5. Derived: shoulders + tilt
    ls = person.get('left_shoulder')
    rs = person.get('right_shoulder')
    for side, s in (('left', ls), ('right', rs)):
        if s:
            sx, sy, sz = smoother.get(person_idx, f'{side}_shoulder')
            rel = 1 if is_reliable(s) else 0
            osc.send_message(f'{pre}/raw/shoulder/{side}',
                             [s.x, s.y, s.z, s.presence, rel])
            osc.send_message(f'{pre}/smooth/shoulder/{side}',
                             [sx, sy, sz, s.presence, rel])
    if ls and rs and is_reliable(ls) and is_reliable(rs):
        tilt = ls.y - rs.y
        smoother.update(person_idx, 'shoulder_tilt', tilt, 0, 0)
        stilt, _, _ = smoother.get(person_idx, 'shoulder_tilt')
        osc.send_message(f'{pre}/raw/shoulder/tilt',    float(tilt))
        osc.send_message(f'{pre}/smooth/shoulder/tilt', float(stilt))

    # 6. Derived: center (hip midpoint — full body needed)
    lh = person.get('left_hip')
    rh = person.get('right_hip')
    if lh and rh and is_reliable(lh) and is_reliable(rh):
        cx, cy, cz = midpoint(lh, rh)
        smoother.update(person_idx, 'center', cx, cy, cz)
        scx, scy, scz = smoother.get(person_idx, 'center')
        osc.send_message(f'{pre}/raw/center',    [cx,  cy,  cz])
        osc.send_message(f'{pre}/smooth/center', [scx, scy, scz])

    # center/upper (shoulder midpoint — upper body only)
    if ls and rs and is_reliable(ls) and is_reliable(rs):
        ux, uy, uz = midpoint(ls, rs)
        smoother.update(person_idx, 'center_upper', ux, uy, uz)
        sux, suy, suz = smoother.get(person_idx, 'center_upper')
        osc.send_message(f'{pre}/raw/center/upper',    [ux,  uy,  uz])
        osc.send_message(f'{pre}/smooth/center/upper', [sux, suy, suz])

    # 7. Derived: velocity
    for name, (vx, vy, vz, speed) in velocities.items():
        svx, svy, svz = smoother.get(person_idx, f'vel_{name}')
        sspeed = (svx**2 + svy**2 + svz**2) ** 0.5
        osc.send_message(f'{pre}/raw/velocity/{name}',
                         [vx, vy, vz, float(speed)])
        osc.send_message(f'{pre}/smooth/velocity/{name}',
                         [svx, svy, svz, float(sspeed)])

    osc.send_message(f'{pre}/status', 1)

# ── DRAWING ───────────────────────────────────────────────────────────────────
# Colors per person: person 0 = green/blue, person 1 = yellow/magenta
COLORS_RAW    = [(0, 255, 0),   (0, 200, 255)]
COLORS_SMOOTH = [(255, 100, 0), (255, 0, 200)]
COLOR_BAD     = (0, 0, 255)

def draw_person(frame, person, person_idx):
    h, w, _ = frame.shape
    c_raw    = COLORS_RAW[min(person_idx, len(COLORS_RAW) - 1)]
    c_smooth = COLORS_SMOOTH[min(person_idx, len(COLORS_SMOOTH) - 1)]

    for name, lm in person.items():
        px, py = int(lm.x * w), int(lm.y * h)
        color  = c_raw if is_reliable(lm) else COLOR_BAD
        cv2.circle(frame, (px, py), 4, color, -1)

    for name, vals in smoother.person_state(person_idx).items():
        if name.startswith('vel_') or name in ('center', 'center_upper', 'shoulder_tilt'):
            continue
        px, py = int(vals[0] * w), int(vals[1] * h)
        cv2.circle(frame, (px, py), 6, c_smooth, 2)

# ── SUMMARY ───────────────────────────────────────────────────────────────────
def print_summary(persons):
    print('\n── Tracking summary ─────────────────────────────────────────')
    for i, person in enumerate(persons):
        label    = f'Person {i+1}  (OSC: {"  /pose/..." if i == 0 else f"/pose/{i+1}/..."})'
        reliable = [n for n, lm in person.items() if is_reliable(lm)]
        bad      = [n for n, lm in person.items() if not is_reliable(lm)]
        print(f'\n  {label}')
        if reliable:
            print(f'  Reliable:   {", ".join(reliable)}')
        if bad:
            print(f'  Unreliable: {", ".join(bad)}')
    print()

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
# avoid hanging windows on Mac OS
if platform.system() == "Darwin" and not args.no_draw:
    cv2.startWindowThread()

try:
    while cap.isOpened():
        t0 = time.perf_counter()

        ret, frame = cap.read()
        if not ret:
            break

        now     = time.perf_counter()
        persons = backend.detect(frame)

        if persons:
            # if there are more than 1 person, sort them by similarity to the previous frame's persons
            if len(persons) > 1 and prev_persons:
                sorted_persons = []
                used_indices = set()
                for prev_idx, prev_p in prev_persons.items():
                    best_idx = None
                    best_score = -1.0
                    for i, p in enumerate(persons):
                        if i in used_indices:
                            continue
                        score = pose_similarity(prev_p, p)
                        if score > best_score:
                            best_score = score
                            best_idx = i
                    if best_idx is not None:
                        sorted_persons.append(persons[best_idx])
                        used_indices.add(best_idx)
                # Add any remaining persons that were not matched
                for i, p in enumerate(persons):
                    if i not in used_indices:
                        sorted_persons.append(p)
                persons = sorted_persons

            for i, person in enumerate(persons):
                send_person(person, i, now,
                            prev_persons.get(i), prev_time)
                if not args.no_draw:
                    draw_person(frame, person, i)

            # update state
            prev_persons = {i: p for i, p in enumerate(persons)}
            prev_time    = now

            # clear smoother state for persons no longer detected
            active = set(range(len(persons)))
            stale  = {k[0] for k in list(smoother._state)
                    if k[0] not in active}
            for p in stale:
                smoother.clear_person(p)

            # periodic summary
            if now - last_summary >= SUMMARY_SECS:
                print_summary(persons)
                last_summary = now

        else:
            osc.send_message('/pose/status', 0)
            prev_persons.clear()
            prev_time = None
            smoother.clear_all()

        # timing display
        t1 = time.perf_counter()
        frame_times.append(t1 - t0)
        if len(frame_times) > 30:
            avg = sum(frame_times[-30:]) / 30
            n   = len(persons) if persons else 0
            print(
                f'Avg: {avg*1000:.1f}ms | {backend_label} | '
                f'alpha={args.alpha} | persons={n} | '
                f'OSC->{args.ip}:{args.port}   ',
                end='\r'
            )

        if not args.no_draw:
            # mirror left-right
            frame = cv2.flip(frame, 1)
            cv2.imshow('Pose', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
except KeyboardInterrupt:
    print('\nKeyboard interrupt received. Exiting...')
finally:
    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # for Mac OS
