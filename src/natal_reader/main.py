import os
import json
import time
from datetime import datetime
from crewai.flow import Flow, listen, start
from natal_reader.utils.models import NatalState
from natal_reader.utils.qdrant_setup import Setup
from natal_reader.utils.decorators import track_token_usage, timeit, timings_file_path
from natal_reader.utils.immanuel_natal_chart import get_natal_chart
from natal_reader.utils.kerykeion_chart_utils import get_kerykeion_subject, get_kerykeion_natal_chart
from natal_reader.utils.convert_to_pdf import convert_md_to_pdf
from natal_reader.utils.constants import TIMESTAMP, CHARTS_DIR, NOW_DT, OUTPUT_DIR
from natal_reader.crews.gpt_analysis_crew.gpt_analysis_crew import GPTAnalysisCrew
from natal_reader.crews.gemini_analysis_crew.gemini_analysis_crew import GeminiAnalysisCrew
from natal_reader.crews.review_crew.review_crew import ReviewCrew
from natal_reader.crews.gmail_crew.gmail_crew import GmailCrew
from natal_reader.crews.merge_crew.merge_crew import MergeCrew

beginning_time = time.time()

class NatalFlow(Flow[NatalState]):

    @timeit
    @start()
    def setup_qdrant(self):
        print("Setting up Qdrant")
        setup = Setup(self.state)
        setup.process_new_markdown_files()
        return


    @timeit
    @listen(setup_qdrant)
    def get_natal_chart_data(self):
        print("Getting natal chart data")
        natal_chart = get_natal_chart(self.state.date_of_birth, self.state.birthplace_latitude, self.state.birthplace_longitude)
        self.state.natal_chart = natal_chart
        return


    @timeit
    @track_token_usage
    @listen(get_natal_chart_data)
    def generate_gpt_natal_analysis(self):
        print("Generating GPT natal analysis")

        inputs = {
            "name": self.state.name,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace,
            "today": self.state.today,
            "natal_chart": self.state.natal_chart
        }

        gpt_natal_analysis = (
            GPTAnalysisCrew()
            .crew()
            .kickoff(inputs=inputs)
        )

        print("Natal analysis generated")
        self.state.gpt_natal_analysis = gpt_natal_analysis.raw

        return gpt_natal_analysis


    @timeit
    @track_token_usage
    @listen(generate_gpt_natal_analysis)
    def generate_gemini_natal_analysis(self):
        print("Generating Gemini natal analysis")

        inputs = {
            "name": self.state.name,
            "natal_chart": self.state.natal_chart,
            "today": self.state.today,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace
        }

        gemini_natal_analysis = (
            GeminiAnalysisCrew()
            .crew()
            .kickoff(inputs=inputs)
        )

        print("Gemini natal analysis generated")
        self.state.gemini_natal_analysis = gemini_natal_analysis.raw

        return gemini_natal_analysis
    

    @timeit
    @track_token_usage
    @listen(generate_gemini_natal_analysis)
    def merge_natal_analyses(self):
        print("Merging natal analyses")

        inputs = {
            "name": self.state.name,
            "gpt_natal_analysis": self.state.gpt_natal_analysis,
            "gemini_natal_analysis": self.state.gemini_natal_analysis,
            "today": self.state.today,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace
        }

        merged_natal_analysis = (
            MergeCrew()
            .crew()
            .kickoff(inputs=inputs)
        )

        print("Merged natal analysis generated")
        self.state.merged_natal_analysis = merged_natal_analysis.raw

        return merged_natal_analysis


    @timeit
    @track_token_usage
    @listen(merge_natal_analyses)
    def review_merged_natal_analysis(self):
        print("Reviewing merged natal analysis")

        inputs = {
            "name": self.state.name,
            "report": self.state.merged_natal_analysis,
            "today": self.state.today,
            "date_of_birth": self.state.dob,
            "place_of_birth": self.state.birthplace
        }

        enhanced_natal_analysis = (
            ReviewCrew()
            .crew()
            .kickoff(inputs=inputs)
        )

        print("Natal analysis enhanced")
        self.state.final_natal_analysis = enhanced_natal_analysis.raw

        return enhanced_natal_analysis


    @timeit
    @listen(review_merged_natal_analysis)
    def get_kerykeion_natal_chart(self):
        print("Creating Kerykeion natal chart PNG")
        kerykeion_subject = get_kerykeion_subject(self.state.name, self.state.date_of_birth.year, self.state.date_of_birth.month, self.state.date_of_birth.day, self.state.date_of_birth.hour, self.state.date_of_birth.minute, self.state.birthplace_city, self.state.birthplace_country, self.state.birthplace_longitude, self.state.birthplace_latitude, self.state.birthplace_timezone)
        kerykeion_natal_chart = get_kerykeion_natal_chart(kerykeion_subject, CHARTS_DIR)
        self.state.kerykeion_natal_chart_png = kerykeion_natal_chart
        return


    @timeit
    @listen(get_kerykeion_natal_chart)
    def save_natal_analysis(self):
        print("Saving natal analysis")
        markdown_file_path = OUTPUT_DIR / f"{self.state.name.replace(' ', '_')}_{TIMESTAMP}.md"

        self.state.final_natal_analysis = self.state.final_natal_analysis.replace("[natal_chart]", f"![Natal Chart]({self.state.kerykeion_natal_chart_png})")
        with open(markdown_file_path, "w") as f:
            f.write(self.state.final_natal_analysis)

        self.state.report_markdown = markdown_file_path
        print(f"Report markdown saved to {markdown_file_path}")

        pdf_file_path = convert_md_to_pdf(markdown_file_path)
        self.state.report_pdf = pdf_file_path
        print(f"Report pdf saved to {pdf_file_path}")
        return


    @timeit
    @track_token_usage
    @listen(save_natal_analysis)
    def send_natal_analysis(self):
        print("Drafting email...")

        try:
            token_file_path = "src/natal_reader/utils/token.json"
            with open(token_file_path, "r") as f:
                token_data = json.load(f)
                expiry_date = token_data.get("expiry")
                if expiry_date:
                    expiry_date = datetime.fromisoformat(expiry_date)
                    if expiry_date < NOW_DT:
                        print("Token expired. Re-authentication required.")
                        os.remove(token_file_path)

        except FileNotFoundError:
            print("Token file not found. Re-authentication required.")
        except json.JSONDecodeError:
            print("Error decoding token file. Re-authentication required.")
            os.remove(token_file_path)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")


        inputs = {
            "report_text": self.state.final_natal_analysis,
            "report_pdf": str(self.state.report_pdf),
            "client": self.state.name,
            "sender": "Ben Jasper",
            "email_address": self.state.email,
            "today": self.state.today
        }

        email_result = (
            GmailCrew()
            .crew()
            .kickoff(inputs=inputs)
        )

        if email_result.raw:
            print("Email draft complete")
        else:
            print("Email draft failed")

        return email_result
    

    @listen(send_natal_analysis)
    def print_final_stats(self):
        completion_time = time.time()
        total_time = completion_time - beginning_time
        minutes, seconds = divmod(total_time, 60)
        print(f"Total time taken: {int(minutes)} minutes and {int(seconds)} seconds")

        with open(f"{timings_file_path}", "a") as f:
            f.write(f"Total time taken: {int(minutes)} minutes and {int(seconds)} seconds\n")
            f.write(f"Total tokens used: {self.state.total_token_usage:,}")
            f.write(f"Final report saved to: {str(self.state.report_pdf)}\n")
        

def kickoff():
    natal_flow = NatalFlow()
    natal_flow.kickoff()


def plot():
    natal_flow = NatalFlow()
    natal_flow.plot()


if __name__ == "__main__":
    kickoff()
