import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from natal_reader.tools.google_search_tool import GoogleSearchTool
from natal_reader.tools.gemini_search_tool import GeminiSearchTool
from natal_reader.tools.qdrant_search_tool import QdrantSearchTool
from natal_reader.utils.constants import TIMESTAMP
from dotenv import load_dotenv

load_dotenv()

google_search_tool = GoogleSearchTool(api_key=os.getenv("GOOGLE_SEARCH_API_KEY"), cx=os.getenv("SEARCH_ENGINE_ID"))

# Precise temperature for technical interpretation
gpt41_precise = LLM(
	model="gpt-4.1",
	api_key = os.getenv("OPENAI_API_KEY"),
	temperature=0.4
)

# Creative temperature for narrative writing
gpt41_creative = LLM(
	model="gpt-4.1",
	api_key = os.getenv("OPENAI_API_KEY"),
	temperature=0.75
)


@CrewBase
class AnalysisCrew():
	"""Single optimized natal chart analysis crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'


	@agent
	def natal_chart_interpreter(self) -> Agent:
		return Agent(
			config=self.agents_config['natal_chart_interpreter'],
			tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool()],
			llm=gpt41_precise,
			verbose=True
		)

	@agent
	def natal_report_writer(self) -> Agent:
		return Agent(
			config=self.agents_config['natal_report_writer'],
			tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool()],
			llm=gpt41_creative,
			verbose=True
		)


	@task
	def natal_chart_interpretation_task(self) -> Task:
		return Task(
			config=self.tasks_config['natal_chart_interpretation_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/natal_chart_interpretation_task.md"
		)

	@task
	def natal_report_writing_task(self) -> Task:
		return Task(
			config=self.tasks_config['natal_report_writing_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/natal_report_writing_task.md"
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the optimized AnalysisCrew"""
		return Crew(
			agents=self.agents,
			tasks=self.tasks,
			process=Process.sequential,
			verbose=True
		)
