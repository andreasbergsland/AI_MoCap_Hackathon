# MotionComposer MC-5 — OSC Reference

This document describes the OSC messages sent by Robert Wechsler's **MotionComposer MC-5**,
a prototype YOLO + segmentation-based motion tracking device brought to the hackathon.

The MC-5 is a separate system from the NTNU `pose_osc.py` pipeline. It runs on its own
machine and sends its own OSC stream. This system will be used by one of the groups at the hackathon.

---

## Network

| Setting | Value |
|---|---|
| Protocol | UDP |
| IP address | `192.168.2.220` |
| Port | `6160` or `6162` |

---

## Conceptual background — Gesture and Flow

Robert's system is built around a distinction between two modes of interaction:

**Flow** — continuous data that changes smoothly over time. The mover enters an intuitive,
ongoing relationship with the sound. Map to continuously varying sound parameters —
filter cutoff, reverb size, amplitude, pitch.

**Gesture** — discrete, triggered events. A specific action produces a specific sound at a
specific moment: cause-and-effect. Map to note triggers, transient sounds, or sudden
parameter changes.

These are not just different data types — they embody different psychological experiences.
See Robert's paper *An Introduction to Mapping Movement to Music* (distributed at the hackathon)
for the full discussion.

---

## OSC addresses

### Presence

| Address | Value | Type | Description |
|---|---|---|---|
| `/player/1/present` | 0 or 1 | `i` | One or more persons with visible hips have been found. Only the first person is tracked — others are ignored. |

Always check this before using other values — use it to mute your patch when no one is present.

---

### Position and shape — Flow

| Address | Range | Type | Description | Paradigm |
|---|---|---|---|---|
| `/player/1/centerX` | 0.0 – 1.0 | `f` | Position left–right in the room. 0 = left, 1 = right | Flow |
| `/player/1/heightRatio` | 0.0 – 1.0 | `f` | Ratio of skeleton height to width. Useful for detecting crouching or bending low — value decreases as the person goes lower | Flow |

---

### Gestures — discrete triggers

| Address | Value | Type | Description | Paradigm |
|---|---|---|---|---|
| `/player/1/hit/overhead` | 1 | `i` | Any quick upward movement of either hand above the head | Gesture |
| `/player/1/jump` | 1 | `i` | A jump, or the body moving upward quickly | Gesture |
| `/player/1/handsUp` | 0 or 1 | `i` | A hand is raised above the head *(possible — confirm with Robert on the day)* | Gesture |

---

### Activity — Flow

Five activity streams derived from different parts of the body and different tracking methods.

> **Note from Robert:** Activity data has been jumpy and is currently work in progress.
> These streams are included but come with no guarantee of stability for the hackathon.
> If they are behaving erratically, use `centerX`, `heightRatio`, or the gesture triggers instead.

| Address | Range | Type | Description | Method |
|---|---|---|---|---|
| `/player/1/activitySkeleton` | 0.0 – 1.0 | `f` | Amount of movement across all skeleton points added together | YOLO skeleton |
| `/player/1/activitySkeletonTorso` | 0.0 – 1.0 | `f` | As above, but ignoring arms and legs — torso movement only | YOLO skeleton |
| `/player/1/activityBlob` | 0.0 – 1.0 | `f` | Movement in a zone around the whole skeleton — background subtraction (not YOLO) | Segmentation |
| `/player/1/activityBlobHands` | 0.0 – 1.0 | `f` | Movement in a zone around the hands — captures finger movement | Segmentation |
| `/player/1/activityBlobHead` | 0.0 – 1.0 | `f` | Movement in a zone around the head — captures lip, eye and facial movement | Segmentation |

The blob-based streams use background subtraction within a defined region around the
body part, making them sensitive to small movements (fingers, lips) that skeleton tracking
alone would miss.

---

## Argument counts for Csound

As with any OSC in Csound, the type string in `OSClisten` must match the message exactly.
Mismatches are silently discarded with no error.

| Address | Type string |
|---|---|
| `/player/1/present` | `"i"` |
| `/player/1/centerX` | `"f"` |
| `/player/1/heightRatio` | `"f"` |
| `/player/1/hit/overhead` | `"i"` |
| `/player/1/hit/jump` | `"i"` |
| `/player/1/handUp` | `"i"` |
| `/player/1/activitySkeleton` | `"f"` |
| `/player/1/activityTorso` | `"f"` |
| `/player/1/activityBlob` | `"f"` |
| `/player/1/activityBlobHands` | `"f"` |
| `/player/1/activityBlobHead` | `"f"` |

**Verify these with Robert on the day** — the MC-5 is a prototype and details may change.

---

## Csound example

```csound
giOSC OSCinit 61   ; MC-5 port

instr 1
    ; presence gate
    kpresent init 0
    kf1 OSClisten giOSC, "/player/1/present", "i", kpresent

    ; horizontal position → panning
    kcx  init 0.5
    kf2 OSClisten giOSC, "/player/1/centerX", "f", kcx

    ; overall activity → amplitude
    kact init 0.0
    kf3 OSClisten giOSC, "/player/1/activitySkeleton", "f", kact

    ; overhead hit → trigger
    khit init 0
    kf4 OSClisten giOSC, "/player/1/hit/overhead", "i", khit
    if khit == 1 then
        event "i", 2, 0, 0.3   ; trigger a note instrument
    endif

    kamp = kact * 0.3 * kpresent
    asig oscili kamp, 220
    aL, aR pan2 asig, kcx
    outs aL, aR
endin
```

---


---

## Comparison with NTNU pose_osc.py

| Feature | MC-5 (Robert) | pose_osc.py (NTNU) |
|---|---|---|
| Tracking | YOLO + segmentation | MediaPipe or YOLO |
| Data style | Pre-computed high-level features | Raw landmarks + derived values |
| Joint positions | No individual joint x/y | 17–33 named body landmarks |
| Activity | 5 region-based streams | Velocity per landmark |
| Gestures | Overhead hit, jump, handUp | Not implemented |
| Smoothing | Built into device | Configurable via --alpha |
| Multi-person | Single person only (first detected) | Up to N persons via --max-persons |
| IP / Port | 192.168.2.207 / 61 | Configurable, default 127.0.0.1:9000 |

The MC-5 gives you high-level, pre-designed features ready to map directly to sound —
closer to the original MotionComposer philosophy. The NTNU pipeline gives raw skeleton
access for participants who want to design their own features from scratch. Both are
valid starting points and can be used simultaneously.
