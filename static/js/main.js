document.addEventListener('DOMContentLoaded', () => {
    
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(msg => {
                msg.style.transition = "opacity 0.5s ease";
                msg.style.opacity = "0";
                setTimeout(() => msg.remove(), 500); // Remove from DOM after fade
            });
        }, 5000);
    }

    // Confirmation for cancelling rides or deleting items
    const dangerButtons = document.querySelectorAll('.btn-danger');
    dangerButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            if (!confirm("Are you sure you want to perform this action? This cannot be undone.")) {
                e.preventDefault(); // Stop the form submission or link navigation
            }
        });
    });
});