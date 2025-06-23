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

    # More predictable quality based on visual information preserved
    ext = os.path.splitext(input_path)[1].lower()
    max_rank = min(height, width)
    
    # Calculate information preservation ratio
    info_preserved = k / max_rank
    
    print(f"DEBUG SVD: k={k}, max_rank={max_rank}, info_preserved={info_preserved:.3f}")
    
    if ext in ('.jpg', '.jpeg'):
        out_fname = f"svd_{int(time.time())}.jpg"
        
        # More aggressive quality reduction for low k (since visual info already lost)
        if info_preserved >= 0.8:      # k > 80% of max rank
            quality = 92  # High quality for minimal SVD loss
        elif info_preserved >= 0.5:    # k > 50% of max rank  
            quality = 85  # Medium-high quality
        elif info_preserved >= 0.2:    # k > 20% of max rank
            quality = 75  # Medium quality (SVD already removed detail)
        elif info_preserved >= 0.1:    # k > 10% of max rank
            quality = 65  # Low quality (heavy SVD compression)
        else:                          # k < 10% of max rank
            quality = 55  # Very low quality (extreme SVD compression)
            
        print(f"DEBUG JPEG: quality={quality}")
        save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True}
        # Ensure RGB for JPEG
        if out.mode != 'RGB':
            out = out.convert('RGB')
    else:
        out_fname = f"svd_{int(time.time())}.png" 
        # For PNG, use compression based on info preservation
        compress_level = min(9, max(1, int(9 - (info_preserved * 7))))
        save_kwargs = {'format': 'PNG', 'optimize': True, 'compress_level': compress_level}

    out_path = os.path.join(tmpdir, out_fname)
    out.save(out_path, **save_kwargs)

    runtime = time.time() - start

    before_size = os.path.getsize(input_path)
    after_size = os.path.getsize(out_path)

    return out_path, runtime, before_size, after_size, height, width 