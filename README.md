# Email Text-to-MP3 Summarization Tool

## Description

The Email Text-to-MP3 Summarization Tool is a Python application designed to summarize unread emails over a specified time interval and deliver these summaries as an MP3 file via text message. This innovative tool leverages the Google API for email access, Twilio API for sending text messages, and the ChatGPT API for generating email summaries. It's an efficient way to stay on top of your inbox without needing to manually sift through each message.

## Features

- **Email Summarization**: Summarizes your unread emails, focusing on the most recent ones based on your specified time interval.
- **MP3 Conversion**: Converts the email summaries into an easily accessible MP3 file.
- **Text Message Delivery**: Sends the MP3 file as a text message to your mobile device, allowing for convenient listening.
- **Integration with Major APIs**: Utilizes Google API for accessing emails, Twilio API for messaging services, and ChatGPT API for advanced natural language processing.

## Getting Started

### Prerequisites

- Python 3.x
- Access to Google APIs (Gmail API in particular)
- Twilio account for sending SMS
- OpenAI account for using ChatGPT API
- `pip` for installing Python packages
- `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`, `beautifulsoup4`, `gtts`, and `twilio` Python packages installed
  
Fill out the necessary API keys and user information in the provided placeholders within the script:
- Google API credentials in token.json and credentials.json.
- OpenAI API key.
- Twilio account SID, auth token, and phone numbers.
- The save path for the generated MP3 file.
- The Dropbox public link for accessing the MP3 file.

### Installation & Usage

```bash
git clone https://github.com/yourusername/email-text-to-mp3.git
cd email-text-to-mp3
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client beautifulsoup4 gtts twilio
python email_text_to_mp3_summarization.py
```



