# OSC Reference — pose-osc

This document describes all OSC messages sent by `pose_osc.py`.

---

## Quick start

| Setting | Value |
|---|---|
| Protocol | UDP |
| Default port | `9000` |
| Default IP (same machine) | `127.0.0.1` |
| Default IP (two machines, Mac) | `192.168.1.2` (example) |
| Message rate | ~30 frames/second (camera dependent) |

> **Csound users — important:** `OSClisten` requires the type string and variable count
> to match the incoming message **exactly**. If the sender sends 5 floats and your
> `OSClisten` expects 4, the message is silently discarded with no error.
> Use the argument counts in this document carefully.

---

## Coordinate system

All position values are **normalised** to the camera frame:

| Axis | Range | Direction |
|---|---|---|
| x | 0.0 – 1.0 | 0 = left edge, 1 = right edge |
| y | 0.0 – 1.0 | 0 = top edge, 1 = bottom edge |
| z | negative – positive | negative = closer to camera, positive = further away (less reliable than x/y) |

Landmarks outside the camera frame may have x or y values slightly outside 0–1.

**Presence** is a confidence value (0.0 – 1.0) indicating how reliably a landmark
was detected. Values below the `--presence` threshold (default 0.5) indicate
the landmark is not visible or is estimated by the model rather than directly detected.
A fifth `reliable` argument (0 or 1) is included in some messages as a convenience flag.

---

## Raw vs smoothed

Every landmark is available in two variants:

- **`/pose/raw/...`** — direct model output, updated every frame. More responsive
  but may be jittery, especially at close range or for occluded landmarks.
- **`/pose/smooth/...`** — exponential moving average filtered values. Smoothness
  is controlled by the `--alpha` argument (default 0.2). Lower alpha = smoother
  but more lag; higher alpha = more responsive but more jitter.

For most sonification applications, start with the smoothed addresses.
Use raw addresses if you need maximum responsiveness for fast percussive gestures.

---

## OSC addresses

### Status

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/status` | 1 | `i` | `1` = person detected, `0` = no person in frame |

---

### Individual landmarks — raw and smoothed

Sends all 33 MediaPipe body landmarks individually by name.

| Address pattern | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/<name>` | 4 | `ffff` | x, y, z, presence |
| `/pose/smooth/<name>` | 4 | `ffff` | x, y, z, presence (smoothed) |

Replace `<name>` with any landmark name from the list below.

**All 33 landmark names:**

| Name | Body part |
|---|---|
| `nose` | Nose tip |
| `left_eye_inner` | Inner corner of left eye |
| `left_eye` | Centre of left eye |
| `left_eye_outer` | Outer corner of left eye |
| `right_eye_inner` | Inner corner of right eye |
| `right_eye` | Centre of right eye |
| `right_eye_outer` | Outer corner of right eye |
| `left_ear` | Left ear |
| `right_ear` | Right ear |
| `mouth_left` | Left corner of mouth |
| `mouth_right` | Right corner of mouth |
| `left_shoulder` | Left shoulder |
| `right_shoulder` | Right shoulder |
| `left_elbow` | Left elbow |
| `right_elbow` | Right elbow |
| `left_wrist` | Left wrist |
| `right_wrist` | Right wrist |
| `left_pinky` | Left pinky finger |
| `right_pinky` | Right pinky finger |
| `left_index` | Left index finger |
| `right_index` | Right index finger |
| `left_thumb` | Left thumb |
| `right_thumb` | Right thumb |
| `left_hip` | Left hip |
| `right_hip` | Right hip |
| `left_knee` | Left knee |
| `right_knee` | Right knee |
| `left_ankle` | Left ankle |
| `right_ankle` | Right ankle |
| `left_heel` | Left heel |
| `right_heel` | Right heel |
| `left_foot_index` | Left foot (front) |
| `right_foot_index` | Right foot (front) |

> Hip, knee, ankle and foot landmarks require the full body to be visible in frame.
> The landmark summary printed every 3 seconds in the terminal shows which landmarks
> are currently reliable given your camera placement.

**Examples:**
```
/pose/smooth/left_wrist     → x, y, z, presence
/pose/raw/nose              → x, y, z, presence
/pose/smooth/right_shoulder → x, y, z, presence
```

---

### Derived — wrists

Convenience addresses for the wrists, including a reliability flag.

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/wrist/left` | 5 | `fffff` | x, y, z, presence, reliable (0 or 1) |
| `/pose/smooth/wrist/left` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/wrist/right` | 5 | `fffff` | x, y, z, presence, reliable (0 or 1) |
| `/pose/smooth/wrist/right` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |

---

### Derived — shoulders

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/shoulder/left` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/shoulder/left` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/shoulder/right` | 5 | `fffff` | x, y, z, presence, reliable |
| `/pose/smooth/shoulder/right` | 5 | `fffff` | x, y, z, presence, reliable (smoothed) |
| `/pose/raw/shoulder/tilt` | 1 | `f` | left_y − right_y. Positive = tilted left, negative = tilted right |
| `/pose/smooth/shoulder/tilt` | 1 | `f` | shoulder tilt (smoothed) |

> Shoulder tilt is only sent when both shoulders are reliably detected.

---

### Derived — body center

Center of mass estimates. Requires hips or shoulders to be visible.

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/center` | 3 | `fff` | x, y, z — midpoint of left and right hip |
| `/pose/smooth/center` | 3 | `fff` | hip midpoint (smoothed) |
| `/pose/raw/center/upper` | 3 | `fff` | x, y, z — midpoint of left and right shoulder |
| `/pose/smooth/center/upper` | 3 | `fff` | shoulder midpoint (smoothed) |

> `/pose/center` requires both hips to be visible (full body in frame).
> `/pose/center/upper` requires both shoulders — works with upper body only.

---

### Derived — velocity

Frame-to-frame velocity for each landmark. Only sent for reliably detected landmarks.

| Address | Arguments | Types | Description |
|---|---|---|---|
| `/pose/raw/velocity/<name>` | 4 | `ffff` | vx, vy, vz, speed (normalised units/second) |
| `/pose/smooth/velocity/<name>` | 4 | `ffff` | vx, vy, vz, speed (smoothed) |

`speed` is the magnitude of the velocity vector: `sqrt(vx² + vy² + vz²)`.
Typical values: slow movement ~0.1–0.5, fast gesture ~2.0–6.0.
These values will need scaling to whatever range is useful in your patch.

**Examples:**
```
/pose/smooth/velocity/right_wrist  → vx, vy, vz, speed
/pose/raw/velocity/nose            → vx, vy, vz, speed
```

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

## Receiving OSC — quick examples

### Csound

```csound
giOSC OSCinit 9000

instr 1
    kx    init 0.5
    ky    init 0.5
    kz    init 0.0
    kpres init 0.0

    ; 4 floats — individual landmark
    kflag OSClisten giOSC, "/pose/smooth/right_wrist", "ffff", kx, ky, kz, kpres

    ; 5 floats — derived wrist address
    ; kreliable init 0.0
    ; kflag OSClisten giOSC, "/pose/smooth/wrist/right", "fffff", kx, ky, kz, kpres, kreliable

    ; 1 float — shoulder tilt
    ; ktilt init 0.0
    ; kflag OSClisten giOSC, "/pose/smooth/shoulder/tilt", "f", ktilt
endin
```

> The type string (`"ffff"`, `"fffff"`, etc.) must match the argument count exactly.
> Mismatches are silently ignored — no error is reported.

### Max/MSP

```
[udpreceive 9000]
        |
[route /pose/smooth/wrist/right]
        |
[unpack f f f f f]   ← 5 floats for wrist addresses
```

---

## Tips for sonification

- **Start with `/pose/smooth/wrist/right` y** — maps naturally to pitch or filter cutoff.
  Remember y is inverted: 0 = top of frame, 1 = bottom. Use `1 - y` for hand-up = high.
- **`/pose/smooth/shoulder/tilt`** maps well to stereo position or panning.
- **`/pose/smooth/center/upper` x** gives overall left-right body position.
- **`/pose/smooth/velocity/right_wrist` speed** maps well to amplitude or brightness —
  fast movement = loud/bright, stillness = silence.
- **`/pose/status`** is useful for muting instruments when no performer is detected.
- Always gate by the `presence` value — landmarks below 0.5 may jump unpredictably.
