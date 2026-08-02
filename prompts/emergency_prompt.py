"""
prompts/emergency_prompt.py – Emergency response prompt templates.
"""

EMERGENCY_RESPONSE_PROMPT = """
A CareCompanion user has triggered an emergency alert.
Emergency type: {emergency_type}
Severity: {severity}
User's exact words: "{trigger_text}"
User name: {user_name}

Write a calm, clear, compassionate emergency response message that:
1. Acknowledges what the user said
2. Instructs them to stay calm and stay still if possible
3. Tells them help is being contacted
4. Gives one immediate safety instruction relevant to their emergency type
5. Keeps it SHORT (under 60 words) — they may be in distress

Respond in: {language}
"""


def build_emergency_prompt(emergency_type: str, severity: str,
                            trigger_text: str, user_name: str,
                            language: str = "English") -> str:
    return EMERGENCY_RESPONSE_PROMPT.format(
        emergency_type=emergency_type,
        severity=severity,
        trigger_text=trigger_text,
        user_name=user_name,
        language=language,
    )
