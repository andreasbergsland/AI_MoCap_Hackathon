import onnxruntime as ort
import glob
import os

# Locate one of the downloaded models in your rtmlib cache
cache_dir = os.path.expanduser("~/.cache/rtmlib/hub/checkpoints")
models = glob.glob(os.path.join(cache_dir, "*.onnx"))

if not models:
    print("No models found in cache. Please provide a direct path to an .onnx file.")
else:
    print(f"Testing CUDA initialization with: {models[0]}")
    try:
        # Passing ONLY CUDA forces an exception if the GPU fails to load
        session = ort.InferenceSession(models[0], providers=['CUDAExecutionProvider'])
        print("Success! CUDA is fully initialized.")
    except Exception as e:
        print("\n--- CUDA INITIALIZATION ERROR ---")
        print(e)