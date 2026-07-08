from pydantic import BaseModel, Field
from datetime import datetime


class NatalState(BaseModel):
    name: str = ""
    email: str = ""
    date_of_birth: datetime = datetime(1970, 1, 1)
    dob: str = ""
    time_known: bool = True
    birthplace: str = ""
    birthplace_city: str = ""
    birthplace_country: str = ""
    birthplace_latitude: float = 0.0
    birthplace_longitude: float = 0.0
    birthplace_timezone: str = ""
    today: str = ""
    natal_chart: str = ""
    chart_facts: dict = {}
    kerykeion_natal_chart_png: str = ""
    natal_analysis: str = ""
    final_natal_analysis: str = ""
    report_markdown: str = ""
    report_pdf: str = ""
    total_token_usage: int = 0

    @classmethod
    def from_subject(cls, subject_data: dict) -> "NatalState":
        date_of_birth = datetime.strptime(subject_data["date_of_birth"], "%Y-%m-%d %H:%M:%S")
        return cls(
            name=subject_data["name"],
            email=subject_data.get("email", ""),
            date_of_birth=date_of_birth,
            dob=datetime.strftime(date_of_birth, "%H:%M %A, %d %B %Y"),
            time_known=subject_data.get("time_known", True),
            birthplace=f"{subject_data['birthplace']['place']}, {subject_data['birthplace']['country']}",
            birthplace_city=subject_data["birthplace"]["place"],
            birthplace_country=subject_data["birthplace"]["country"],
            birthplace_latitude=subject_data["birthplace"]["latitude"],
            birthplace_longitude=subject_data["birthplace"]["longitude"],
            birthplace_timezone=subject_data["birthplace"]["timezone"],
            today=datetime.now().strftime("%A, %d %B %Y"),
        )


class Email(BaseModel):
    subject: str = Field(description="The subject of the email.")
    body: str = Field(description="The body of the email.")
