document.addEventListener('DOMContentLoaded', function() {
    const supportLink = document.getElementById('support-link');

    if (supportLink) {
        supportLink.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default link behavior

            // You can fetch content for the modal dynamically
            // For a simple popup, you might just define the content here
            const modalContent = `
                <h4>Support Information</h4>
                <p>For support, please contact us at support@example.com or call 123-456-7890.</p>
                <p>Alternatively, visit our <a href="/help/" target="_blank">Help Center</a>.</p>
            `;

            // Or, if your Django view at 'admin:support_modal_view' returns
            // HTML content, you can fetch it:
            /*
            fetch(supportLink.href)
                .then(response => response.text())
                .then(html => {
                    // Update the modal body with the fetched HTML
                    $('#supportModal .modal-body').html(html);
                    $('#supportModal').modal('show');
                })
                .catch(error => console.error('Error fetching support content:', error));
            */

            // Create or update a Bootstrap modal element (assuming Bootstrap is available via Jazzmin)
            // You might need to add this modal HTML to your base admin template or create it dynamically.
            let modalElement = document.getElementById('supportModal');
            if (!modalElement) {
                modalElement = document.createElement('div');
                modalElement.id = 'supportModal';
                modalElement.classList.add('modal', 'fade');
                modalElement.setAttribute('tabindex', '-1');
                modalElement.setAttribute('role', 'dialog');
                modalElement.setAttribute('aria-labelledby', 'supportModalLabel');
                modalElement.setAttribute('aria-hidden', 'true');
                modalElement.innerHTML = `
                    <div class="modal-dialog" role="document">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title" id="supportModalLabel">Support</h5>
                                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            </div>
                            <div class="modal-body">
                                </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.appendChild(modalElement);
            }

            // Set the content
            modalElement.querySelector('.modal-body').innerHTML = modalContent;

            // Show the modal using Bootstrap's JavaScript API
            // Requires jQuery, which Jazzmin often includes
            $(modalElement).modal('show');
        });
    }
});