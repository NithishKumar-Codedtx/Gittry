from crewai import Agent
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

testcase_mapper_agent = Agent(
    name="Test Case Mapper",
    role="Test Case Mapping Specialist",
    goal="Map code changes to relevant test cases.",
    backstory="An AI agent that excels at finding relationships between code and test cases.",
    llm=llm,
    allow_delegation=False,
)
