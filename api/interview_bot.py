import anthropic

COMPLETION_CODE = "x7y8"
SAFETY_CODE = "5j3k"

DEFAULT_GENERAL_INSTRUCTIONS = """
You are an expert qualitative research interviewer. Follow these principles:

1. Ask one question at a time. Wait for the respondent's answer before moving on.
2. Use open-ended questions. Avoid yes/no questions when possible.
3. Listen actively: acknowledge what the respondent says before transitioning.
4. Use neutral, non-leading language. Do not suggest answers.
5. Probe for depth: ask follow-up questions like "Can you tell me more about that?" or "What do you mean by...?"
6. Stay flexible: if the respondent brings up something relevant, explore it before returning to the script.
7. Keep a warm, conversational, and professional tone.
8. Do not repeat questions that have already been thoroughly answered.
9. Track which topics have been covered and which remain.
10. When all questions have been sufficiently addressed, provide a brief summary of the key points discussed and ask the respondent if they want to add anything.
""".strip()

CLOSING_MESSAGE_COMPLETE = "Thank you very much for participating in this interview. Your responses have been recorded and will be very valuable for our research. You may now close this window."
CLOSING_MESSAGE_SAFETY = "Thank you for your time. The interview has ended. You may now close this window."


def build_system_prompt(study):
    instructions = study.get("general_instructions") or DEFAULT_GENERAL_INSTRUCTIONS

    return f"""You are conducting a qualitative research interview.

## Research Context
The research question guiding this study is: {study['research_question']}

## Interview Outline
Follow this interview script, adapting your questions based on the respondent's answers:

{study['interview_outline']}

## General Instructions
{instructions}

## Termination Codes
- When you have asked all questions and the interview is complete, end your FINAL message with the code: {COMPLETION_CODE}
- If the respondent posts clearly problematic, offensive, or unethical content, end your message with the code: {SAFETY_CODE}

IMPORTANT: Only include a termination code when the condition is truly met. The code must appear at the very end of your message, on its own line. Do not mention these codes to the respondent."""


def stream_response(study, messages, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(study)
    model = study.get("model", "claude-sonnet-4-20250514")

    api_messages = []
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    with client.messages.stream(
        model=model,
        max_tokens=2048,
        system=system_prompt,
        messages=api_messages,
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            full_text += text
            if COMPLETION_CODE in full_text:
                clean = full_text.replace(COMPLETION_CODE, "").strip()
                yield {"type": "text", "content": text.replace(COMPLETION_CODE, "")}
                yield {"type": "done", "code": "complete", "closing": CLOSING_MESSAGE_COMPLETE}
                return
            if SAFETY_CODE in full_text:
                yield {"type": "done", "code": "safety", "closing": CLOSING_MESSAGE_SAFETY}
                return
            yield {"type": "text", "content": text}
        yield {"type": "done", "code": None, "closing": None}


def get_first_message(study, api_key):
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(study)
    model = study.get("model", "claude-sonnet-4-20250514")

    with client.messages.stream(
        model=model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": "Hello, I'm ready to start the interview."}],
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            full_text += text
            yield text
    return full_text
