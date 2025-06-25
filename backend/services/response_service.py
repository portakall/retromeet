from sqlalchemy.orm import Session
from backend.database.models import Participant, Response, Project, ProjectParticipant
from backend.agents.crew import create_agents
from typing import Dict, Any, List, Optional
from crewai import Task, Crew
import os
import tempfile

class ResponseService:
    def __init__(self, db: Session):
        self.db = db
        self.agents = create_agents()
    
    def get_participants_for_project(self, project_id: int) -> List[Participant]:
        """Get all participants for a specific project"""
        participants = self.db.query(Participant).join(
            ProjectParticipant, Participant.id == ProjectParticipant.participant_id
        ).filter(ProjectParticipant.project_id == project_id).all()
        return participants
    
    def get_participant_by_name(self, name: str) -> Optional[Participant]:
        """Get a participant by name"""
        return self.db.query(Participant).filter(Participant.name == name).first()
    
    def create_participant(self, name: str, avatar_path: Optional[str] = None) -> Participant:
        """Create a new participant (not associated with any project yet)"""
        participant = Participant(name=name, avatar_path=avatar_path)
        self.db.add(participant)
        self.db.commit()
        self.db.refresh(participant)
        return participant
    
    def add_participant_to_project(self, participant_id: int, project_id: int) -> bool:
        """Add an existing participant to a project"""
        # Check if association already exists
        existing = self.db.query(ProjectParticipant).filter(
            ProjectParticipant.participant_id == participant_id,
            ProjectParticipant.project_id == project_id
        ).first()
        
        if existing:
            return False  # Already associated
        
        association = ProjectParticipant(
            participant_id=participant_id,
            project_id=project_id
        )
        self.db.add(association)
        self.db.commit()
        return True
    
    def store_response(self, participant_id: int, project_id: int, question: str, response_text: str) -> Response:
        """Store a participant's response for a specific project"""
        response = Response(
            participant_id=participant_id,
            project_id=project_id,
            question=question,
            original_response=response_text
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response
    
    def refine_response(self, response_id: int):
        """
        Refines all responses for a participant in a project by generating a single coherent speech.
        """
        # Fetch the initial response to get participant and project context
        initial_response = self.db.query(Response).filter(Response.id == response_id).first()
        if not initial_response:
            print(f"WARN: refine_response called with invalid response_id {response_id}")
            return

        participant = initial_response.participant
        project_id = initial_response.project_id

        print(f"INFO: Starting refine_response for participant {participant.id} in project {project_id}")

        # 1. Fetch all original responses for this participant in this project
        all_participant_responses = self.db.query(Response).filter(
            Response.participant_id == participant.id,
            Response.project_id == project_id
        ).order_by(Response.created_at).all()

        if not all_participant_responses:
            print(f"INFO: No original responses found for participant {participant.id} in project {project_id} to refine.")
            return

        # 2. Format the responses for the agent
        # We only want to process original responses that haven't been part of a refinement yet, 
        # or if we decide to re-generate, we'd clear refined_response first.
        # For now, let's assume we always re-generate based on all current original_responses.
        original_qa_pairs = []
        for r in all_participant_responses:
            if r.original_response: # Ensure there's an original response to process
                original_qa_pairs.append(f"- Question: {r.question}\n  Answer: {r.original_response}")
        
        if not original_qa_pairs:
            print(f"INFO: No original response text found for participant {participant.id} in project {project_id}.")
            return
            
        formatted_responses_text = "\n".join(original_qa_pairs)
        print(f"INFO: Formatted responses for participant {participant.id} (length {len(formatted_responses_text)}):\n{formatted_responses_text}")

        # 3. Create and execute the CrewAI task
        tuner_agent = self.agents.get('response_tuner')
        if not tuner_agent:
            print(f"ERROR: 'response_tuner' agent not found in self.agents.")
            return

        tuner_task = Task(
            description=(
                f"Take the following raw Q&A responses from a participant named {participant.name} "
                f"and synthesize them into a single, coherent, first-person speech. "
                f"The speech should flow naturally, be well-structured, and capture the key points of their feedback. "
                f"Do not just list the answers; weave them into a narrative. Ensure the output is only the speech itself.\n\n"
                f"Here are the responses:\n{{formatted_responses_input}}"
            ),
            agent=tuner_agent,
            expected_output="A single string containing the generated first-person speech. It should be suitable for direct presentation."
        )

        crew = Crew(agents=[tuner_agent], tasks=[tuner_task], verbose=True) # verbose=True for detailed output
        
        try:
            print(f"INFO: Kicking off CrewAI task for participant {participant.id}...")
            crew_output = crew.kickoff(inputs={'formatted_responses_input': formatted_responses_text})
            # The raw output from the last task is what we want
            refined_text = crew_output.raw
            print(f"INFO: CrewAI task completed for participant {participant.id}. Result:\n{refined_text}")
            
            # 4. Update all of the participant's response entries for this project with the single generated speech
            updated_count = 0
            for r in all_participant_responses:
                r.refined_response = refined_text
                updated_count += 1
            
            self.db.commit()
            print(f"INFO: Successfully generated and saved refined speech to {updated_count} response entries for participant {participant.id} in project {project_id}")

        except Exception as e:
            print(f"ERROR: CrewAI kickoff for response tuning failed for participant {participant.id} in project {project_id}: {e}")
            import traceback
            traceback.print_exc() # Print full traceback
            self.db.rollback()
            print("INFO: Database transaction rolled back due to error.")

    def process_response_pipeline(self, participant_name: str, project_id: int, question: str, response_text: str) -> Dict[str, Any]:
        """Process a response through the entire pipeline"""
        # Get or create participant
        participant = self.get_participant_by_name(participant_name)
        if not participant:
            participant = self.create_participant(name=participant_name)
        
        # Add participant to project if not already associated
        if not self.add_participant_to_project(participant.id, project_id):
            # Participant is already associated with the project
            pass
        
        # Store the response
        response = self.store_response(participant.id, project_id, question, response_text)
        
        # Refine the response
        self.refine_response(response.id)

        # Re-fetch the response to ensure we have the latest data, including refined_response
        updated_response = self.db.query(Response).filter(Response.id == response.id).first()
        
        return {
            "participant_id": participant.id,
            "response_id": updated_response.id,
            "question": updated_response.question,
            "original_response": updated_response.original_response,
            "refined_response": updated_response.refined_response
        }

    def process_chat_response(self, participant_name: str, project_id: int, chat_content: str, question: str = "Chat Response") -> Response:
        """Process a full chat response and save it as a markdown file
        
        Args:
            participant_name: Name of the participant
            project_id: ID of the project
            chat_content: Full chat conversation content
            question: Question or topic (defaults to "Chat Response")
            
        Returns:
            Response object with markdown file path
        """
        # Get or create participant
        participant = self.get_participant_by_name(participant_name)
        if not participant:
            participant = self.create_participant(name=participant_name)
        
        # Add participant to project if not already associated
        self.add_participant_to_project(participant.id, project_id)
        
        # Use ResponseCollectorTool to save chat as markdown file
        response_collector = None
        for agent in self.agents.values():
            for tool in agent.tools:
                if tool.name == "ResponseCollector":
                    response_collector = tool
                    break
            if response_collector:
                break
        
        if not response_collector:
            raise ValueError("ResponseCollector tool not found")
        
        # Save chat content as markdown file
        markdown_file_path = response_collector._run(
            chat_content=chat_content,
            participant_name=participant_name,
            project_id=project_id
        )
        
        # Store the response with markdown file path
        response = Response(
            participant_id=participant.id,
            project_id=project_id,
            question=question,
            original_response=chat_content[:1000] + "..." if len(chat_content) > 1000 else chat_content,  # Truncate for database
            chat_response_file_path=markdown_file_path
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        
        return response
    
    def get_all_responses(self, project_id: Optional[int] = None) -> List[Response]:
        """Get all responses, optionally filtering by project_id"""
        query = self.db.query(Response)
        if project_id:
            query = query.filter(Response.project_id == project_id)
        responses = query.all()
        return responses
