import os
import sys
import urllib.request

URL = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
DEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minilm.onnx")
EXPECTED_MIN_BYTES = 85_000_000

for attempt in range(1, 4):
    try:
        print(f"downloading MiniLM ONNX ({attempt}/3)...")
        urllib.request.urlretrieve(URL, DEST)
        size = os.path.getsize(DEST)
        if size >= EXPECTED_MIN_BYTES:
            print(f"ok: minilm.onnx ({size} bytes)")
            break
        print(f"incomplete ({size} bytes), retrying")
    except Exception as e:
        print(f"attempt {attempt} failed: {e}")
else:
    sys.exit("model download failed after 3 attempts")
