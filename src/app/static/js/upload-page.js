const presetSel = document.getElementById('preset');
const kHidden = document.getElementById('kHidden');
const compressionSlider = document.getElementById('compressionRate');
const rateLabel = document.getElementById('rateValue');
const inputFile = document.getElementById('input-file');
const imgView = document.getElementById('img-view');
const previewContent = document.getElementById('preview-content');
const uploadedImage = document.getElementById('uploaded-image');
const dropArea = document.getElementById('drop-area');
const mapping = { low: 100, medium: 50, high: 30 };

// Update compression rate slider
compressionSlider.oninput = () => {
    rateLabel.textContent = compressionSlider.value;
    // Convert compression rate % to k value (inverse relationship)
    // Higher compression rate = lower k
    const rate = parseInt(compressionSlider.value);
    const maxK = 200; // reasonable max for most images
    const k = Math.max(5, Math.round(maxK * (100 - rate) / 100));
    kHidden.value = k;
};

// Update preset selector
presetSel.onchange = () => { 
    const k = mapping[presetSel.value];
    kHidden.value = k;
    // Update slider to match preset
    const rate = Math.round(100 - (k / 200 * 100));
    compressionSlider.value = Math.max(5, Math.min(95, rate));
    rateLabel.textContent = compressionSlider.value;
};

// Initialize values
kHidden.value = mapping[presetSel.value];
const initialRate = Math.round(100 - (mapping[presetSel.value] / 200 * 100));
compressionSlider.value = Math.max(5, Math.min(95, initialRate));
rateLabel.textContent = compressionSlider.value;

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