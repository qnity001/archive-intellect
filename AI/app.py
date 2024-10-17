from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
import time
import json

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure the Gemini AI SDK with the API key
genai.configure(api_key=os.getenv('API_KEY'))

# Path to the data.json file for global conversation history and PDF references
DATA_FILE = 'data.json'

# Function to load system instruction from a text file with utf-8 encoding
def load_system_instruction(file_path):
    """Loads system instruction from a text file with utf-8 encoding."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Load the system instruction from the text file
system_instruction = load_system_instruction('system_instruction.txt')

# Helper function to load conversation history and PDF references from data.json
def load_history():
    """Load the conversation history and PDF references from data.json."""
    try:
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)  # Load the data
            # Ensure 'pdfs' exists and is a list
            if 'pdfs' not in data or not isinstance(data['pdfs'], list):
                data['pdfs'] = []
            # Ensure 'history' exists and is a list
            if 'history' not in data or not isinstance(data['history'], list):
                data['history'] = []
            return data
    except FileNotFoundError:
        # If the file doesn't exist, return default structure
        return {'history': [], 'pdfs': []}

# Helper function to save conversation history and PDF references to data.json
def save_history(data):
    """Save the conversation history and PDF references to data.json."""
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Helper function to upload PDF to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        print(f"Error uploading file to Gemini: {str(e)}")
        raise Exception(f"Failed to upload file to Gemini: {str(e)}")

# Helper function to wait for files to be active
def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    try:
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        print("...all files ready")
    except Exception as e:
        print(f"Error during file processing: {str(e)}")
        raise Exception(f"Error during file processing: {str(e)}")

# Route for the homepage
@app.route('/')
def index():
    return render_template('bot.html')

# Route to handle PDF upload and process it with Gemini
@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    uploaded_file = request.files['file']  # Get the uploaded PDF file
    if uploaded_file:
        try:
            # Ensure the uploads directory exists
            if not os.path.exists('uploads'):
                os.makedirs('uploads')

            # Save the file locally
            file_path = os.path.join('uploads', uploaded_file.filename)
            uploaded_file.save(file_path)

            # Upload the PDF to Gemini and get its URI
            file = upload_to_gemini(file_path, mime_type="application/pdf")

            # Wait for the PDF to be processed
            wait_for_files_active([file])

            # Load the global conversation history and PDF references from the data.json file
            data = load_history()

            # Store the PDF information for future reference
            pdf_entry = {'filename': uploaded_file.filename, 'uri': file.uri, 'path': file_path}
            data['pdfs'].append(pdf_entry)

            # Start a chat session with the PDF file
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 64,
                    "max_output_tokens": 8192,
                    "response_mime_type": "application/json",
                },
                system_instruction=system_instruction,  # Load the instruction from the file
            )

            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [file],  # Add the PDF file as part of the chat history
                    },
                ]
            )

            # Ask the model to summarize the PDF
            response = chat_session.send_message("Summarize the PDF")
            summary_text = response.text

            # Append the model's response to the conversation history
            data['history'].append({'role': 'model', 'parts': [{'text': summary_text}]})

            # Save the updated conversation history and PDF references to the data.json file
            save_history(data)

            return jsonify({'summary': summary_text})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'No file uploaded'}), 400

# Route to get a response from Gemini AI with global history stored in data.json
@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json.get('message')

    # Load the global conversation history and PDF references from the data.json file
    data = load_history()
    conversation_history = data['history']
    pdfs = data['pdfs']

    # Modify system instruction to include reference to available PDFs
    system_instruction_with_pdfs = system_instruction + "\n\nYou have access to the following PDF files for reference:\n"
    for pdf in pdfs:
        system_instruction_with_pdfs += f"- {pdf['filename']}: {pdf['uri']}\n"

    # Create the model with configuration and safety settings
    generation_config = {
        "temperature": 1.35,        # Adjusts randomness; higher = more random
        "top_p": 0.95,              # Nucleus sampling; considers the top 95% probable tokens
        "top_k": 64,                # Considers the top 64 tokens
        "max_output_tokens": 300,   # Limits the number of tokens in the output
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction_with_pdfs,  # Use the modified system instruction
    )

    # Append the new user message to the conversation history
    conversation_history.append({'role': 'user', 'parts': [{'text': user_message}]})

    # Introduce a cool-down period (for example, 2 seconds)
    time.sleep(2)

    # Generate a response based on the user's input and the entire history
    try:
        chat_session = model.start_chat(history=conversation_history)  # Pass the global history to the chat model
        response = chat_session.send_message(user_message)
        response_text = response.text

        # Append the model's response to the conversation history
        conversation_history.append({'role': 'model', 'parts': [{'text': response_text}]})

        # Save the updated conversation history and PDF references to the data.json file
        save_history(data)

    except Exception as e:
        # Handle any errors that occur during the API request
        response_text = f"Error: {str(e)}"

    # Return the response and updated history to the client
    return jsonify({'response': response_text, 'history': conversation_history})

if __name__ == '__main__':
    # Ensure the uploads directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
