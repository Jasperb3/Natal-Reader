import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from natal_reader.tools.gmail_tool_with_attachment import GmailAttachmentTool
from natal_reader.utils.models import Email
from dotenv import load_dotenv

load_dotenv()


gpt56_terra = LLM(
	model="gpt-5.6-terra",
	api_key = os.getenv("OPENAI_API_KEY"),
	reasoning_effort="medium"
)

gpt56_luna = LLM(
	model="gpt-5.6-luna",
	api_key = os.getenv("OPENAI_API_KEY"),
	reasoning_effort="low"
)

gpt41mini = LLM(
	model="gpt-4.1-mini",
	api_key = os.getenv("OPENAI_API_KEY"),
	temperature=0.7
)

@CrewBase
class GmailCrew():
	"""GmailCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def email_writing_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['email_writing_agent'],
			llm=gpt56_terra,
			verbose=True
)

	@agent
	def gmail_draft_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['gmail_draft_agent'],
			tools=[GmailAttachmentTool()],
			llm=gpt56_luna,
			verbose=True
)

	@task
	def email_writing_task(self) -> Task:
		return Task(
			config=self.tasks_config['email_writing_task'],
			output_pydantic=Email
		)

	@task
	def gmail_draft_task(self) -> Task:
		return Task(
			config=self.tasks_config['gmail_draft_task']
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the GmailCrew crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			cache=True
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
