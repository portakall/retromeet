from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.services.response_service import ResponseService
from backend.agents.crew import create_agents, Task, Crew
from backend.database.models import Response as DBResponse # Alias to avoid conflict with FastAPI's Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json # Added json import
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Project Root to construct absolute paths for file reading
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

router = APIRouter()

@router.post("/projects/{project_id}/topics", tags=["Topics"])
def generate_topics(project_id: int, db: Session = Depends(get_db)):
    """
    Generate discussion topics for a project based on all participant responses.
    """
    response_service = ResponseService(db)
    all_responses = response_service.get_all_responses(project_id=project_id)

    if not all_responses:
        raise HTTPException(status_code=404, detail="No responses found for this project.")

    # Aggregate all text into a single string
    all_text = ""
    for r in all_responses:
        if r.original_response:
            all_text += r.original_response + " "
        if r.refined_response:
            all_text += r.refined_response + " "
        if r.chat_response_file_path:
            try:
                file_path = os.path.join(PROJECT_ROOT, "frontend", "static", r.chat_response_file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_text += f.read() + " "
            except Exception as e:
                print(f"WARN: Could not read chat file {r.chat_response_file_path}: {e}")

    if not all_text.strip():
        raise HTTPException(status_code=404, detail="No text content found in responses for this project.")

    logger.info(f"Aggregated text for topic generation (length: {len(all_text)} chars)")

    # --- Using CrewAI for topic generation ---
    agents = create_agents()  # Get the dictionary of all agents
    topic_generator_agent = agents['topic_generator'] # Get the specific agent by key

    # Create a task for the topic generator agent
    topic_task = Task(
        description=(
            "Analyze the combined text from all participant responses for a retrospective meeting. "
            "Just to have an extra context, the project consists of 3 different teams - (AH - Admin Hierarchy, C360 (or PLATFORM), and OA - OrderAPI)."
            "Your primary goal is to identify and extract **a small number (e.g., 5-7) of broad, thematic, high-level discussion topics based on the challenges/negatives mentioned in the responses.** "
            "These topics should synthesize multiple specific points, if present, into overarching themes that represent significant **negatives, problems, challenges, or systemic areas for improvement.** "
            "Do not simply list individual complaints. Instead, look for patterns, common threads, or underlying causes that can be discussed at a strategic level. "
            "For example, if multiple people mention specific tool issues, a high-level topic might be 'Tooling and Infrastructure Challenges' rather than listing each tool problem separately. "
            "Focus on issues that require collective discussion and potential action. "
            "**Avoid generating topics from purely positive statements or statements indicating no issues (e.g., 'everything was fine', 'no blockers'), unless these statements seem to mask underlying problems or warrant deeper investigation.** "
            "The topics should be concise and suitable for a meeting agenda. "
            "Please select simple words and avoid using complex or technical terms."
            "Present the output as a JSON list of strings."
        ),
        agent=topic_generator_agent,
        expected_output="A JSON list of strings, where each string is a unique discussion topic."
    )

    # Create a new Crew specifically for this task
    crew = Crew(
        agents=[topic_generator_agent],
        tasks=[topic_task],
        verbose=True  # Or False, depending on desired logging for this specific task
    )

    # Execute the task
    try:
        logger.info("Kicking off CrewAI for topic generation...")
        result = crew.kickoff(inputs={'all_text': all_text})
        logger.info(f"CrewAI kickoff successful. Result object: {result}")
        
        raw_output = result.raw  # Get the raw string output from CrewOutput object
        logger.info(f"Raw output from CrewAI for topic generation: {raw_output}")

        # Preprocess to remove markdown fences if present
        cleaned_output = raw_output.strip()
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:] # Remove ```json
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3] # Remove ```
        cleaned_output = cleaned_output.strip() # Ensure no leading/trailing whitespace remains
        
        # Attempt to parse the cleaned_output as JSON
        parsed_topics = json.loads(cleaned_output)
        # Ensure it's a list of strings as expected by the frontend
        if isinstance(parsed_topics, list) and all(isinstance(item, str) for item in parsed_topics):
            return parsed_topics
        else:
            logger.warning(f"Parsed JSON output is not a list of strings: {parsed_topics}. Attempting fallback parsing.")
            # Fallback if JSON is valid but not list of strings (e.g. a single string, or list of numbers)
            # This attempts to handle simple string representations of lists if JSON parsing failed to produce the right type.
            return [str(topic).strip() for topic in str(cleaned_output).strip('[]').split(',') if str(topic).strip()] # Ensure non-empty topics
    except json.JSONDecodeError:
        # Use cleaned_output for logging in case of JSONDecodeError as well, if cleaned_output was not valid JSON
        logger.warning(f"Cleaned output '{cleaned_output}' is not valid JSON. Attempting fallback string manipulation.")
        # Fallback for non-JSON strings that might look like a list (e.g., '[Topic 1, Topic 2]')
        # Ensure items are stripped and non-empty
        return [topic.strip() for topic in cleaned_output.strip('[]').split(',') if topic.strip()]
    except Exception as e:
        logger.error("Error during CrewAI kickoff for topic generation", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate topics using CrewAI: {e}")


class TopicRelevanceQuery(BaseModel):
    topic: str

class ParticipantTopicRelevance(BaseModel):
    participant_id: int
    participant_name: str
    participant_avatar_path: Optional[str] = None # Added avatar path
    relevant_snippets: List[str]

@router.post(
    "/projects/{project_id}/topic_responses",
    response_model=List[ParticipantTopicRelevance],
    summary="Get participant responses relevant to a specific topic"
)
async def get_responses_for_topic(
    project_id: int,
    query: TopicRelevanceQuery,
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching responses for project {project_id} relevant to topic: '{query.topic}'")
    response_service = ResponseService(db)
    
    try:
        project_responses = db.query(DBResponse).filter(DBResponse.project_id == project_id).all()
    except Exception as e:
        logger.error(f"Database error fetching responses for project {project_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error fetching responses from database.")

    if not project_responses:
        logger.info(f"No responses found for project {project_id}")
        return []

    participant_texts: Dict[int, Dict[str, Any]] = {}
    for resp in project_responses:
        if resp.participant_id not in participant_texts:
            participant_texts[resp.participant_id] = {
                "name": resp.participant.name, # Assuming relationship is loaded or accessible
                "avatar_path": resp.participant.avatar_path, # Added avatar path
                "texts": []
            }
        # Prioritize refined_response, fallback to original_response
        text_to_add = resp.refined_response if resp.refined_response and resp.refined_response.strip() else resp.original_response
        if text_to_add and text_to_add.strip():
            participant_texts[resp.participant_id]["texts"].append(text_to_add.strip())
    
    agents = create_agents()
    relevance_analyzer = agents.get('relevance_analyzer')
    if not relevance_analyzer:
        logger.error("Relevance analyzer agent not found.")
        raise HTTPException(status_code=500, detail="Relevance analyzer agent not configured.")

    results: List[ParticipantTopicRelevance] = []

    for participant_id, data in participant_texts.items():
        full_participant_text = "\n\n---\n\n".join(data["texts"])
        if not full_participant_text.strip():
            continue

        logger.debug(f"Analyzing text for participant {data['name']} (ID: {participant_id}) for topic: '{query.topic}'")
        
        relevance_task = Task(
            description=(
                f"Analyze the following text from a participant to determine if it is relevant to the discussion topic: '{query.topic}'. "
                f"The participant's text is: \n\n{{participant_text}}\n\n "
                f"If relevant, extract the specific sentences or key phrases that directly discuss this topic. "
                f"If not relevant, clearly indicate non-relevance."
            ),
            agent=relevance_analyzer,
            expected_output=(
                "A JSON object as a string with two keys: 'is_relevant' (boolean) and 'snippets' (a list of strings). "
                "Example for relevant: {\"is_relevant\": true, \"snippets\": [\"The participant mentioned X...\", \"They also said Y regarding the topic.\"]}. "
                "Example for not relevant: {\"is_relevant\": false, \"snippets\": []}."
            )
        )

        crew = Crew(
            agents=[relevance_analyzer],
            tasks=[relevance_task],
            verbose=False # Keep this less verbose for per-participant calls unless debugging
        )

        try:
            task_input = {'participant_text': full_participant_text, 'topic': query.topic}
            logger.debug(f"Kicking off relevance analysis crew for participant {data['name']} with input keys: {list(task_input.keys())}")
            crew_result = crew.kickoff(inputs=task_input)
            raw_output = crew_result.raw
            logger.debug(f"Relevance analysis for participant {data['name']} raw output: {raw_output}")
            
            parsed_relevance = json.loads(raw_output)
            if parsed_relevance.get("is_relevant") and parsed_relevance.get("snippets"):
                results.append(ParticipantTopicRelevance(
                    participant_id=participant_id,
                    participant_name=data["name"],
                    participant_avatar_path=data.get("avatar_path"), # Added avatar path
                    relevant_snippets=parsed_relevance["snippets"]
                ))
                logger.info(f"Participant {data['name']} found relevant to topic '{query.topic}'. Snippets: {len(parsed_relevance['snippets'])} items.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from relevance analyzer for participant {data['name']}: {raw_output}. Error: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error during relevance analysis for participant {data['name']}: {e}", exc_info=True)
            # Optionally, decide if this should halt or just skip the participant
            
    logger.info(f"Found {len(results)} participants relevant to topic '{query.topic}'.")
    return results
