const presetSel = document.getElementById('preset');
const kHidden = document.getElementById('kHidden');
const inputFile = document.getElementById('input-file');
const imgView = document.getElementById('img-view');
const previewContent = document.getElementById('preview-content');
const uploadedImage = document.getElementById('uploaded-image');
const dropArea = document.getElementById('drop-area');
const mapping = { low: 100, medium: 50, high: 30 };
presetSel.onchange = () => { kHidden.value = mapping[presetSel.value]; };
kHidden.value = mapping[presetSel.value];
inputFile.addEventListener("change", uploadImage);

function uploadImage() {
    if (inputFile.files && inputFile.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            previewContent.style.display = 'none';
            
            uploadedImage.src = e.target.result;
            uploadedImage.style.display = 'block';
            
            const img = new Image();
            img.onload = function() {
                if (img.width > img.height) { // Landscape
                    uploadedImage.style.width = '100%';
                    uploadedImage.style.height = 'auto';
                } else { // Portrait
                    uploadedImage.style.height = '100%';
                    uploadedImage.style.width = 'auto';
                }
            };
            img.src = e.target.result;
        }
        
        reader.readAsDataURL(inputFile.files[0]);
    }
}

dropArea.addEventListener("dragover", function(e) {
    e.preventDefault();
});

dropArea.addEventListener("drop", function(e) {
    e.preventDefault();
    inputFile.files = e.dataTransfer.files;
    uploadImage();
});