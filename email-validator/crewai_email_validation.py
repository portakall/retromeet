import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import requests
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAILHIPPO_API_KEY = os.getenv("EMAILHIPPO_API_KEY")
HUBSPOT_PRIVATE_APP_TOKEN = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")

# Fail early if any .env var is missing
for var, val in {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "EMAILHIPPO_API_KEY": EMAILHIPPO_API_KEY,
    "HUBSPOT_PRIVATE_APP_TOKEN": HUBSPOT_PRIVATE_APP_TOKEN
}.items():
    if not val:
        raise EnvironmentError(f"🚨 Missing required env var: {var}")

# Init LLM + HubSpot
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-3.5-turbo", temperature=0)
hubspot_client = HubSpot(access_token=HUBSPOT_PRIVATE_APP_TOKEN)

# EmailHippo API call
def validate_email(email):
    url = f"https://api.hippoapi.com/v3/more/json/{EMAILHIPPO_API_KEY}/{email}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # DEBUG: print raw if needed
        print(f"📨 Raw response for {email}: {data}")

        mailbox = data.get("emailVerification", {}).get("mailboxVerification", {})
        trust = data.get("hippoTrust", {})
        send = data.get("sendAssess", {})

        result = mailbox.get("result", "Unknown")
        reason = mailbox.get("reason", "Unknown")
        trust_score = trust.get("score", "N/A")
        trust_level = trust.get("level", "N/A")
        quality_score = send.get("inboxQualityScore", "N/A")

        # Formatted summary for HubSpot
        summary = (
            f"Result: {result}\n"
            f"Reason: {reason}\n"
            f"Trust Score: {trust_score}\n"
            f"Trust Level: {trust_level}\n"
            f"Inbox Quality Score: {quality_score}"
        )

        return summary

    except requests.RequestException as e:
        print(f"⚠️ EmailHippo error for {email}: {e}")
        return f"error: {str(e)}"


# Update HubSpot if valid
def update_hubspot(email, dns_result):
    search_filter = {
        "filterGroups": [{
            "filters": [{"propertyName": "email", "operator": "EQ", "value": email}]
        }],
        "properties": ["email"],
        "limit": 1
    }

    results = hubspot_client.crm.contacts.search_api.do_search(public_object_search_request=search_filter)

    for contact in results.results:
        contact_id = contact.id
        properties = {
            "emailhippo___email_verification_dns": dns_result
        }

        # ✅ Only mark validation as "No" if result is positive
        if dns_result.startswith("Result: Ok"):
            properties["cg_emailhippo_validation_required"] = "No"
        else:
            with open("hippo_failures.txt", "a") as f:
                f.write(f"{email} => {dns_result}\n")

        hubspot_client.crm.contacts.basic_api.update(
            contact_id,
            SimplePublicObjectInput(properties=properties)
        )

        print(f"✅ Updated: {email} => DNS: {dns_result}")

# Agent + task
agent = Agent(
    role="Email Validation Bot",
    goal="Validate emails via EmailHippo and update DNS results in HubSpot",
    backstory="You help ensure our CRM emails are verified.",
    allow_delegation=False,
    verbose=True,
    llm=llm
)

task = Task(
    description=(
        "Fetch all HubSpot contacts where cg_emailhippo_validation_required is 'Yes' "
        "and emailhippo___email_verification_dns is missing. "
        "Validate their email DNS via EmailHippo and push results back to HubSpot."
    ),
    expected_output="Valid contacts updated; failed ones logged locally.",
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task], verbose=True)

# Main logic
if __name__ == "__main__":
    print("🚀 Starting email validation crew...")

    search_filter = {
        "filterGroups": [{
            "filters": [
                {"propertyName": "cg_emailhippo_validation_required", "operator": "EQ", "value": "Yes"},
                {"propertyName": "emailhippo___email_verification_dns", "operator": "NOT_HAS_PROPERTY"}
            ]
        }],
        "properties": ["email"],
        "limit": 100
    }

    results = hubspot_client.crm.contacts.search_api.do_search(public_object_search_request=search_filter)

    for contact in results.results:
        email = contact.properties.get("email")
        if email:
            dns_result = validate_email(email)
            update_hubspot(email, dns_result)

    # Optional: let CrewAI describe what just happened
    crew.kickoff()
