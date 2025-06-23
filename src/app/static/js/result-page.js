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
    fetch("{{ url_for('recompress') }}", {method:'POST', body:fd})
        .then(r=>r.json()).then(d=>{
        if(d.error){console.error(d.error);return;}
        img.src=d.url+'?'+Date.now();
        statsDiv.innerHTML=`<p><strong>Ukuran sebelum:</strong> ${d.before_kb} KB</p>
            <p><strong>Ukuran sesudah:</strong> ${d.after_kb} KB</p>
            <p><strong>Rasio kompresi:</strong> ${d.ratio}%</p>
            <p><strong>Dimensi:</strong> ${d.dimension}</p>
            <p><strong>Nilai k:</strong> ${d.k}</p>
            <p><strong>Runtime:</strong> ${d.runtime} detik</p>`;
        dlBtn.href=d.url.replace('/preview/','/download/');
    });
}