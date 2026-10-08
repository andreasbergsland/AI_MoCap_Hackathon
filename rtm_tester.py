# %%
import os
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


# %%
from rtmlib import Body, Wholebody3d, PoseTracker, draw_skeleton
import cv2
import platform
import numpy as np
from pythonosc.udp_client import SimpleUDPClient

# %%
import onnxruntime as ort
print(f'onnxruntime version: {ort.__version__}, available providers: {ort.get_available_providers()}')

# %%
device = 'cuda'
backend = 'onnxruntime'
openpose_skeleton = False

pose_tracker = PoseTracker(
    Wholebody3d, 
    det_frequency=1, 
    backend=backend, 
    device=device,
    to_openpose=openpose_skeleton,
    tracking=False
)

# %%
det_providers = pose_tracker.det_model.session.get_providers()
print(f'detection model providers: {det_providers}')

pose_providers = pose_tracker.pose_model.session.get_providers()
print(f'pose model providers: {pose_providers}')

# %%
# osc setup
# Replace with the local IP address of your Max machine
TARGET_IP = "192.168.1.50" 
TARGET_IP = "127.0.0.1"  # For testing on the same machine
TARGET_PORT = 9000

client = SimpleUDPClient(TARGET_IP, TARGET_PORT)

def send_frame(keypoints_133x3: np.ndarray):
    """
    keypoints_133x3: shape (133, 3) float32/float64 array.
    """
    # 1. Body & Feet: indices 0 to 22 (23 points -> 69 floats)
    body_data = keypoints_133x3[0:23].flatten().tolist()
    client.send_message("/pose/body", body_data)

    # 2. Face: indices 23 to 90 (68 points -> 204 floats)
    face_data = keypoints_133x3[23:91].flatten().tolist()
    client.send_message("/pose/face", face_data)

    # 3. Hands: indices 91 to 132 (42 points -> 126 floats)
    hands_data = keypoints_133x3[91:133].flatten().tolist()
    client.send_message("/pose/hands", hands_data)

# %%
cap = cv2.VideoCapture(0)  # for video file instead of webcam, use cap = cv2.VideoCapture('./demo.mp4')

frame_idx = 0
try:
    # avoid hanging windows on Mac OS
    if platform.system() == "Darwin":
        cv2.startWindowThread()
    while cap.isOpened():
        success, frame = cap.read()
        frame_idx += 1
        if not success:
            break

        
        keypoints, scores, keypoints_simcc, keypoints_2d = None, None, None, None
        results = pose_tracker(frame)
        if results is None:
            # print(f"Frame {frame_idx}: No results returned.")
            continue  # Skip this frame if no results are returned
        else:
            if len(results) == 4:
                # print(f"Frame {frame_idx}: Received 4 results.")
                keypoints, scores, keypoints_simcc, keypoints_2d = results
            elif len(results) == 2:
                # print(f"Frame {frame_idx}: Received 2 results.")
                keypoints, scores = results
            else:
                print(f"Unexpected number of results: {len(results)}")
        # keypoints, scores = pose_tracker(frame)

        if keypoints is not None and len(keypoints) > 0:
            send_frame(keypoints[0])
            client.send_message("/pose/scores", scores[0].flatten().tolist())

        # img_show = frame.copy()
        # if keypoints_2d is not None:
        #     img_show = draw_skeleton(img_show,
        #                             keypoints_2d,
        #                             scores,
        #                             openpose_skeleton=openpose_skeleton,
        #                             kpt_thr=0.5)
        # cv2.imshow('img', img_show)
        # cv2.waitKey(10)
except KeyboardInterrupt:
    pass
finally:
    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # for Mac OS

# %%
print(f'keypoints shape: {keypoints.shape}, scores shape: {scores.shape}, keypoints_simcc shape: {keypoints_simcc.shape}, keypoints_2d shape: {keypoints_2d.shape}')


# %%
