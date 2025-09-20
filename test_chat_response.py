#!/usr/bin/env python3
"""
Test script to demonstrate the new chat response functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
PROJECT_ID = 1
PARTICIPANT_NAME = "Test User"

# Sample chat content
SAMPLE_CHAT_CONTENT = """**User**: Hello, I'd like to share my thoughts about our recent sprint.

**Assistant**: Great! I'd love to hear your retrospective thoughts. What went well during this sprint?

**User**: Well, I think our team communication improved a lot. We had daily standups that were actually productive, and everyone was engaged. The new project management tool we adopted really helped with tracking our progress.

**Assistant**: That's excellent to hear! Improved communication and better tooling can make a huge difference. What about challenges - were there any areas where you felt things could have gone better?

**User**: Yes, definitely. I think we underestimated the complexity of the authentication module. It took us almost twice as long as planned. Also, we had some issues with the testing environment that caused delays in our deployment pipeline.

**Assistant**: Those are valuable insights. Estimation challenges and infrastructure issues are common pain points. What do you think we should do differently in the next sprint?

**User**: I'd suggest we do more detailed technical analysis during planning, maybe involve the senior developers more in estimation. And we definitely need to invest time in stabilizing our CI/CD pipeline - maybe dedicate a full day to fixing those issues.

**Assistant**: Those sound like actionable improvements. Is there anything else you'd like to add about the sprint?

**User**: Just that despite the challenges, I'm proud of what we accomplished. The team really pulled together when we hit those roadblocks, and the final product quality is really good.

**Assistant**: Thank you for sharing such thoughtful feedback! Your insights about communication improvements, estimation challenges, and the need for better infrastructure planning will be valuable for the team's continuous improvement."""

def test_create_project():
    """Create a test project"""
    try:
        response = requests.post(f"{BASE_URL}/projects/", json={
            "name": "Test Retrospective Project"
        })
        if response.status_code == 200:
            project = response.json()
            print(f"✅ Created project: {project['name']} (ID: {project['id']})")
            return project['id']
        else:
            print(f"❌ Failed to create project: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return None

def test_create_chat_response(project_id):
    """Create a test chat response"""
    try:
        response = requests.post(f"{BASE_URL}/responses/chat", json={
            "participant_name": PARTICIPANT_NAME,
            "project_id": project_id,
            "chat_content": SAMPLE_CHAT_CONTENT,
            "question": "Sprint Retrospective Chat"
        })
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ Created chat response for {PARTICIPANT_NAME}")
            print(f"   Response ID: {chat_response['id']}")
            print(f"   Markdown file: {chat_response['chat_response_file_path']}")
            return chat_response
        else:
            print(f"❌ Failed to create chat response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating chat response: {e}")
        return None

def test_get_project_responses(project_id):
    """Get all responses for the project"""
    try:
        response = requests.get(f"{BASE_URL}/responses/project/{project_id}")
        if response.status_code == 200:
            responses = response.json()
            print(f"✅ Retrieved {len(responses)} responses for project {project_id}")
            for resp in responses:
                print(f"   - {resp['question']} by participant {resp['participant_id']}")
                if resp['chat_response_file_path']:
                    print(f"     📄 Markdown file: {resp['chat_response_file_path']}")
            return responses
        else:
            print(f"❌ Failed to get responses: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting responses: {e}")
        return None

def main():
    print("🚀 Testing Chat Response Functionality")
    print("=" * 50)
    
    # Test 1: Create a project
    print("\n1. Creating test project...")
    project_id = test_create_project()
    if not project_id:
        print("❌ Cannot continue without a project")
        return
    
    # Test 2: Create a chat response
    print(f"\n2. Creating chat response for project {project_id}...")
    chat_response = test_create_chat_response(project_id)
    if not chat_response:
        print("❌ Failed to create chat response")
        return
    
    # Test 3: Retrieve project responses
    print(f"\n3. Retrieving all responses for project {project_id}...")
    responses = test_get_project_responses(project_id)
    
    print("\n✅ All tests completed!")
    print("\nNext steps:")
    print("1. Open the React frontend and navigate to the Responses page")
    print("2. Look for the 'View Full Chat Response' button")
    print("3. Click it to see the markdown file in a dialog")

if __name__ == "__main__":
    main()
