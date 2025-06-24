const debounceDelay=400;
let timer=null;
const slider=document.getElementById('kSlider');
const kLabel=document.getElementById('kVal');
const img=document.getElementById('compressedImg');
const statsDiv=document.getElementById('stats');
const dlBtn=document.getElementById('downloadBtn');
const origName='{{ before_fname }}';

slider.oninput=()=>{
    kLabel.textContent=slider.value;
    if(timer) clearTimeout(timer);
    timer=setTimeout(doRecompress, debounceDelay);
};

function doRecompress(){
    const fd=new FormData();
    fd.append('fname', origName);
    fd.append('k', slider.value);
    fetch('/recompress', {method:'POST', body:fd})
        .then(r=>r.json()).then(d=>{
        if(d.error){console.error(d.error);return;}
        img.src=d.url+'?'+Date.now();
        statsDiv.innerHTML=`<h4 class="font-bold text-lg mb-3">SVD Mathematical Metrics</h4>
            <p><strong>Image size:</strong> ${d.dimension}</p>
            <p><strong>Pixels:</strong> ${d.total_pixels}</p>
            <p><strong>Uncompressed matrix size:</strong> ${d.uncompressed_matrix_size} (proportional to pixels)</p>
            <p><strong>Compressed matrix size:</strong> ${d.compressed_matrix_size} (${d.height}×${d.k} + ${d.k} + ${d.k}×${d.width}) × 3</p>
            <p><strong>SVD compression ratio:</strong> ${d.svd_compression_ratio}</p>
            
            <hr class="my-4">
            <h4 class="font-bold text-lg mb-3">File Size Metrics (Secondary)</h4>
            <p><strong>Ukuran sebelum:</strong> ${d.before_kb} KB</p>
            <p><strong>Ukuran sesudah:</strong> ${d.after_kb} KB</p>
            <p><strong>Rasio kompresi file:</strong> ${d.ratio}%</p>
            <p><strong>Info preserved:</strong> <span id="infoPreserved">${d.info_preserved}%</span></p>
            
            <hr class="my-4">
            <div class="bg-blue-50 p-3 rounded text-sm">
                <p class="font-semibold text-blue-800">💡 Catatan Penting:</p>
                <p class="text-blue-700">SVD compression ratio menunjukkan kompresi matematis matriks. File size disesuaikan dengan info yang tersisa (k rendah = kualitas JPEG lebih rendah karena detail sudah hilang dari SVD).</p>
            </div>
            
            <hr class="my-4">
            <p><strong>Nilai k:</strong> ${d.k}</p>
            <p><strong>Runtime:</strong> ${d.runtime} detik</p>`;
        dlBtn.href=d.url.replace('/preview/','/download/');
    });
}