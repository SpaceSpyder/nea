// Fade out flash messages after 3 seconds
setTimeout(function() {
    var flashes = document.querySelectorAll('.flashes li');
    flashes.forEach(function(flash) {
        flash.style.transition = 'opacity 0.6s ease-out';
        flash.style.opacity = '0';
        setTimeout(function() {
            flash.style.display = 'none';
        }, 450); // Wait for the transition to complete before hiding the element
    });
}, 2000); // 3 seconds delay before starting the fade out