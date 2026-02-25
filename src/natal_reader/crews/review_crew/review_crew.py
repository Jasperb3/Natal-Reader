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

gemini_flash = LLM(
	model="gemini/gemini-3-flash-preview",
	api_key = os.getenv("GEMINI_API_KEY"),
	temperature=0.7,
	timeout=600
)

gemini_pro = LLM(
	model="gemini/gemini-3.1-pro-preview",
	api_key = os.getenv("GEMINI_API_KEY"),
	temperature=0.7,
	timeout=600
)

deepseek = LLM(
	model="deepseek/deepseek-reasoner",
	api_key = os.getenv("DEEPSEEK_API_KEY"),
	temperature=0.7,
	timeout=600
)

@CrewBase
class ReviewCrew():
	"""ReviewCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	# If you would like to add tools to your agents, you can learn more about it here:
	# https://docs.crewai.com/concepts/agents#agent-tools
	@agent
	def critic(self) -> Agent:
		return Agent(
			config=self.agents_config['critic'],
			llm=gemini_pro,
			verbose=True
		)

	@agent
	def report_enhancer(self) -> Agent:
		return Agent(
			config=self.agents_config['report_enhancer'],
			llm=gemini_pro,
			tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool()],
			verbose=True
		)

	@task
	def review_task(self) -> Task:
		return Task(
			config=self.tasks_config['review_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/critique.md"
		)

	@task
	def report_enhancement_task(self) -> Task:
		return Task(
			config=self.tasks_config['report_enhancement_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/enhanced_report.md"
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the ReviewCrew crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True
		)
