const photoInput = document.querySelector(
    '.vehicle-form input[type="file"][name="photo"]'
);

const photoPreview = document.getElementById('photo-preview');

let previewUrl = null;

if (photoInput && photoPreview) {
    photoInput.addEventListener('change', function () {
        const file = this.files[0];

        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            previewUrl = null;
        }

        if (file && file.type.startsWith('image/')) {
            previewUrl = URL.createObjectURL(file);
            photoPreview.src = previewUrl;
            photoPreview.hidden = false;
        } else {
            photoPreview.removeAttribute('src');
            photoPreview.hidden = true;
        }
    });
}
