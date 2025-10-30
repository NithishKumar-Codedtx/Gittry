import os
import requests
import pandas as pd
import json
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
# Replace with a specific commit hash you want to analyze
COMMIT_ID = "e0ecb123405a434b2063eb4a0c2278f8aae57318"  # Try a different commit
GITHUB_REPO = "Nithishrish23/Nithish-portfolio"
TOKEN = os.getenv("GITHUB_TOKEN")
EXCEL_PATH = "test_cases/Nithish_Portfolio_TestCases.xlsx"

# Configure OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Initialize OpenAI LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY
)

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
    verbose=True
)

# --- Helper Functions ---
def get_changed_files(commit_id):
    """Fetches the list of changed files for a given commit."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{commit_id}"
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"\nError fetching commit: Status {response.status_code}")
        print(f"Response: {response.text}")
        # Try alternative auth format
        headers = {"Authorization": f"token {TOKEN}"}
        response = requests.get(url, headers=headers)

    response.raise_for_status()
    data = response.json()
    files = [f["filename"] for f in data.get("files", [])]

    if not files:
        print("\nWarning: No files found in commit. This might be:")
        print("  - An empty commit")
        print("  - A merge commit")
        print("  - An invalid commit ID")

    return files

def get_test_cases():
    """Reads test cases from the Excel file."""
    try:
        return pd.read_excel(EXCEL_PATH)
    except FileNotFoundError:
        print(f"Error: Test case file not found at {EXCEL_PATH}")
        return pd.DataFrame()

def run_selected_tests(testcase_ids):
    """Simulates running selected test cases."""
    if not testcase_ids:
        print("\nNo test cases were identified for execution.")
        return
    print("\n" + "="*50)
    print("SELECTED TEST CASES TO RUN")
    print("="*50)
    for tc_id in testcase_ids:
        print(f"  - {tc_id}")
    print("="*50)

# --- Main Execution ---
def main():
    """Main function to run the analysis."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY is not set. Please add it to your .env file.")
        return

    if not TOKEN:
        print("Error: GITHUB_TOKEN is not set. Please add it to your .env file.")
        return

    print(f"\nAnalyzing commit: {COMMIT_ID}")
    print(f"Repository: {GITHUB_REPO}\n")

    try:
        changed_files = get_changed_files(COMMIT_ID)
    except Exception as e:
        print(f"Error fetching from GitHub: {e}")
        print("\n" + "="*50)
        print("Using TEST MODE with example files")
        print("="*50)
        # Example files for testing - Uncomment scenarios you want to test:

        # Scenario 1: Homepage change
        changed_files = ["index.html", "styles/home.css"]

        # Scenario 2: Contact form change
        # changed_files = ["src/components/contact.jsx", "contact.html"]

        # Scenario 3: API routes change
        # changed_files = ["server/routes/api.js", "backend/server.js"]

        # Scenario 4: Global style change (affects all modules)
        # changed_files = ["styles/global.css", "app.css"]

        # Scenario 5: Mixed changes
        # changed_files = ["index.html", "contact.html", "server/api.js"]

    print(f"\nChanged files detected:")
    for file in changed_files:
        print(f"  - {file}")

    df = get_test_cases()
    if df.empty:
        return

    print(f"\nTotal test cases available: {len(df)}")

    # Prepare context for the agent
    test_cases_list = df[['TC_ID', 'Module', 'Test Case']].to_dict(orient='records')

    # Get unique modules
    unique_modules = df['Module'].unique().tolist()

    task = Task(
        description=f"""Analyze the code changes and return ONLY the test case IDs that are directly affected.

**Changed Files:**
{json.dumps(changed_files, indent=2)}

**Available Modules in Test Cases:**
{json.dumps(unique_modules, indent=2)}

**All Test Cases with Their Modules:**
{json.dumps(test_cases_list, indent=2)}

**Matching Rules & Examples:**

1. **Homepage/Landing Page files** → "Homepage" module
   - index.html, home.html, landing.html
   - home.jsx, Home.jsx, homepage.js
   - main.js, app.js (only if they're main entry files)
   - ANY file in folders: /home, /landing, /index
   - Return test cases where Module = "Homepage"

2. **Contact files** → "Contact Form" module
   - contact.html, contact-form.html
   - contact.jsx, Contact.jsx, ContactForm.jsx
   - ANY file in folders: /contact
   - Return test cases where Module = "Contact Form"

3. **API/Routes/Backend files** → "API Routes" module
   - ANY file in folders: /routes, /api, /backend, /server
   - server.js, routes.js, api.js
   - Return test cases where Module = "API Routes"

4. **Performance/Config/Build files** → "Performance" module
   - webpack.config.js, package.json, .babelrc
   - ANY file in folders: /config, /build
   - Return test cases where Module = "Performance"

5. **Global CSS/Shared files** → ALL modules
   - global.css, app.css, main.css, reset.css
   - Return test cases for ALL modules

6. **Specific module CSS** → That specific module only
   - home.css → "Homepage"
   - contact.css → "Contact Form"

7. **Test/Example/Random files** → IGNORE (return empty list)
   - sample.py, test.py, example.js, demo.html
   - ANY file with names: sample, test, demo, example, temp
   - Return [] (empty list)

**Your Task:**
1. Check if file should be IGNORED (rule 7) - if yes, return []
2. Check if file is GLOBAL (rule 5) - if yes, return ALL test cases
3. Match file to specific module (rules 1-4, 6)
4. Look at the file path and file name carefully
5. If you cannot determine the module, return [] instead of guessing

**Output Format:**
Return ONLY a Python list: ["TC_HP_001", "TC_CF_001"]
No explanations, just the list.""",
        agent=impact_agent,
        expected_output='A Python list of TC_IDs like ["TC_HP_001", "TC_CF_001"]'
    )

    crew = Crew(
        agents=[impact_agent],
        tasks=[task],
        process=Process.sequential
    )

    print("\n" + "="*50)
    print("RUNNING AI ANALYSIS...")
    print("="*50)

    result = crew.kickoff()

    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print(f"\nRaw AI output:\n{result}\n")

    # Simple parsing - expect a Python list format
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
        print("Expected format: ['TC001', 'TC005']")
        selected_ids = []

    run_selected_tests(selected_ids)

    # Show summary
    if selected_ids:
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        selected_tests = df[df['TC_ID'].isin(selected_ids)]
        print(f"\nTotal selected test cases: {len(selected_ids)}")
        print(f"Affected modules:")
        for module in selected_tests['Module'].unique():
            count = len(selected_tests[selected_tests['Module'] == module])
            print(f"  - {module}: {count} test(s)")
        print("="*50)

if __name__ == '__main__':
    main()
