// Function to send a message
function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();

    if (message === "") return;

    // Display the user's message in the chatbox
    appendMessage('You', message);

    // Send the message to the Flask backend
    fetch('https://archive-intellect-d2qb.vercel.app/get_response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        // Display the chatbot's response
        appendMessage('Milo', data.response);
    })
    .catch(error => {
        appendMessage('Milo', 'Error: ' + error.message);
    });

    // Clear the input box
    userInput.value = "";
}

// Function to upload a PDF
function uploadPDF() {
    const pdfInput = document.getElementById("pdf-upload");
    const file = pdfInput.files[0];

    if (file) {
        const formData = new FormData();
        formData.append("file", file);

        fetch('https://archive-intellect-d2qb.vercel.app/upload_pdf', {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.summary) {
                appendMessage('Milo', 'PDF Uploaded: ' + data.summary);
            } else if (data.error) {
                appendMessage('Milo', 'Error: ' + data.error);
            }
        })
        .catch(error => {
            appendMessage('Milo', 'Error: ' + error.message);
        });
    } else {
        appendMessage('Milo', 'Please select a PDF file to upload.');
    }
}
