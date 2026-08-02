"""
prompts/mood_prompt.py – Mood-analysis prompt templates.
"""

MOOD_ANALYSIS_PROMPT = """
Analyse the following text written by an elderly person and determine their
current emotional state.

TEXT: "{text}"

Respond ONLY with a valid JSON object (no markdown, no explanation) in this
exact format:
{{
  "mood": "<one of: happy, content, neutral, anxious, lonely, sad, confused, angry, depressed>",
  "mood_score": <integer 1-10 where 10=very happy, 1=very depressed>,
  "triggers": "<brief phrase about what may be causing this mood>",
  "suggestions": "<2-3 warm, actionable suggestions to improve wellbeing>",
  "needs_attention": <true if score <= 3 or mood is depressed, else false>
}}
"""


def build_mood_prompt(text: str) -> str:
    return MOOD_ANALYSIS_PROMPT.format(text=text.replace('"', "'"))
