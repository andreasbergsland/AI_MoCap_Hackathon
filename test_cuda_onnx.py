import sys
import numpy as np
import onnxruntime as ort

def test_model_on_cuda(model_path: str):
    print(f"Testing model: {model_path}")
    print(f"Available ONNX providers on system: {ort.get_available_providers()}\n")

    # 1. Force CUDAExecutionProvider ONLY (omitting CPUExecutionProvider prevents silent fallback)
    try:
        session = ort.InferenceSession(
            model_path,
            providers=['CUDAExecutionProvider']
        )
    except Exception as e:
        print("FAIL: Failed to create session on CUDAExecutionProvider.")
        print("Error details:")
        print(e)
        return False

    # 2. Check active providers assigned by the runtime
    active_providers = session.get_providers()
    print(f"Active providers for session: {active_providers}")
    if 'CUDAExecutionProvider' not in active_providers:
        print("FAIL: CUDAExecutionProvider was not assigned.")
        return False

    # 3. Inspect expected inputs and build dummy tensor
    inputs = session.get_inputs()
    input_feed = {}
    print("\nModel input requirements:")
    for inp in inputs:
        print(f" - Name: '{inp.name}', Type: {inp.type}, Shape: {inp.shape}")
        
        # Resolve dynamic or negative dimensions to a default size (1 or 256)
        resolved_shape = [
            dim if isinstance(dim, int) and dim > 0 else (1 if idx == 0 else 256)
            for idx, dim in enumerate(inp.shape)
        ]
        
        # Determine numpy data type
        dtype = np.float32
        if "float16" in inp.type:
            dtype = np.float16
        elif "int64" in inp.type:
            dtype = np.int64
        elif "int32" in inp.type:
            dtype = np.int32

        input_feed[inp.name] = np.zeros(resolved_shape, dtype=dtype)

    # 4. Execute a dummy inference pass on the GPU
    try:
        print(f"\nRunning test inference pass with dummy input shape: {[v.shape for v in input_feed.values()]}...")
        outputs = session.run(None, input_feed)
        print("SUCCESS: Inference pass completed on GPU without errors.")
        print(f"Output count: {len(outputs)}, Output 0 shape: {outputs[0].shape}")
        return True
    except Exception as e:
        print("FAIL: Session initialized, but inference pass failed on GPU.")
        print("Error details:")
        print(e)
        return False


if __name__ == "__main__":
    # Replace with the direct path to the .onnx file you want to test
    # e.g., "C:/Users/<Username>/.cache/rtmlib/hub/checkpoints/rtmpose-m_simcc-body7_pt-body7_420e-384x288-0f04c622_20230504.onnx"
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("Enter full path to .onnx model: ").strip().strip('"').strip("'")

    test_model_on_cuda(target_path)