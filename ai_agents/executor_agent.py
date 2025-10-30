from crewai import Agent
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

executor_agent = Agent(
    name="Test Executor",
    role="Automated Test Runner",
    goal="Execute the identified test cases.",
    backstory="An AI agent responsible for triggering automated test execution.",
    llm=llm,
    allow_delegation=False,
)
