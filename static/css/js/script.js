document.addEventListener('DOMContentLoaded', function () {
    const slider = document.querySelector('.box');
    const items = Array.from(slider.children);

    // Remove existing clones if needed
    while (slider.children.length > items.length) {
        slider.removeChild(slider.lastChild);
    }

    // Log the number of items before cloning
    console.log('Number of items before cloning:', items.length);

    // Clone all items and append them to the slider
    items.forEach(item => {
        let clone = item.cloneNode(true);
        slider.appendChild(clone);
    });

    // Log the number of items after cloning
    console.log('Number of items after cloning:', slider.children.length);
});
