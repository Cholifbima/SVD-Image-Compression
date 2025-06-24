const compressionSlider = document.getElementById('compressionRate');
        const rateLabel = document.getElementById('rateValue');
        const kHidden = document.getElementById('kHidden');
        const inputFile = document.getElementById('input-file');
        const imgView = document.getElementById('img-view');
        const previewContent = document.getElementById('preview-content');
        const uploadedImage = document.getElementById('uploaded-image');
        const dropArea = document.getElementById('drop-area');

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

        // Initialize values
        const initialRate = 50;
        compressionSlider.value = initialRate;
        rateLabel.textContent = initialRate;
        const initialK = Math.max(5, Math.round(200 * (100 - initialRate) / 100));
        kHidden.value = initialK;

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