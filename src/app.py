from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
import shutil
from PIL import Image

from svd import compress_image
from utils import allowed_file

# Configure upload folder (temporary directory)
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "svd_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'app', 'static'), template_folder=os.path.join(os.path.dirname(__file__), 'app', 'templates'))
app.secret_key = "CHANGE_ME_SECRET_KEY"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Limit uploads to 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


@app.route("/")
def index():
    """Render the main upload page."""
    return render_template("upload-page.html")


@app.route("/compress", methods=["POST"])
def compress():
    """Handle file upload and perform SVD compression."""
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

    # Simpan file upload ke folder sementara
    filename = secure_filename(file.filename)
    in_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(in_path)

    # Tentukan nilai k / preset setelah file tersimpan, agar PIL dapat membuka file
    preset = request.form.get('preset', 'low')
    k = int(request.form.get('k', 100))

    # Jalankan kompresi
    (out_path,
     runtime,
     before_size,
     after_size,
     height,
     width) = compress_image(in_path, k)

    # Pindahkan hasil kompresi ke folder upload agar dapat diakses melalui route preview/download
    after_basename = os.path.basename(out_path)
    dest_path = os.path.join(app.config["UPLOAD_FOLDER"], after_basename)
    try:
        shutil.move(out_path, dest_path)
    except Exception:
        # Jika sudah berada di lokasi yang sama atau gagal dipindah, abaikan
        dest_path = out_path

    ratio = (before_size - after_size) / before_size * 100
    ratio_str = f"{ratio:.2f}%" if ratio >=0 else f"+{abs(ratio):.2f}% (lebih besar)"

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
    )


@app.route("/download/<path:fname>")
def download(fname):
    """Serve compressed file for download."""
    path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
    if not os.path.exists(path):
        # File mungkin berada di tempdir yang berbeda jika menggunakan server produksi.
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
    if not fname or not k_val:
        return jsonify({'error': 'Parameter missing'}), 400
    try:
        k = int(k_val)
    except ValueError:
        return jsonify({'error': 'k must be int'}), 400

    orig_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
    if not os.path.exists(orig_path):
        return jsonify({'error': 'file not found'}), 404

    # Compress again
    out_path, runtime, before_size, after_size, height, width = compress_image(orig_path, k)
    # ensure file reachable via preview route
    dest_basename = os.path.basename(out_path)
    dest_path = os.path.join(app.config['UPLOAD_FOLDER'], dest_basename)
    try:
        shutil.move(out_path, dest_path)
    except Exception:
        dest_path = out_path

    ratio = (before_size - after_size) / before_size * 100

    return jsonify({
        'url': url_for('preview', fname=os.path.basename(dest_path)),
        'k': k,
        'runtime': f"{runtime:.3f}",
        'before_kb': f"{before_size/1024:.2f}",
        'after_kb': f"{after_size/1024:.2f}",
        'ratio': f"{ratio:.2f}",
        'dimension': f"{height}×{width}"
    })


if __name__ == "__main__":
    app.run(debug=True) 