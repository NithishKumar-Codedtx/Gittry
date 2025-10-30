from crewai import Agent
from langchain_openai import ChatOpenAI
import os

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

code_analyzer_agent = Agent(
    name="Code Analyzer",
    role="Code Analysis Expert",
    goal="Analyze the provided code changes for potential impacts.",
    backstory="An AI agent that specializes in understanding code and its implications.",
    llm=llm,
    allow_delegation=False,
)
