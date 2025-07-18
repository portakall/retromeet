from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
import os
import tempfile
from sqlalchemy.orm import Session
from backend.database.models import Participant, Response
from typing import List, Dict, Any, Optional
import json
import datetime
import pathlib
import re
from collections import Counter

AGENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(AGENT_FILE_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
BASE_PROJECT_DATA_PATH = os.path.join(BACKEND_DIR, "data", "projects")
CHAT_RESPONSES_DIR = os.path.join(PROJECT_ROOT, "frontend", "static", "chat_responses")

# Basic English stop words
STOP_WORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
    "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers",
    "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
    "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
])

class ResponseCollectorTool(BaseTool):
    name: str = "ResponseCollector"
    description: str = "Collects responses from participants and saves them as markdown files"
    
    def _run(self, chat_content: str, participant_name: str, project_id: int) -> str:
        """Process and store the collected chat response as a markdown file
        
        Args:
            chat_content: The full chat conversation content
            participant_name: Name of the participant
            project_id: ID of the project
            
        Returns:
            Path to the saved markdown file
        """
        try:
            # Ensure the chat responses directory exists
            os.makedirs(CHAT_RESPONSES_DIR, exist_ok=True)
            
            # Create a unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_participant_name = "".join(c for c in participant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_participant_name = safe_participant_name.replace(' ', '_')
            filename = f"project_{project_id}_{safe_participant_name}_{timestamp}.md"
            file_path = os.path.join(CHAT_RESPONSES_DIR, filename)
            
            # Create markdown content
            markdown_content = f"""# Chat Response - {participant_name}

**Project ID:** {project_id}  
**Participant:** {participant_name}  
**Date:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Chat Conversation

{chat_content}

---

*Generated automatically by RetroMeet Response Collector*
"""
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Return relative path from static directory
            relative_path = f"chat_responses/{filename}"
            return relative_path
            
        except Exception as e:
            print(f"[ResponseCollectorTool] ERROR saving chat response: {e}")
            raise



def create_agents():
    """Create and return the CrewAI agents"""
    
    # Create the researcher agent
    researcher = Agent(
        role='Response Collector',
        goal='Collect and organize participant responses to retrospective questions',
        backstory="""You are a skilled facilitator who excels at gathering and organizing 
        participant feedback during retrospective meetings. You ensure that all voices are heard 
        and responses are properly categorized.""",
        tools=[ResponseCollectorTool()],
        verbose=True,
        allow_delegation=False,
    )
    
    # Create the response tuner agent
    response_tuner = Agent(
        role='Response Tuner',
        goal='Generate coherent speeches from participant responses',
        backstory="""You are an expert communicator who can take fragmented responses 
        from participants and turn them into coherent, well-structured speeches that 
        capture the essence of their feedback while maintaining their voice and perspective.""",
        verbose=True,
        allow_delegation=False,
    )

    # Create the topic generator agent
    topic_generator = Agent(
        role='Discussion Topic Generator',
        goal='Analyze participant responses to identify key discussion topics',
        backstory="""You are an expert at synthesizing information from multiple sources. 
        Your strength lies in identifying patterns, themes, and key points from a collection of texts, 
        and presenting them as concise, actionable topics for discussion.""",
        verbose=True,
        allow_delegation=False,
    )

    # Create the relevance analyzer agent
    relevance_analyzer_agent = Agent(
        role='Relevance Analysis Expert',
        goal=(
            "Analyze a participant's response/speech against a specific discussion topic. "
            "Determine if the response is relevant to that topic. "
            "If relevant, extract the specific sentences or key phrases that directly discuss the topic. "
            "If not relevant, indicate that clearly."
        ),
        backstory=(
            "You are an expert in textual context and relevance. "
            "Your task is to accurately identify if a given piece of text discusses a specific topic, "
            "and if so, to pinpoint the exact parts of the text that are pertinent. "
            "You provide concise extractions or a clear indication of non-relevance."
        ),
        verbose=True,
        allow_delegation=False,
    )
    
    # Create the summary generator agent
    # TODO: Configure the OpenAI LLM for this agent, e.g., by setting OPENAI_API_KEY environment variable
    # or by passing an llm instance to the Agent constructor: llm=OpenAI(model_name="gpt-4")
    summary_generator = Agent(
        role='Project Summary Generator',
        goal='Generate a comprehensive project summary including key themes, what went well, what could be improved, and action items, based on participant responses.',
        backstory=(
            "You are an advanced AI assistant specialized in analyzing and summarizing textual data. "
            "You process multiple participant responses, identify overarching themes, categorize feedback into 'went well' and 'could be improved', "
            "and formulate actionable items to drive future improvements. You deliver clear, concise, and insightful summaries. "
            "Do NOT include generic or welcoming opening messages (such as 'Good afternoon, everyone' or similar) in your summaries. Focus strictly on the summary content."
        ),
        # tools=[], # Add any specific tools if needed later
        verbose=True,
        allow_delegation=False, # Or True if it needs to delegate to other agents
    )

    return {
        'researcher': researcher,
        'response_tuner': response_tuner,
        'topic_generator': topic_generator,
        'relevance_analyzer': relevance_analyzer_agent,
        'summary_generator': summary_generator
    }

def create_crew():
    """Create and return the CrewAI crew with all agents"""
    agents = create_agents()
    
    crew = Crew(
        agents=list(agents.values()),
        tasks=[],  # Tasks will be defined when needed
        verbose=True,
    )
    
    return crew

def create_summary_generation_task(summary_generator_agent: Agent, tuned_responses: str) -> Task:
    """Creates a task for the summary_generator agent to generate a project summary
    in a structured JSON format.

    Args:
        summary_generator_agent: The summary_generator agent instance.
        tuned_responses: A string containing all the tuned responses from participants.

    Returns:
        A Task object for summary generation.
    """
    return Task(
        description=(
            f"Analyze the following participant responses to generate a comprehensive project summary. "
            f"You will structure this summary as a JSON object. The JSON object will contain several keys "
            f"such as 'title', 'overview', 'key_themes', 'positives', 'improvements', and 'action_items'. "
            f"The *values* for 'overview', 'key_themes', 'positives', and 'improvements' should be strings "
            f"containing text formatted in Markdown, suitable for direct rendering. "
            f"Just to have an extra context, the project consists of 3 different teams - (AH - Admin Hierarchy, C360 (or PLATFORM), and OA - OrderAPI)."
            f"For example, the 'key_themes' value might be a Markdown string like: "
            f"\"- Theme 1: Description of theme\\n- Theme 2: Description of theme\". "
            f"The 'action_items' key will hold a list of objects, each with 'description' and 'priority'.\n\n"
            f"Base your analysis on the following participant responses:\n{tuned_responses}\n\n"
            f"Remember, your entire output must be a single, valid JSON object string. "
            f"Refer to the 'expected_output' field of this task for the precise JSON structure and an example."
            
        ),
        expected_output=(
            "A single, valid JSON string adhering to the specified structure. "
            "The JSON object should contain 'title', 'overview', 'key_themes', 'positives', 'improvements', and 'action_items' (array of objects with 'description' and 'priority'). "
            "All textual content within the JSON (like overview, positives, etc.) should be Markdown formatted."
        ),
        agent=summary_generator_agent
    )
