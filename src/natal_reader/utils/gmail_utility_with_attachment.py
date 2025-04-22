import base64
import mimetypes
import os
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders  # Import the encoders module

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import markdown


SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def authenticate_gmail():
    """
    Authenticate and return an authorized Gmail API service instance.
    Expects credentials.json and token.json in the same directory as this script.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(current_dir, 'token.json')
    credentials_path = os.path.join(current_dir, 'credentials.json')
    
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_path}. "
                    "Download OAuth 2.0 credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
    
    service = build('gmail', 'v1', credentials=creds)
    return service

def gmail_create_draft_with_attachment(sender: str, to: str, subject: str, markdown_text: str, attachment_filename: str) -> dict:
    """
    Create and insert a draft email with attachment.

    Args:
        sender: The email address of the sender.
        to: The email address of the recipient.
        subject: The subject of the email.
        markdown_text: The body of the email in markdown format.
        attachment_filename: The full path to the attachment file.

    Returns:
        Draft object, including draft id and message meta data, or None if an error occurs.
    """
    try:
        service = authenticate_gmail()  # Use the authentication function

        # Convert markdown to HTML
        md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        html_content = md.convert(markdown_text)

        # Wrap the converted HTML in a full HTML document
        html = f"""\
<html>
  <head>
    <style>
      body {{
          font-family: Arial, sans-serif;
          line-height: 1.6;
          color: #333;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
      }}
      h1 {{
          color: #2c3e50;
          border-bottom: 2px solid #eee;
          padding-bottom: 10px;
      }}
    </style>
  </head>
  <body>
    {html_content}
  </body>
</html>
"""
        # Create a multipart message
        message = MIMEMultipart()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = to

        # Attach the HTML content as the main part
        message.attach(MIMEText(html, "html"))

        # Attachment handling
        content_type, encoding = mimetypes.guess_type(attachment_filename)
        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)

        try:
            with open(attachment_filename, "rb") as fp:
                if main_type == "text":
                    msg = MIMEText(fp.read().decode(), _subtype=sub_type)
                elif main_type == "image":
                    msg = MIMEImage(fp.read(), _subtype=sub_type)
                elif main_type == "audio":
                    msg = MIMEAudio(fp.read(), _subtype=sub_type)
                else:
                    msg = MIMEBase(main_type, sub_type)
                    file_content = fp.read()  # Read as bytes
                    msg.set_payload(file_content)
                    # Encode the payload correctly for binary data
                    encoders.encode_base64(msg) # Correct way to encode base64

                filename = os.path.basename(attachment_filename)
                msg.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(msg)
        except FileNotFoundError:
            print(f"Warning: Could not find attachment file: {attachment_filename}")
            #  Continue creating the draft *without* the attachment
        except Exception as e:
            print(f"An unexpected error occurred while processing the attachment: {e}")
            return None


        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_draft_request_body = {"message": {"raw": encoded_message}}
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body=create_draft_request_body)
            .execute()
        )
        print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')
        return draft

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def create_draft(service, user_id: str, message_body: dict) -> dict:
    """
    Create and insert a draft email using the Gmail API.  (Moved from gmail_utility_inline_images_bup.py)

    Args:
        service: Authorized Gmail API service instance
        user_id: User's email address or 'me'
        message_body: Dict containing the raw base64url encoded message

    Returns:
        Created draft object or None if error occurs
    """
    try:
        draft = service.users().drafts().create(
            userId=user_id,
            body={'message': message_body}
        ).execute()
        print(f"Draft id: {draft['id']}")
        return draft
    except Exception as error:
        print(f"An error occurred while creating draft: {error}")
        return None


# Removed the build_file_part function as it's now integrated into gmail_create_draft_with_attachment

if __name__ == "__main__":
    # Example Usage (replace with your actual values)
    sender_email = os.getenv("SENDER_EMAIL")  # Replace with your sender email
    recipient_email = os.getenv("SENDER_EMAIL")  # Replace with recipient email
    test_subject = "Test Email with Attachment and HTML"
    test_markdown = """
# This is a test email

This email includes:

*   A list
*   Some **bold** text
*   A [link](https://www.google.com)
    """
    test_attachment = "/home/j/ai/crewAI/finance/stock_analyser/final_reports/2025-03-17/SOUN_Stock_Analysis_Report_20250317_183922_orig.pdf"  # Replace with your attachment path

    # You'll need a credentials.json file for authentication.
    # See the Google API documentation for how to obtain this.

    if not os.path.exists(test_attachment):
        print("Creating dummy attachment file...")
        with open(test_attachment, "w") as f:
            f.write("Dummy PDF content")

    draft = gmail_create_draft_with_attachment(
        sender_email, recipient_email, test_subject, test_markdown, test_attachment
    )

    if draft:
        print(f"Draft created successfully! Draft ID: {draft['id']}")