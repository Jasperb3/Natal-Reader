import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from natal_reader.tools.google_search_tool import GoogleSearchTool
from natal_reader.tools.gemini_search_tool import GeminiSearchTool
from natal_reader.tools.qdrant_search_tool import QdrantSearchTool
from natal_reader.tools.linkup_search_tool import LinkUpSearchTool
from natal_reader.utils.constants import TIMESTAMP
from dotenv import load_dotenv

load_dotenv()

google_search_tool = GoogleSearchTool(api_key=os.getenv("GOOGLE_SEARCH_API_KEY"), cx=os.getenv("SEARCH_ENGINE_ID"))

gemini_flash = LLM(
	model="gemini/gemini-2.5-flash-preview-04-17",
	api_key = os.getenv("GEMINI_API_KEY"),
	temperature=0.7,
	timeout=600
)

@CrewBase
class GeminiAnalysisCrew():
    """GeminiAnalysisCrew crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def natal_chart_interpreter(self) -> Agent:
        return Agent(
			config=self.agents_config['natal_chart_interpreter'],
			tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool(), LinkUpSearchTool()],
			llm=gemini_flash,
			verbose=True
		)

    @agent
    def natal_report_writer(self) -> Agent:
        return Agent(
			config=self.agents_config['natal_report_writer'],
			tools=[google_search_tool, GeminiSearchTool(), QdrantSearchTool(), LinkUpSearchTool()],
			llm=gemini_flash,
			verbose=True
		)

    @task
    def natal_chart_interpretation_task(self) -> Task:
        return Task(
			config=self.tasks_config['natal_chart_interpretation_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/gemini_natal_chart_interpretation_task.md"
		)

    @task
    def natal_report_writing_task(self) -> Task:
        return Task(
			config=self.tasks_config['natal_report_writing_task'],
			output_file=f"crew_outputs/{TIMESTAMP}/gemini_natal_report_writing_task.md"
		)

    @crew
    def crew(self) -> Crew:
        """Creates the GeminiAnalysisCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
