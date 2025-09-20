from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional # Added Optional
from pydantic import BaseModel # Added BaseModel
import json # Added json
import os

from backend.database.database import get_db
from backend.database.models import Response as ResponseModel, Project as ProjectModel
from backend.agents.crew import create_agents, create_summary_generation_task
from crewai import Crew

router = APIRouter()

# --- Pydantic Models for Structured Summary ---
class ActionItem(BaseModel):
    description: str
    priority: str

class ProjectSummaryOutput(BaseModel):
    title: str
    overview: str  # Markdown
    key_themes: str # Markdown
    positives: str # Markdown
    improvements: str # Markdown
    action_items: List[ActionItem]

import pathlib

SUMMARY_DIR = os.path.join(os.path.dirname(__file__), '../../summaries')
os.makedirs(SUMMARY_DIR, exist_ok=True)

@router.put(
    "/projects/{project_id}/summary",
    response_model=ProjectSummaryOutput,
    tags=["Summary"]
)
def update_project_summary(
    project_id: int,
    summary: ProjectSummaryOutput,
    db: Session = Depends(get_db)
):
    """
    Updates the project summary for a given project. Stores the summary as a JSON file for now.
    """
    summary_path = os.path.join(SUMMARY_DIR, f"project_{project_id}_summary.json")
    # Save the updated summary (create or overwrite)
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary.dict(), f, ensure_ascii=False, indent=2)
    return summary


# Ensure OPENAI_API_KEY is set in your environment or configure llm for the agent
# os.environ["OPENAI_API_KEY"] = "your_api_key_here"

@router.post(
    "/projects/{project_id}/summary",
    response_model=ProjectSummaryOutput, # Use the new Pydantic model
    tags=["Summary"]
)
def generate_project_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Generates a project summary using the summary_generator agent.
    It collects all unique refined responses for the project and uses them as input.
    The agent is expected to return a JSON string, which is then parsed and returned
    as a structured JSON object.
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

    refined_responses_query = (
        db.query(ResponseModel.refined_response)
        .filter(ResponseModel.project_id == project_id)
        .filter(ResponseModel.refined_response.isnot(None))
        .distinct(ResponseModel.participant_id)
        .all()
    )

    if not refined_responses_query:
        raise HTTPException(
            status_code=404,
            detail=f"No refined responses found for project {project_id}. Cannot generate summary."
        )

    all_tuned_responses_text = "\\n\\n---\\n\\n".join([r[0] for r in refined_responses_query if r[0]])

    if not all_tuned_responses_text.strip():
        raise HTTPException(
            status_code=400,
            detail=f"Refined responses for project {project_id} are empty or contain no actionable text."
        )

    agents = create_agents()
    summary_agent = agents.get('summary_generator')
    if not summary_agent:
        raise HTTPException(status_code=500, detail="Summary generator agent not found.")

    if not os.getenv("OPENAI_API_KEY") and not summary_agent.llm:
        print("WARN: OPENAI_API_KEY not found in environment. Summary generation might fail.")
        # Consider raising HTTPException if API key is strictly required and not configured via llm instance

    summary_task = create_summary_generation_task(
        summary_generator_agent=summary_agent,
        tuned_responses=all_tuned_responses_text
    )

    summary_crew = Crew(
        agents=[summary_agent],
        tasks=[summary_task],
        verbose=True
    )

    try:
        print(f"INFO: Kicking off summary generation for project {project_id}...")
        crew_result_raw_json = summary_crew.kickoff()

        if not crew_result_raw_json or not isinstance(crew_result_raw_json, str):
            # Handle cases where the output might be in a .raw attribute
            if hasattr(crew_result_raw_json, 'raw') and isinstance(crew_result_raw_json.raw, str):
                crew_result_raw_json = crew_result_raw_json.raw
            else:
                print(f"ERROR: Summary generation did not return a JSON string. Result: {crew_result_raw_json}")
                raise HTTPException(status_code=500, detail="Summary generation failed to produce a valid string output.")

        print(f"INFO: Raw JSON string from agent: {crew_result_raw_json}")

        # Attempt to strip markdown fences if present
        cleaned_json_string = crew_result_raw_json
        if crew_result_raw_json.strip().startswith("```json"):
            # Find the start of the actual JSON content after ```json
            json_start_index = crew_result_raw_json.find('{')
            # Find the end of the actual JSON content before the closing ```
            json_end_index = crew_result_raw_json.rfind('}')
            if json_start_index != -1 and json_end_index != -1 and json_start_index < json_end_index:
                cleaned_json_string = crew_result_raw_json[json_start_index : json_end_index + 1]
                print(f"INFO: Cleaned JSON string: {cleaned_json_string}")
            else:
                # Fallback or error if JSON markers are not found as expected
                print(f"WARN: Found '```json' prefix but could not reliably extract JSON content.")
        elif crew_result_raw_json.strip().startswith("```") and crew_result_raw_json.strip().endswith("```"):
             # Generic ``` stripping if ```json is not present
            cleaned_json_string = crew_result_raw_json.strip()[3:-3].strip()
            print(f"INFO: Cleaned JSON string (generic ``` strip): {cleaned_json_string}")

        # Parse the JSON string from the agent
        parsed_summary = json.loads(cleaned_json_string)
        
        # Validate with Pydantic model (FastAPI will also do this on return)
        # This also converts the dict to an instance of ProjectSummaryOutput
        validated_summary = ProjectSummaryOutput(**parsed_summary)

        print(f"INFO: Summary generated and parsed successfully for project {project_id}.")
        # Save summary to file for later PUT updates
        summary_path = os.path.join(SUMMARY_DIR, f"project_{project_id}_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(validated_summary.dict(), f, ensure_ascii=False, indent=2)
        return validated_summary # Return the Pydantic model instance

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from summary agent for project {project_id}. Error: {e}")
        print(f"LLM Output that caused error: {crew_result_raw_json}")
        raise HTTPException(status_code=500, detail=f"Failed to parse summary JSON from AI: {str(e)}. Check LLM output.")
    except Exception as e:
        print(f"ERROR: Summary generation crew failed for project {project_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred during summary generation: {str(e)}")
