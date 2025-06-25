import gradio as gr
import requests
import os
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Define the questions for the retrospective
RETRO_QUESTIONS = [
    "How was the overall performance of the sprint?",
    "What was good? Please mention everything separately.",
    "What was challenging or difficult? Please mention everything separately.",
    "What did you learn or experience?",
    "Is there anything you could change in the future sprint?"
]

def create_chat_interface(api_url: str = "http://localhost:8000", project_id: int = None, project_participants_details: List[Dict[str, Any]] = None):
    """Create a Gradio chat interface for collecting responses
    
    Args:
        api_url: The URL of the backend API
        project_participants: Optional list of participant objects with at least a 'name' field
    """
    
    # Store project_id and participant details for later use
    current_project_id = project_id
    participant_name_to_id_map = {}
    if project_participants_details:
        participant_name_to_id_map = {p["name"]: p["id"] for p in project_participants_details}

    participant_all_responses = {} # Accumulate responses here

    # Get participants from the provided list or API
    def get_participants(attempt_api_call_if_no_details: bool = False):
        # If project_participants_details were provided, use those directly
        if project_participants_details:
            print("[ChatInterface.get_participants] Using provided project_participants_details.")
            return [p["name"] for p in project_participants_details]
        
        # If no details provided AND we are instructed to try the API:
        if attempt_api_call_if_no_details:
            print(f"[ChatInterface.get_participants] No project_participants_details provided, attempting to fetch from API: {api_url}/participants/")
            try:
                response = requests.get(f"{api_url}/participants/")
                response.raise_for_status() # Raise an exception for bad status codes
                participants_data = response.json()
                # Assuming participants_data is a list of dicts with a 'name' key
                return [p["name"] for p in participants_data if isinstance(p, dict) and "name" in p]
            except requests.exceptions.RequestException as e:
                print(f"[ChatInterface.get_participants] Error fetching participants from API: {e}")
                return []  # Fallback in case of API error
        
        # Default: No details provided and not attempting API call (e.g., during initial setup)
        print("[ChatInterface.get_participants] No project_participants_details, and API call not attempted.")
        return []
    
    # Submit response to the API
    def submit_response(participant_name: str, question: str, response_text: str) -> str:
        try:
            # First, create a regular response entry
            payload = {
                "participant_name": participant_name,
                "project_id": current_project_id, # Add project_id
                "question": question,
                "response_text": response_text
            }
            
            # Save the response to the database
            create_response = requests.post(f"{api_url}/responses/", json=payload)
            
            if create_response.status_code != 200:
                print(f"Warning: Failed to create response entry: {create_response.text}")
            
            # Process the response
            process_response = requests.post(f"{api_url}/responses/process", json=payload)
            
            if process_response.status_code == 200:
                return "Response submitted successfully! It will be processed."
            else:
                return f"Error submitting response: {process_response.text}"
        except Exception as e:
            print(f"Exception in submit_response: {e}")
            return f"Error: {str(e)}"
    
    # Function to get AI response using OpenAI API
    def get_ai_response(participant_name, question, user_message):
        try:
            print(f"Debug: OpenAI API key loaded: {openai.api_key[:10] if openai.api_key else 'None'}...")
            if not openai.api_key or openai.api_key in ["your_openai_api_key_here", "your-openai-key-here"]:
                return "Error: OpenAI API key not configured. Please set your API key in the .env file."
            
            # Create a prompt for the AI that does NOT include a follow-up question
            prompt = f"You are a helpful retrospective facilitator. The participant {participant_name} is answering the question: '{question}'. Their response was: '{user_message}'. Provide a brief, encouraging response that acknowledges their input. DO NOT ask any follow-up questions."
            
            # Call the OpenAI API
            response = openai.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful retrospective facilitator. Keep responses brief and encouraging. DO NOT ask follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            
            # Extract the AI's response
            ai_response = response.choices[0].message.content.strip()
            return ai_response
        
        except Exception as e:
            print(f"Error with OpenAI API: {e}")
            return f"I encountered an error: {str(e)}. Please try again or check your API configuration."
    
    # Function to handle chat logic (formerly respond)
    def chat_logic(message: str, history: list, participant_name: str, current_question_on_entry: str):
        """
        Handles the core chat logic.
        history: List of message dictionaries with 'role' and 'content' keys
        Returns:
            tuple: (bot_message_to_display, next_question_for_gradio_state)
        """
        if not participant_name:
            return "Please select a participant first.", current_question_on_entry

        try:
            if current_question_on_entry not in RETRO_QUESTIONS:
                if current_question_on_entry == "COMPLETED":
                    return "The retrospective is complete. Thank you!", "COMPLETED"
                current_q_idx = -1 # Indicates to start fresh or error
            else:
                current_q_idx = RETRO_QUESTIONS.index(current_question_on_entry)
        except ValueError:
            current_q_idx = -1

        if message.lower().strip() in ["next", "next question", "continue", "go on"]:
            if current_question_on_entry == "COMPLETED":
                return "The retrospective is already complete. Thank you!", "COMPLETED"
            
            next_q_for_logic_idx = current_q_idx + 1 if current_q_idx != -1 else 0

            if next_q_for_logic_idx >= len(RETRO_QUESTIONS):
                bot_msg = "Thank you for participating in the retrospective meeting! Your responses have been recorded."
                
                # ---- START API CALL LOGIC ----
                # When all questions are answered, collect all responses for this participant and call the API
                collected_responses = participant_all_responses.get(participant_name, [])
                if collected_responses:
                    print(f"All questions answered for {participant_name}. Collected {len(collected_responses)} responses.")
                    
                    # Format the chat content from the history
                    chat_content = ""
                    try:
                        for entry in collected_responses:
                            chat_content += f"**Question:** {entry['question']}\n\n"
                            chat_content += f"**User Response:** {entry['answer']}\n\n"
                            if entry.get('ai_response'):
                                chat_content += f"**Assistant Response:** {entry['ai_response']}\n\n"
                            chat_content += "---\n\n"
                        
                        # Add the full conversation history
                        chat_content += "**Full Conversation:**\n\n"
                        for msg in history:
                            role = "User" if msg.get("role") == "user" else "Assistant"
                            chat_content += f"**{role}:** {msg.get('content', '')}\n\n"
                        
                        print(f"Formatted chat content length: {len(chat_content)}")
                        
                        # Call the API to save the chat response
                        api_url = "http://localhost:8000/responses/chat"
                        payload = {
                            "participant_name": participant_name,
                            "project_id": current_project_id,  # Use the dynamic project ID for this session
                            "chat_content": chat_content,
                            "question": "Retrospective Chat Session"
                        }
                        
                        response = requests.post(api_url, json=payload)
                        if response.status_code == 200:
                            print(f"Successfully saved chat response for {participant_name}")
                        else:
                            print(f"Failed to save chat response: {response.status_code} - {response.text}")
                    except Exception as e:
                        print(f"Error in API call logic: {e}")
                        import traceback
                        traceback.print_exc()
                # ---- END API CALL LOGIC ----
                return bot_msg, "COMPLETED"
            else:
                next_q_for_state = RETRO_QUESTIONS[next_q_for_logic_idx]
                bot_msg = f"**Question {next_q_for_logic_idx + 1}:** {next_q_for_state}"
                return bot_msg, next_q_for_state

        if current_question_on_entry == "COMPLETED":
            return "The retrospective is complete. Please refresh if you wish to start over.", "COMPLETED"
        if current_question_on_entry not in RETRO_QUESTIONS:
            return "There was an issue with the current question. Please select your name again to restart.", RETRO_QUESTIONS[0]

        # Accumulate responses before processing
        if current_question_on_entry in RETRO_QUESTIONS and message.lower().strip() not in ["next", "next question", "continue", "go on"]:
            if participant_name not in participant_all_responses:
                participant_all_responses[participant_name] = []
            
            already_answered = False
            if participant_all_responses[participant_name]:
                last_entry = participant_all_responses[participant_name][-1]
                if last_entry["question"] == current_question_on_entry:
                    last_entry["answer"] = message # Update if re-answering same question
                    already_answered = True
            
            if not already_answered:
                participant_all_responses[participant_name].append({
                    "question": current_question_on_entry,
                    "answer": message
                })

        response_result = submit_response(participant_name, current_question_on_entry, message)
        ai_response = get_ai_response(participant_name, current_question_on_entry, message)
        bot_msg = f"{ai_response}\n\nType 'next' when you're ready for the next question."
        return bot_msg, current_question_on_entry
    
    # Create the Gradio interface with a simple theme
    with gr.Blocks(title="RetroMeet - Retrospective Chat", theme="default") as demo:
        gr.Markdown("# RetroMeet - Retrospective Chat")
        gr.Markdown("Please select your name and answer the retrospective questions.")
        
        # State for tracking the current question
        current_question = gr.State(RETRO_QUESTIONS[0])
        
        # Participant selection dropdown
        participant = gr.Dropdown(
            choices=get_participants(),
            label="Select your name",
            value=None,
            interactive=True
        )
        
        # Refresh button for participant list
        refresh_btn = gr.Button("Refresh Participant List")
        
        # Chat interface
        chatbot = gr.Chatbot(height=400, type="messages")
        msg = gr.Textbox(label="Your response")
        
        # Submit button
        submit_btn = gr.Button("Submit")
        
        # Event handlers
        refresh_btn.click(
            fn=lambda: gr.Dropdown(choices=get_participants()),
            outputs=[participant],
            queue=False,  # Explicitly disable queue
            api_name=None # Disable API endpoint creation
        )

        def on_participant_select(participant_name_selected):
            if participant_name_selected:
                first_question_text = RETRO_QUESTIONS[0]
                questions_md = "\n".join([f"{i+1}. {q}" for i, q in enumerate(RETRO_QUESTIONS)])
                initial_history = [
                    {"role": "assistant", "content": f"Hello {participant_name_selected}! I will be your retrospective assistant. I hope everything went well in the sprint and you are ready to share your thoughts. During our conversation, I will ask you the following questions:\n\n{questions_md}\n\nLet's start with the first question.\n\n**Question 1:** {first_question_text}"}
                ]
                # Clear any old responses for this participant when they are selected
                if participant_name_selected in participant_all_responses:
                    del participant_all_responses[participant_name_selected]
                return initial_history, first_question_text, "" # history, current_question_state, msg_textbox_value
            return [], RETRO_QUESTIONS[0], "" # Clear history, reset question state, clear msg

        participant.select(
            fn=on_participant_select,
            inputs=[participant],
            outputs=[chatbot, current_question, msg],
            queue=False,  # Explicitly disable queue for this event
            api_name=None # Disable API endpoint creation for this event
        )
        
        def process_chat(message, history, participant_name, current_question_state_val):
            if not participant_name:
                # Append to history for gr.Chatbot
                updated_history = history + [{"role": "assistant", "content": "Please select a participant first."}]
                return "", updated_history, current_question_state_val

            bot_message, new_question_for_state = chat_logic(message, history, participant_name, current_question_state_val)
            
            # Append user message and bot's response to history for gr.Chatbot
            updated_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": bot_message}
            ]
            
            return "", updated_history, new_question_for_state
        
        # Set up event handlers with explicit queue=False to avoid queueing issues
        submit_btn.click(
            fn=process_chat,
            inputs=[msg, chatbot, participant, current_question],
            outputs=[msg, chatbot, current_question],
            queue=False,
            api_name=None  # Disable API endpoint creation
        )
        
        msg.submit(
            fn=process_chat,
            inputs=[msg, chatbot, participant, current_question],
            outputs=[msg, chatbot, current_question],
            queue=False,
            api_name=None  # Disable API endpoint creation
        )
    
    return demo

def launch_chat(project_id=None, project_participants=None, share=True, server_name="localhost", server_port=8080):
    """Launch the chat interface
    
    Args:
        project_id: Optional project ID to associate with this chat session
        project_participants: Optional list of participant objects with at least a 'name' field
        share: Whether to create a shareable link
        server_name: Server hostname
        server_port: Server port
    """
    # Create the chat interface, passing project_id and full participant details
    demo = create_chat_interface(
        project_id=project_id, 
        project_participants_details=project_participants
    )
    
    print(f"Launching Gradio interface on {server_name}:{server_port}")
    
    # Launch with absolute minimum parameters
    try:
        # Avoid any optional parameters that might cause issues
        demo.launch(
            server_name=server_name,
            server_port=server_port,
            share=share,
            quiet=True  # Reduce log output
        )
        print("Gradio interface launched successfully")
    except Exception as e:
        print(f"Error launching Gradio interface: {e}")
    
    # Always return a fixed URL
    return f"http://{server_name}:{server_port}"

if __name__ == "__main__":
    launch_chat()
