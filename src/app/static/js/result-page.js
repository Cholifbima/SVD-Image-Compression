const debounceDelay=400;
let timer=null;
const slider = document.getElementById('kSlider');
const kLabel = document.getElementById('kVal');
const img=document.getElementById('compressedImg');
const statsDiv=document.getElementById('stats');
const dlBtn=document.getElementById('downloadBtn');
const origName = document.querySelector('[data-before-fname]')?.dataset.beforeFname || window.beforeFname || img.src.split('/preview/')[1].split('?')[0];

if (slider) {
    slider.oninput = () => {
        kLabel.textContent = slider.value;
        if (timer) clearTimeout(timer);
        timer = setTimeout(doRecompress, debounceDelay);
    };
};

function doRecompress(){
    const fd=new FormData();
    fd.append('fname', origName);
    fd.append('k', '{{ k }}');
    fetch('/recompress', {method:'POST', body:fd})
        .then(r=>r.json()).then(d=>{
        if(d.error){console.error(d.error);return;}
        img.src=d.url+'?'+Date.now();
        statsDiv.innerHTML=`<h4 class="font-bold mb-3">File Size Metrics</h4>
            <hr class="my-4">
            <p><strong>Image pixel size:</strong> ${d.dimension}</p>
            <p><strong>Original file size:</strong> ${d.before_kb} KB</p>
            <p><strong>Compressed file size:</strong> ${d.after_kb} KB</p>
            <p><strong>File compression ratio:</strong> ${d.ratio}%</p>
            
            <hr class="my-4">
            <p><strong>k value:</strong> ${d.k}</p>
            <p><strong>Runtime:</strong> ${d.runtime} seconds</p>`;
        dlBtn.href=d.url.replace('/preview/','/download/');
    });
}