from pydantic import BaseModel, Field
from datetime import datetime
from natal_reader.utils.subject_selection import get_subject_data

subject_data = get_subject_data()

class NatalState(BaseModel):
    name: str = subject_data["name"]
    email: str = subject_data["email"]
    date_of_birth: datetime = datetime.strptime(subject_data["date_of_birth"], "%Y-%m-%d %H:%M:%S")
    dob: str = datetime.strftime(date_of_birth, "%H:%M %A, %d %B %Y")
    birthplace: str = f"{subject_data['birthplace']['place']}, {subject_data['birthplace']['country']}"
    birthplace_city: str = subject_data["birthplace"]["place"]
    birthplace_country: str = subject_data["birthplace"]["country"]
    birthplace_latitude: float = subject_data["birthplace"]["latitude"]
    birthplace_longitude: float = subject_data["birthplace"]["longitude"]
    birthplace_timezone: str = subject_data["birthplace"]["timezone"]
    today: str = datetime.now().strftime("%A, %d %B %Y")
    natal_chart: str = ""
    kerykeion_natal_chart_png: str = ""
    gpt_natal_analysis: str = ""
    gemini_natal_analysis: str = ""
    merged_natal_analysis: str = ""
    final_natal_analysis: str = ""
    report_markdown: str = ""
    report_pdf: str = ""


class Email(BaseModel):
    subject: str = Field(description="The subject of the email.")
    body: str = Field(description="The body of the email.")
