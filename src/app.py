from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from PIL import Image

from svd import compress_image
from utils import allowed_file, get_file_hash, load_cache, save_cache, cleanup_old_files

UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "svd_uploads")
CACHE_FOLDER = os.path.join(tempfile.gettempdir(), "svd_cache")
CACHE_FILE = os.path.join(CACHE_FOLDER, "cache.json")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'app', 'static'), template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'))
app.secret_key = "CHANGE_ME_SECRET_KEY"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CACHE_FOLDER"] = CACHE_FOLDER
app.config["CACHE_FILE"] = CACHE_FILE
# Limit uploads to 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

cleanup_old_files(UPLOAD_FOLDER, max_age_hours=24)
cleanup_old_files(CACHE_FOLDER, max_age_hours=48)


@app.route("/")
def index():
    """Render the main upload page."""
    return render_template("upload-page.html")


@app.route("/compress", methods=["POST"])
def compress():
    """Handle file upload and perform SVD compression with caching."""
    if "image" not in request.files:
        flash("Tidak ada file yang di-upload.")
        return redirect(url_for("index"))

    file = request.files["image"]
    if file.filename == "":
        flash("Silakan pilih file gambar.")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Tipe file tidak didukung. Hanya JPG, JPEG, PNG yang diperbolehkan.")
        return redirect(url_for("index"))

    filename = secure_filename(file.filename)
    in_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(in_path)

    preset = request.form.get('preset', 'low')
    k = int(request.form.get('k', 100))

    file_hash = get_file_hash(in_path)
    cache_key = f"{file_hash}_{k}"
    
    cache_data = load_cache(app.config["CACHE_FILE"])
    
    if cache_key in cache_data:
        print(f"Cache hit for {cache_key}")
        cached_result = cache_data[cache_key]
        
        cached_file_path = os.path.join(app.config["CACHE_FOLDER"], cached_result["output_filename"])
        if os.path.exists(cached_file_path):
            dest_path = os.path.join(app.config["UPLOAD_FOLDER"], cached_result["output_filename"])
            shutil.copy2(cached_file_path, dest_path)
            
            return render_template(
                "result.html",
                before_fname=os.path.basename(in_path),
                after_fname=cached_result["output_filename"],
                runtime=f"{cached_result['runtime']:.3f} (cached)",
                ratio=cached_result["ratio_str"],
                dimension=cached_result["dimension"],
                before_size_kb=cached_result["before_size_kb"],
                after_size_kb=cached_result["after_size_kb"],
                k=k,
                preset=preset if preset else 'custom',
            )

    print(f"Cache miss for {cache_key} - performing compression")
    (out_path, runtime, before_size, after_size, height, width) = compress_image(in_path, k)

    after_basename = os.path.basename(out_path)
    cache_file_path = os.path.join(app.config["CACHE_FOLDER"], after_basename)
    shutil.copy2(out_path, cache_file_path)
    
    dest_path = os.path.join(app.config["UPLOAD_FOLDER"], after_basename)
    try:
        shutil.move(out_path, dest_path)
    except Exception:
        dest_path = out_path

    ratio = (before_size - after_size) / before_size * 100
    ratio_str = f"{ratio:.2f}%" if ratio >=0 else f"+{abs(ratio):.2f}% (lebih besar)"

    # Calculate mathematical SVD compression metrics
    total_pixels = height * width
    uncompressed_matrix_size = total_pixels * 3  # RGB channels
    compressed_matrix_size = (height * k + k + k * width) * 3  # U + S + Vt per channel
    svd_compression_ratio = uncompressed_matrix_size / compressed_matrix_size

    print(f"DEBUG Math: h={height}, w={width}, k={k}")
    print(f"DEBUG Math: uncompressed={uncompressed_matrix_size}, compressed={compressed_matrix_size}")
    print(f"DEBUG Math: SVD ratio={svd_compression_ratio:.2f}")
    print(f"DEBUG File: before={before_size}, after={after_size}, ratio={(before_size-after_size)/before_size*100:.2f}%")

    cache_entry = {
        "output_filename": after_basename,
        "runtime": runtime,
        "ratio_str": ratio_str,
        "dimension": f"{height}×{width}",
        "before_size_kb": f"{before_size / 1024:.2f}",
        "after_size_kb": f"{after_size / 1024:.2f}",
        "timestamp": time.time()
    }
    
    cache_data[cache_key] = cache_entry
    save_cache(app.config["CACHE_FILE"], cache_data)

    return render_template(
        "result.html",
        before_fname=os.path.basename(in_path),
        after_fname=os.path.basename(dest_path),
        runtime=f"{runtime:.3f}",
        ratio=ratio_str,
        dimension=f"{height}×{width}",
        before_size_kb=f"{before_size / 1024:.2f}",
        after_size_kb=f"{after_size / 1024:.2f}",
        k=k,
        preset=preset if preset else 'custom',
        # SVD mathematical metrics
        total_pixels=total_pixels,
        uncompressed_matrix_size=uncompressed_matrix_size,
        compressed_matrix_size=compressed_matrix_size,
        svd_compression_ratio=f"{svd_compression_ratio:.2f}",
        height=height,
        width=width,
        info_preserved=f"{(k/min(height,width))*100:.1f}",
    )


@app.route("/download/<path:fname>")
def download(fname):
    """Serve compressed file for download."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


@app.route("/preview/<path:fname>")
def preview(fname):
    """Serve file inline for preview in browser."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=False)


@app.route('/recompress', methods=['POST'])
def recompress():
    """Ajax endpoint to recompress original image with a new k value."""
    fname = request.form.get('fname')  # original uploaded filename
    k_val = request.form.get('k')
    
    print(f"DEBUG: Recompress called with fname={fname}, k={k_val}")  # Debug log
    
    if not fname or not k_val:
        return jsonify({'error': 'Parameter missing'}), 400
    try:
        k = int(k_val)
    except ValueError:
        return jsonify({'error': 'k must be int'}), 400

    orig_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    if not os.path.exists(orig_path):
        return jsonify({'error': 'file not found'}), 404

    try:
        # Compress again - FORCE no cache
        out_path, runtime, before_size, after_size, height, width = compress_image(orig_path, k)
        
        print(f"DEBUG: SVD result - before:{before_size}, after:{after_size}, h:{height}, w:{width}")  # Debug log
        
        # ensure file reachable via preview route
        dest_basename = os.path.basename(out_path)
        dest_path = os.path.join(app.config['UPLOAD_FOLDER'], dest_basename)
        try:
            shutil.move(out_path, dest_path)
        except Exception as e:
            print(f"DEBUG: Move failed: {e}")
            dest_path = out_path

        ratio = (before_size - after_size) / before_size * 100

        # Calculate mathematical SVD compression metrics
        total_pixels = height * width
        uncompressed_matrix_size = total_pixels * 3  # RGB channels
        compressed_matrix_size = (height * k + k + k * width) * 3  # U + S + Vt per channel
        svd_compression_ratio = uncompressed_matrix_size / compressed_matrix_size

        print(f"DEBUG: Math metrics - pixels:{total_pixels}, ratio:{svd_compression_ratio}")  # Debug log

        return jsonify({
            'url': url_for('preview', fname=os.path.basename(dest_path)),
            'k': k,
            'runtime': f"{runtime:.3f}",
            'before_kb': f"{before_size/1024:.2f}",
            'after_kb': f"{after_size/1024:.2f}",
            'ratio': f"{ratio:.2f}",
            'dimension': f"{height}×{width}",
            # SVD mathematical metrics
            'total_pixels': total_pixels,
            'uncompressed_matrix_size': uncompressed_matrix_size,
            'compressed_matrix_size': compressed_matrix_size,
            'svd_compression_ratio': f"{svd_compression_ratio:.2f}",
            'height': height,
            'width': width,
            'info_preserved': f"{(k/min(height,width))*100:.1f}"
        })
        
    except Exception as e:
        print(f"ERROR in recompress: {e}")  # Error log
        return jsonify({'error': f'Compression failed: {str(e)}'}), 500


@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached files and data."""
    try:
        # Clear cache folder
        if os.path.exists(app.config["CACHE_FOLDER"]):
            shutil.rmtree(app.config["CACHE_FOLDER"])
            os.makedirs(app.config["CACHE_FOLDER"], exist_ok=True)
        
        return jsonify({'success': True, 'message': 'Cache cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/cache/stats')
def cache_stats():
    """Get cache statistics."""
    cache_data = load_cache(app.config["CACHE_FILE"])
    total_entries = len(cache_data)
    
    cache_size = 0
    if os.path.exists(app.config["CACHE_FOLDER"]):
        for dirpath, dirnames, filenames in os.walk(app.config["CACHE_FOLDER"]):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                cache_size += os.path.getsize(filepath)
    
    return jsonify({
        'total_entries': total_entries,
        'cache_size_mb': f"{cache_size / (1024*1024):.2f}",
        'cache_folder': app.config["CACHE_FOLDER"]
    })


if __name__ == "__main__":
    import time
    app.run(debug=True)