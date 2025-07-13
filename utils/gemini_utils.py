import os
import requests
import re

def analyze_email(email_body: str):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
        You are a professional AI email assistant.

        TASK:
        - Carefully analyze the following email.
        - Write a full, detailed, emotionally appropriate reply (at least 5 sentences).
        - Detect intent: reply, urgent_meeting, schedule_meeting, casual_meeting.
        - Use professional tone, show understanding and clarity.
        - NEVER only reply with short greetings or simple links.
        - If needed, include the Google Meet link in context with explanation.
        - DO NOT begin reply with "Hi" or "Dear" only — address the issue meaningfully.
        - Add meeting time if mentioned or required.

        RESPONSE FORMAT:
        Summary: <...>
        Intent: <reply | urgent_meeting | schedule_meeting | casual_meeting>
        Reply: <long-form, helpful, contextual reply>
        MeetingTime: <YYYY-MM-DD HH:MM or None>

        EMAIL:
        \"\"\"
        {email_body}
        \"\"\"
        """

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {"temperature": 0.7}
    }
    params = {"key": GEMINI_API_KEY}
    response = requests.post(url, headers=headers, params=params, json=data)

    try:
        result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("Error in Gemini response:", e)
        return "Could not summarize", "reply", "Apologies, we couldn't process your message.", None

    # Extract fields using regex
    summary = re.search(r"Summary:\s*(.*)", result_text)
    intent = re.search(r"Intent:\s*(.*)", result_text)
    reply = re.search(r"Reply:\s*(.*)", result_text)
    meeting_time = re.search(r"MeetingTime:\s*(.*)", result_text)

    return (
        summary.group(1).strip() if summary else "No summary",
        intent.group(1).strip().lower() if intent else "reply",
        reply.group(1).strip() if reply else "Thank you for your email. I'll follow up shortly.",
        meeting_time.group(1).strip() if meeting_time and meeting_time.group(1).strip().lower() != "none" else None
    )