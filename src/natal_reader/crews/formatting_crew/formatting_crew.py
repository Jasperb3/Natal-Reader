import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from natal_reader.utils.constants import TIMESTAMP
from dotenv import load_dotenv

load_dotenv()

# Use a smaller, cheaper model for pure formatting tasks
gpt41mini = LLM(
	model="gpt-4.1-mini",
	api_key = os.getenv("OPENAI_API_KEY"),
	temperature=0.3  # Low temperature for precise formatting
)


@CrewBase
class FormattingCrew():
	"""Formatting crew for HTML markup of reports"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'


	@agent
	def markdown_enhancer(self) -> Agent:
		return Agent(
			config=self.agents_config['markdown_enhancer'],
			llm=gpt41mini,
			verbose=True
		)


	@task
	def markdown_enhancement_task(self) -> Task:
		return Task(
			config=self.tasks_config['markdown_enhancement_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/tagged_markdown.md"
		)


	@crew
	def crew(self) -> Crew:
		"""Creates the FormattingCrew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
		)
