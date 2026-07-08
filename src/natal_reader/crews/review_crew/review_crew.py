import os
import re
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tasks.task_output import TaskOutput
from natal_reader.tools.google_search_tool import GoogleSearchTool
from natal_reader.tools.gemini_search_tool import GeminiSearchTool
from natal_reader.tools.qdrant_search_tool import QdrantSearchTool
from natal_reader.utils.constants import TIMESTAMP
from dotenv import load_dotenv

load_dotenv()


def _report_enhancement_guardrail(task_output: TaskOutput) -> tuple[bool, str]:
	"""Content-integrity check for report_enhancement_task (P1-3): the enhancer's
	own instructions demand the output be at least as long as the original and
	preserve every heading, but nothing enforced that before this guardrail."""
	original_report = task_output.description.rsplit("Report:\n", 1)[-1].strip()
	enhanced = task_output.raw

	if len(enhanced) < 0.95 * len(original_report):
		return False, (
			f"Enhanced report ({len(enhanced)} chars) is shorter than 95% of the "
			f"original ({len(original_report)} chars). Re-do the enhancement without "
			"condensing or dropping any content."
		)

	original_headings = re.findall(r"^#{2,3} .+$", original_report, re.MULTILINE)
	missing_headings = [h for h in original_headings if h not in enhanced]
	if missing_headings:
		return False, f"Missing headings from the enhanced report: {missing_headings}"

	if "[natal_chart]" not in enhanced:
		return False, "The [natal_chart] placeholder is missing from the enhanced report."

	return True, enhanced

google_search_tool = GoogleSearchTool(api_key=os.getenv("GOOGLE_SEARCH_API_KEY"), cx=os.getenv("SEARCH_ENGINE_ID"))

gemini_pro = LLM(
	model="gemini/gemini-3.1-pro-preview",
	api_key = os.getenv("GEMINI_API_KEY"),
	temperature=0.7,
	timeout=600
)

# Verification is not a creative task — a lower temperature reduces the
# critic's own risk of misreading placements it's meant to be checking.
gemini_pro_precise = LLM(
	model="gemini/gemini-3.1-pro-preview",
	api_key = os.getenv("GEMINI_API_KEY"),
	temperature=0.2,
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
			llm=gemini_pro_precise,
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
			output_file=f"crew_outputs/{TIMESTAMP}/enhanced_report.md",
			guardrail=_report_enhancement_guardrail,
			guardrail_max_retries=2
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
