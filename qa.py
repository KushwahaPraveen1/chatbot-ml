from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create generative model and chat
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Function to get response from the chatbot
def get_gemini_response(question):
    response = chat.send_message(question)
    return response

# Initialize FastAPI app
app = FastAPI()

# Global variable to store chat history
chat_history = []

# Create a Pydantic model for request input
class ChatRequest(BaseModel):
    input: str

# Create a Pydantic model for response
class ChatResponse(BaseModel):
    input: str
    response: str
    chat_history: list

# Define API endpoint for chatbot interaction
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(chat_request: ChatRequest):
    try:
        # Get input from the request
        input_text = chat_request.input

        # Prompt for the chatbot
        prompt = """Now remember that you are a health chatbot and only gonna address questions or input is related to health. 
        It can be a diet related question or workout related question, keep your answer plain and simple, and don't share any 
        unnecessary information. Don't add anything to the output which is not asked. If the text input is something not 
        related to health in any way, you just give the output "I don't have information regarding this topic". Q"""

        # Create a question for the chatbot
        question = prompt + input_text

        # Get response from the chatbot
        response = get_gemini_response(question)

        # Process the response
        if response.text == 'NO':
            response_text = "I'm sorry, I can't provide any information regarding this topic."
        else:
            response_text = "\n".join(chunk.text for chunk in response)

        # Build the response model
        response_data = {
            'input': input_text,
            'response': response_text,
            'chat_history': chat_history
        }

        # Update the global chat history
        chat_history.append(("User", input_text))
        chat_history.append(("Bot", response_text))

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Define API endpoint to clear chat history
@app.delete("/api/clear-chat")
def clear_chat():
    global chat_history
    chat_history = []
    return {"message": "Chat history cleared successfully"}

if __name__ == "__main__":
    # Run the FastAPI app using Uvicorn
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
