document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.processed-image').forEach(function (img) {
        img.addEventListener('click', function (event) {
            const rect = img.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            alert(`Coordinates: (${x}, ${y})`);
        });
    });
});
