const compressionSlider = document.getElementById('compressionRate');
        const rateLabel = document.getElementById('rateValue');
        const kHidden = document.getElementById('kHidden');
        const inputFile = document.getElementById('input-file');
        const imgView = document.getElementById('img-view');
        const previewContent = document.getElementById('preview-content');
        const uploadedImage = document.getElementById('uploaded-image');
        const dropArea = document.getElementById('drop-area');

        // Update compression rate slider with smarter k calculation
        compressionSlider.oninput = () => {
            rateLabel.textContent = compressionSlider.value;
            
            // Simple linear inverse mapping: Higher compression rate = lower k
            const rate = parseInt(compressionSlider.value);
            
            // Linear scaling: 5% → k=100, 95% → k=1
            // Formula: k = 105 - rate (simple and predictable)
            let k = 105 - rate;
            
            // Clamp between 1-100 to be safe
            k = Math.max(1, Math.min(k, 100));
            kHidden.value = k;
            
            console.log(`Compression rate: ${rate}%, k value: ${k}`);
        };

        // Initialize with good compression (70% rate)
        const initialRate = 70; // Start with higher compression rate
        compressionSlider.value = initialRate;
        rateLabel.textContent = initialRate;
        
        // Calculate initial k using the same linear formula (70% = k=35)
        const initialK = 105 - initialRate; // 105 - 70 = 35
        kHidden.value = initialK;

        inputFile.addEventListener("change", uploadImage);

        function uploadImage() {
            if (inputFile.files && inputFile.files[0]) {
                // Reset preview state first
                uploadedImage.style.display = 'none';
                uploadedImage.src = '';
                previewContent.style.display = 'flex';
                
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // Hide initial preview content
                    previewContent.style.display = 'none';
                    
                    // Set image source and show
                    uploadedImage.src = e.target.result;
                    uploadedImage.style.display = 'block';
                    
                    // Handle image loading for proper sizing
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
                    
                    img.onerror = function() {
                        // Fallback if image fails to load
                        console.error('Failed to load image preview');
                        previewContent.style.display = 'flex';
                        uploadedImage.style.display = 'none';
                    };
                    
                    img.src = e.target.result;
                }
                
                reader.onerror = function() {
                    console.error('Failed to read file');
                    previewContent.style.display = 'flex';
                    uploadedImage.style.display = 'none';
                };
                
                reader.readAsDataURL(inputFile.files[0]);
            }
        }

        // Reset form when going back to home page
        function resetForm() {
            inputFile.value = '';
            uploadedImage.style.display = 'none';
            uploadedImage.src = '';
            previewContent.style.display = 'flex';
        }

        // Reset form on page load/visibility change
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                // Small delay to ensure proper reset
                setTimeout(resetForm, 100);
            }
        });

        dropArea.addEventListener("dragover", function(e) {
            e.preventDefault();
        });

        dropArea.addEventListener("drop", function(e) {
            e.preventDefault();
            inputFile.files = e.dataTransfer.files;
            uploadImage();
        });