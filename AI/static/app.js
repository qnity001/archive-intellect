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

// Function to append a message to the chat box
function appendMessage(sender, message) {
    const chatBox = document.getElementById('chat-box');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    if (sender === 'You') {
        messageElement.classList.add('user-message');

        const userName = document.createElement('div');
        userName.classList.add('user-name');
        userName.innerHTML = "You";
        messageElement.appendChild(userName);

        const userContent = document.createElement('div');
        userContent.classList.add('user-content');
        userContent.innerHTML = message;
        messageElement.appendChild(userContent);
    } else {
        messageElement.classList.add('bot-message');

        // Add bot image/avatar
        const botImage = document.createElement('div');
        botImage.classList.add('bot-image');
        botImage.innerHTML = "<img src=\"https://github.com/qnity001/coffee-break/blob/main/coffee/Mascot.png?raw=true\" alt=\"mascot\">";
        messageElement.appendChild(botImage);

        // Add bot's text container
        const botText = document.createElement('div');
        botText.classList.add('bot-text');
        messageElement.appendChild(botText);

        // Add bot's name
        const botName = document.createElement('div');
        botName.classList.add('bot-name');
        botName.innerHTML = sender;
        botText.appendChild(botName);

        // Add bot's message content
        const botContent = document.createElement('div');
        botContent.classList.add('bot-content');
        botContent.innerHTML = message;
        botText.appendChild(botContent);
    }

    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom of the chat
}

// Function to check if the Enter key is pressed in the input field
function checkEnterKey(event) {
    if (event.keyCode === 13 || event.key === 'Enter') {
        sendMessage(); // Trigger sendMessage function on Enter key press
    }
}

// Attach event listener to the message input field to detect Enter key
const userInput = document.getElementById('user-input');
userInput.addEventListener('keypress', checkEnterKey);

// Attach event listener for PDF upload button
const uploadButton = document.getElementById('pdf-upload-btn');
uploadButton.addEventListener('click', uploadPDF);

}
