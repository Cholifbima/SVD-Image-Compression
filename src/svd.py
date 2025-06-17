import time
import numpy as np
from PIL import Image
import os
import tempfile
from typing import Tuple


SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg")

def compress_image(input_path: str, k: int) -> Tuple[str, float, int, int, int, int]:
    """Compress an RGB image using Singular Value Decomposition.

    Args:
        input_path: Full path to input image file.
        k: Number of singular values to keep (per channel).

    Returns:
        out_path: Path where compressed image is stored.
        runtime: Compression runtime in seconds.
        before_size: Original file size in bytes.
        after_size: Compressed file size in bytes.
        height: Image height (pixels).
        width: Image width (pixels).
    """
    start = time.time()

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"{input_path} tidak ditemukan.")

    img = Image.open(input_path).convert("RGB")
    arr = np.asarray(img, dtype=np.float32)
    height, width, _ = arr.shape

    # Pastikan k tidak lebih besar dari dimensi minimum
    k = max(1, min(k, min(height, width)))

    out_channels = []
    for ch in range(3):
        # U: (m, m); S: (m, n); Vt: (n, n) untuk full_matrices=True
        U, S, Vt = np.linalg.svd(arr[:, :, ch], full_matrices=False)
        S[k:] = 0  # buang singular value kecil
        recon = np.matmul(U, np.matmul(np.diag(S), Vt))
        out_channels.append(recon)

    recon_img = np.dstack(out_channels).clip(0, 255).astype(np.uint8)
    out = Image.fromarray(recon_img)

    # Simpan ke direktori temp agar mudah dihapus nanti
    tmpdir = tempfile.gettempdir()

    # Determine output format based on input extension
    ext = os.path.splitext(input_path)[1].lower()
    save_kwargs = {}
    if ext in ('.jpg', '.jpeg'):
        out_fname = f"svd_{int(time.time())}.jpg"
        save_kwargs = {'quality': 85, 'optimize': True}
    else:
        out_fname = f"svd_{int(time.time())}.png"
        save_kwargs = {'optimize': True, 'compress_level': 9}

    out_path = os.path.join(tmpdir, out_fname)
    out.save(out_path, **save_kwargs)

    runtime = time.time() - start

    before_size = os.path.getsize(input_path)
    after_size = os.path.getsize(out_path)

    return out_path, runtime, before_size, after_size, height, width 