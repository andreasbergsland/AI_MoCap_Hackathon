# OSC Reference — pose_osc.py

This document describes all OSC messages sent by `pose_osc.py`.

---

## Quick start

| Setting | Value |
|---|---|
| Protocol | UDP |
| Default port | `9000` |
| Default IP (same machine) | `127.0.0.1` |
| Default IP (two machines) | e.g. `192.168.1.2` |
| Message rate | ~30 fps (camera dependent) |

> **Csound users — critical:** `OSClisten` requires the type string and variable count
> to match the incoming message **exactly**. If the sender sends 5 floats and your
> `OSClisten` expects 4, the message is silently discarded with no error.
> Use the argument counts in this document carefully.

---

## Backends

The script supports two tracking backends, selectable via `--backend`:

| Backend | Command | Landmarks | Inference | Device |
|---|---|---|---|---|
| MediaPipe (default) | `--backend mediapipe` | 33 (full body + face + hand detail) | ~30ms | CPU |
| YOLO | `--backend yolo` | 17 (COCO skeleton) | ~5–20ms | GPU (NVIDIA) |

Both backends send OSC on the **same addresses** using the same format.
When using YOLO, the 16 MediaPipe-only landmarks (inner/outer eye detail, pinky, index,
thumb, heel, foot index) are simply absent from the stream — all other addresses work
identically. Patches built for one backend work with the other without modification,
as long as they don't rely on MediaPipe-only landmarks.

---

## Coordinate system

All position values are **normalised** to the camera frame:

| Axis | Range | Direction |
|---|---|---|
| x | 0.0 – 1.0 | 0 = left edge, 1 = right edge |
| y | 0.0 – 1.0 | 0 = top edge, 1 = bottom edge |
| z | negative – positive | negative = closer to camera (less reliable than x/y) |

**Presence** is a confidence value (0.0 – 1.0) indicating how reliably a landmark
was detected. Values below the `--presence` threshold (default 0.5) indicate the
landmark is not visible or is estimated by the model.
A `reliable` flag (0 or 1) is included in some messages as a convenience.

---

## Raw vs smoothed

Every landmark is available in two variants:

- **`/pose/raw/...`** — direct model output, updated every frame. More responsive
  but may be jittery, especially at close range or for occluded landmarks.
- **`/pose/smooth/...`** — exponential moving average (EMA) filtered values.
  Smoothness is controlled by `--alpha` (default 0.2).
  Lower alpha = smoother but more lag; higher alpha = more responsive but more jitter.

For most sonification applications, start with the smoothed addresses.

---

## Multi-person addressing

The script supports multiple simultaneous performers when using the YOLO backend
with `--max-persons N`. OSC addresses are prefixed per person:

| Person | OSC prefix | Example |
|---|---|---|
| Person 1 | `/pose` | `/pose/smooth/left_wrist` |
| Person 2 | `/pose/2` | `/pose/2/smooth/left_wrist` |
| Person 3 | `/pose/3` | `/pose/3/smooth/left_wrist` |

Person 1 uses `/pose` (no number) for backward compatibility with single-person patches.

> **Multi-person is off by default.** The `--max-persons` argument defaults to `1`.
> You must pass `--max-persons 2` (or higher) explicitly to enable multi-person tracking.
> The startup output will remind you if you forget:
> ```
> Max persons: 1
>              ↑ Use --max-persons 2 (or more) for multi-person tracking
> ```

> **No persistent identity.** YOLO detects persons in order of confidence score per frame,
> not by persistent identity. If a performer leaves and re-enters the frame, they may
> swap between `/pose/...` and `/pose/2/...`. Patches should not rely on a specific
> prefix always corresponding to the same physical performer across a full session.

---

## OSC addresses

### Status

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/status` | 1 | `i` | `1` = person detected, `0` = no person in frame |
| `/pose/2/status` | 1 | `i` | Status for person 2 (multi-person YOLO only) |

---

### Individual landmarks — raw and smoothed

| Address pattern | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/<name>` | 4 | `ffff` | x, y, z, presence |
| `/pose/smooth/<name>` | 4 | `ffff` | x, y, z, presence (smoothed) |

Replace `<name>` with any landmark name from the tables below.

#### All 17 COCO landmarks (both MediaPipe and YOLO)

| Name | Body part |
|---|---|
| `nose` | Nose tip |
| `left_eye` | Centre of left eye |
| `right_eye` | Centre of right eye |
| `left_ear` | Left ear |
| `right_ear` | Right ear |
| `left_shoulder` | Left shoulder |
| `right_shoulder` | Right shoulder |
| `left_elbow` | Left elbow |
| `right_elbow` | Right elbow |
| `left_wrist` | Left wrist |
| `right_wrist` | Right wrist |
| `left_hip` | Left hip |
| `right_hip` | Right hip |
| `left_knee` | Left knee |
| `right_knee` | Right knee |
| `left_ankle` | Left ankle |
| `right_ankle` | Right ankle |

#### Additional 16 landmarks — MediaPipe only (not available with YOLO)

| Name | Body part |
|---|---|
| `left_eye_inner` | Inner corner of left eye |
| `left_eye_outer` | Outer corner of left eye |
| `right_eye_inner` | Inner corner of right eye |
| `right_eye_outer` | Outer corner of right eye |
| `mouth_left` | Left corner of mouth |
| `mouth_right` | Right corner of mouth |
| `left_pinky` | Left pinky finger |
| `right_pinky` | Right pinky finger |
| `left_index` | Left index finger |
| `right_index` | Right index finger |
| `left_thumb` | Left thumb |
| `right_thumb` | Right thumb |
| `left_heel` | Left heel |
| `right_heel` | Right heel |
| `left_foot_index` | Left foot front |
| `right_foot_index` | Right foot front |

> Hip, knee, ankle and foot landmarks require the full body to be visible in frame.
> The landmark summary printed every 3 seconds in the terminal shows which landmarks
> are currently reliable given your camera placement.

---

### Derived — wrists

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/wrist/left` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/wrist/left` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/wrist/right` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/wrist/right` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |

---

### Derived — shoulders

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/shoulder/left` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/shoulder/left` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/shoulder/right` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/shoulder/right` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/shoulder/tilt` | 1 | `f` | left_y − right_y. Positive = tilted left, negative = right |
| `/pose/smooth/shoulder/tilt` | 1 | `f` | Shoulder tilt (smoothed) |

> Shoulder tilt is only sent when both shoulders are reliably detected.

---

### Derived — body center

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/center` | 3 | `fff` | x, y, z — midpoint of left and right hip |
| `/pose/smooth/center` | 3 | `fff` | Hip midpoint (smoothed) |
| `/pose/raw/center/upper` | 3 | `fff` | x, y, z — midpoint of left and right shoulder |
| `/pose/smooth/center/upper` | 3 | `fff` | Shoulder midpoint (smoothed) |

> `/pose/center` requires both hips visible (full body in frame).
> `/pose/center/upper` requires both shoulders — works with upper body only.

---

### Derived — velocity

Frame-to-frame velocity for each landmark. Only sent for reliably detected landmarks.

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/velocity/<name>` | 4 | `ffff` | vx, vy, vz, speed |
| `/pose/smooth/velocity/<name>` | 4 | `ffff` | vx, vy, vz, speed (smoothed) |

`speed` is the magnitude: `sqrt(vx² + vy² + vz²)`.
Typical values: slow movement ~0.1–0.5, fast gesture ~2.0–6.0.

---

## Summary table — argument counts at a glance

| Pattern | Count | Types |
|---|---|---|
| `/pose/status` | 1 | `i` |
| `/pose/raw/<name>` | 4 | `ffff` |
| `/pose/smooth/<name>` | 4 | `ffff` |
| `/pose/raw/wrist/<side>` | 5 | `fffff` |
| `/pose/smooth/wrist/<side>` | 5 | `fffff` |
| `/pose/raw/shoulder/<side>` | 5 | `fffff` |
| `/pose/smooth/shoulder/<side>` | 5 | `fffff` |
| `/pose/raw/shoulder/tilt` | 1 | `f` |
| `/pose/smooth/shoulder/tilt` | 1 | `f` |
| `/pose/raw/center` | 3 | `fff` |
| `/pose/smooth/center` | 3 | `fff` |
| `/pose/raw/center/upper` | 3 | `fff` |
| `/pose/smooth/center/upper` | 3 | `fff` |
| `/pose/raw/velocity/<name>` | 4 | `ffff` |
| `/pose/smooth/velocity/<name>` | 4 | `ffff` |

---

## Drawing

By default the scripts opens a separate window that visualizes the detected keypoints drawn onto the camera feed. However, to save resources, you can also disable drawing with the `--no_draw` flag.

## Receiving OSC — quick examples

### Csound

```csound
giOSC OSCinit 9000

instr 1
    ; 4 floats — individual landmark
    kx    init 0.5
    ky    init 0.5
    kz    init 0.0
    kpres init 0.0
    kflag OSClisten giOSC, "/pose/smooth/right_wrist", "ffff", kx, ky, kz, kpres

    ; 5 floats — derived wrist address (note the extra reliable argument)
    ; kreliable init 0.0
    ; kflag OSClisten giOSC, "/pose/smooth/wrist/right", "fffff", kx, ky, kz, kpres, kreliable

    ; 3 floats — center
    ; kcx init 0.5
    ; kcy init 0.5
    ; kcz init 0.0
    ; kflag OSClisten giOSC, "/pose/smooth/center/upper", "fff", kcx, kcy, kcz

    ; 1 float — shoulder tilt
    ; ktilt init 0.0
    ; kflag OSClisten giOSC, "/pose/smooth/shoulder/tilt", "f", ktilt

    ; 1 int — status
    ; kstat init 0
    ; kflag OSClisten giOSC, "/pose/status", "i", kstat
endin
```

### Max/MSP

```
[udpreceive 9000]
        |
[oscparse]
        |
[route /pose/smooth/wrist/right]
        |
[unpack f f f f f]   ← 5 floats for derived wrist addresses
```

### Pure Data

```
[netreceive -u 9000]
        |
[oscparse]
        |
[route /pose/smooth/right_wrist]
        |
[unpack f f f f]     ← 4 floats for individual landmark addresses
```

---

## Tips for sonification

- **Start with `/pose/smooth/wrist/right` y** — maps naturally to pitch or filter.
  y is 0 at the top of frame, 1 at the bottom. Use `1 - y` so hand up = high.
- **`/pose/smooth/shoulder/tilt`** maps well to stereo panning.
- **`/pose/smooth/center/upper` x** gives overall left–right body position.
- **`/pose/smooth/velocity/right_wrist` speed** maps well to amplitude or brightness —
  fast movement = loud/bright, stillness = quiet.
- **`/pose/status`** is useful for muting instruments when no performer is in frame.
- Always gate by `presence` — landmarks below 0.5 may jump unpredictably.
- Camera should be 2–4 metres from the performer for stable tracking.
