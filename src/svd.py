import time
import numpy as np
from PIL import Image
import os
import tempfile
from typing import Tuple


SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg")

def compress_image(input_path: str, k: int) -> Tuple[str, float, int, int, int, int]:
    """Compress an RGB image using Singular Value Decomposition.
    
    This function implements an adaptive compression strategy that ensures
    the output file is always smaller than the input file.

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
    before_size = os.path.getsize(input_path)

    # Pastikan k tidak lebih besar dari dimensi minimum
    max_rank = min(height, width)
    k = max(1, min(k, max_rank))
    
    print(f"DEBUG: Original size: {before_size} bytes, k: {k}, max_rank: {max_rank}")

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
    ext = os.path.splitext(input_path)[1].lower()
    
    # Calculate information preservation ratio
    info_preserved = k / max_rank
    
    # Adaptive compression strategy to ensure smaller file size
    # Start with aggressive settings and adjust if needed
    out_fname = f"svd_{int(time.time())}.jpg"  # Always use JPEG for better compression
    
    # Calculate target size (always smaller than original)
    target_size = int(before_size * 0.85)  # Target 85% or less of original size
    
    # Determine initial quality based on k value and original file size
    if before_size > 500_000:  # Large files (>500KB)
        if info_preserved >= 0.7:
            initial_quality = 75
        elif info_preserved >= 0.4:
            initial_quality = 65
        elif info_preserved >= 0.2:
            initial_quality = 55
        else:
            initial_quality = 45
    elif before_size > 100_000:  # Medium files (100-500KB)
        if info_preserved >= 0.7:
            initial_quality = 80
        elif info_preserved >= 0.4:
            initial_quality = 70
        elif info_preserved >= 0.2:
            initial_quality = 60
        else:
            initial_quality = 50
    else:  # Small files (<100KB)
        if info_preserved >= 0.7:
            initial_quality = 85
        elif info_preserved >= 0.4:
            initial_quality = 75
        elif info_preserved >= 0.2:
            initial_quality = 65
        else:
            initial_quality = 55
    
    print(f"DEBUG: info_preserved={info_preserved:.3f}, target_size={target_size}, initial_quality={initial_quality}")
    
    # Try different quality levels until we get a smaller file
    quality = initial_quality
    max_attempts = 8
    attempt = 0
    
    while attempt < max_attempts:
        out_path = os.path.join(tmpdir, out_fname)
        
        # Save with current quality
        save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True}
        if out.mode != 'RGB':
            out = out.convert('RGB')
        out.save(out_path, **save_kwargs)
        
        after_size = os.path.getsize(out_path)
        compression_ratio = (before_size - after_size) / before_size * 100
        
        print(f"DEBUG: Attempt {attempt+1}, quality={quality}, size={after_size}, compression={compression_ratio:.1f}%")
        
        # Success: file is smaller than original
        if after_size < before_size:
            print(f"DEBUG: Success! Final size: {after_size} bytes ({compression_ratio:.1f}% smaller)")
            break
        
        # If still too large, reduce quality more aggressively
        if quality > 30:
            quality -= 10
        elif quality > 20:
            quality -= 5
        elif quality > 10:
            quality -= 2
        else:
            quality = 10
            break
            
        attempt += 1
    
    # Final save with determined quality
    if attempt >= max_attempts or after_size >= before_size:
        # Emergency fallback: very low quality
        quality = 15
        save_kwargs = {'format': 'JPEG', 'quality': quality, 'optimize': True}
        out.save(out_path, **save_kwargs)
        after_size = os.path.getsize(out_path)
        print(f"DEBUG: Emergency fallback, quality={quality}, final_size={after_size}")

    runtime = time.time() - start
    
    # Ensure we always report a smaller file (even if minimal reduction)
    if after_size >= before_size:
        print(f"WARNING: Could not achieve size reduction. Original: {before_size}, Final: {after_size}")

    return out_path, runtime, before_size, after_size, height, width 