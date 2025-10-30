import os
import json
from flask import Flask, request, jsonify
import requests
import pandas as pd
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
GITHUB_REPO = "Nithishrish23/Nithish-portfolio"
EXCEL_PATH = "test_cases/Nithish_Portfolio_TestCases.xlsx"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# --- Initialize OpenAI Model ---
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY
)

# --- Flask App ---
app = Flask(__name__)

# --- CrewAI Agents ---
impact_agent = Agent(
    name="Impact Analyzer",
    role="Test Impact Analyst",
    goal="Identify ONLY the test cases that are directly affected by code changes",
    backstory="""You are an expert at analyzing code changes and mapping them to test cases.
    You must be extremely selective and only return test cases that are directly related to the changed files.
    Match the file paths to the Module names in test cases. Only return matching test cases.""",
    llm=llm,
    allow_delegation=False,
)

# --- Helper Functions ---
def get_changed_files(commit_id):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{commit_id}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return [f["filename"] for f in data.get("files", [])]

def get_test_cases():
    try:
        return pd.read_excel(EXCEL_PATH)
    except FileNotFoundError:
        return pd.DataFrame()

def run_selected_tests(testcase_ids):
    for tc_id in testcase_ids:
        print(f"Running Test Case: {tc_id}")
        # Add your testing framework command here (pytest, unittest, etc.)

# --- Webhook Endpoint ---
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if "head_commit" in data:
        commit_id = data["head_commit"]["id"]
        changed_files = get_changed_files(commit_id)

        df = get_test_cases()
        if not df.empty:
            test_cases_list = df[['TC_ID', 'Module', 'Test Case']].to_dict(orient='records')

            task = Task(
                description=f"""Analyze the code changes and return ONLY the test case IDs that are directly affected.

**Changed Files:**
{json.dumps(changed_files, indent=2)}

**Available Test Cases:**
{json.dumps(test_cases_list, indent=2)}

**Instructions:**
1. Look at each changed file path
2. Extract the module/component name from the file path (e.g., "Home", "Contact", "About", etc.)
3. Match the extracted module name with the "Module" field in test cases
4. ONLY return test cases where the Module exactly matches the changed file's module
5. Return your answer as a valid Python list of TC_IDs: ["TC001", "TC002"]
6. If no test cases match, return an empty list: []
7. BE VERY SELECTIVE - only return directly related test cases

**Output Format:**
Return ONLY a Python list like this: ["TC001", "TC005"]
Do not include any other text or explanation.""",
                agent=impact_agent,
                expected_output='A Python list of TC_IDs like ["TC001", "TC005"] or [] if none match'
            )

            crew = Crew(
                agents=[impact_agent],
                tasks=[task],
                process=Process.sequential
            )

            result = crew.kickoff()

            # Simple parsing
            try:
                result_str = str(result).strip()
                # Remove any markdown code blocks
                if "```" in result_str:
                    result_str = result_str.split("```")[1]
                    if result_str.startswith("python"):
                        result_str = result_str[6:]
                    result_str = result_str.strip()

                # Parse as JSON/Python list
                selected_ids = json.loads(result_str.replace("'", '"'))

                if not isinstance(selected_ids, list):
                    selected_ids = []

            except Exception as e:
                print(f"Error parsing result: {e}")
                selected_ids = []

            run_selected_tests(selected_ids)

            return jsonify({"status": "success", "triggered_tests": selected_ids}), 200

    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
