import os
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from natal_reader.utils.gmail_utility_with_attachment import authenticate_gmail, gmail_create_draft_with_attachment

from dotenv import load_dotenv
load_dotenv()

class GmailAttachmentToolInput(BaseModel):
    """Input schema for GmailAttachmentToolInput."""

    body: str = Field(..., description="The body of the email to send.")
    subject: str = Field(..., description="The subject of the email to send.")
    attachment_filename: str = Field(..., description="The filename of the attachment to send.")
    to: str = Field(..., description="The email address of the recipient.")

class GmailAttachmentTool(BaseTool):
    name: str = "GmailAttachmentTool"
    description: str = (
        "Send an email using the provided subject, body, and attachment filename"
    )
    args_schema: Type[BaseModel] = GmailAttachmentToolInput

    def _run(self, body: str, subject: str, attachment_filename: str, to: str) -> str:
        try:
            service = authenticate_gmail()
            sender = os.getenv("SENDER_EMAIL")
            subject = subject
            draft = gmail_create_draft_with_attachment(sender, to, subject, body, attachment_filename)

            if draft:
                return f"Email draft created successfully! Draft ID: {draft['id']}"
            else:
                return "Email draft creation failed."

        except Exception as e:
            return f"An error occurred: {e}"
        
if __name__ == "__main__":
    gmail_tool = GmailAttachmentTool()

    report = "/home/j/ai/crewAI/finance/stock_analyser/final_reports/2025-03-12/MSFT_Stock_Analysis_Report_20250312_132728.md"
    report_pdf = "/home/j/ai/crewAI/finance/stock_analyser/final_reports/2025-03-12/MSFT_Stock_Analysis_Report_20250312_132728.pdf"

    with open(report, "r") as file:
        body = file.read()

    print(gmail_tool.run(body=body, subject="Test Email", attachment_filename=report_pdf))
        