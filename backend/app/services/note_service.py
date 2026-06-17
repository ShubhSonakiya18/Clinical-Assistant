import time
from pathlib import Path
from anthropic import Anthropic
from app.config import settings

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SOAP_TOOL = {
    "name": "generate_soap_note",
    "description": "Generate a structured clinical note from a consultation transcript.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subjective": {
                "type": "string",
                "description": (
                    "Chief complaint and history of present illness, exactly as stated. "
                    "Write 'Not documented.' if absent."
                ),
            },
            "objective": {
                "type": "string",
                "description": (
                    "Examination findings and vitals, exactly as stated. "
                    "Write 'Not documented.' if absent."
                ),
            },
            "assessment": {
                "type": "string",
                "description": (
                    "Diagnosis or clinical impression, exactly as stated by the doctor. "
                    "Write 'Not documented.' if absent."
                ),
            },
            "plan": {
                "type": "string",
                "description": (
                    "Management plan, medications, follow-up instructions, exactly as discussed. "
                    "Write 'Not documented.' if absent."
                ),
            },
            "missing_information": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Names of clinical sections that were not documented.",
            },
        },
        "required": ["subjective", "objective", "assessment", "plan", "missing_information"],
    },
}

DEFAULT_SYSTEM_PROMPT = """You are a clinical documentation assistant for Indian doctors.

Your ONLY job is to extract and organize information that was EXPLICITLY stated in the consultation transcript.

STRICT RULES — violating any of these is a critical error:
1. Never add symptoms, diagnoses, or treatments that were NOT explicitly mentioned.
2. Never infer or assume clinical information.
3. If a section has no information in the transcript, write exactly: "Not documented."
4. Use the exact medical terms the doctor used — do not paraphrase clinical details.
5. The transcript may be in Hindi, English, or Hinglish — document in English.
6. You are a scribe, not a clinician. Extract. Do not interpret.

Common Hinglish medical terms:
- "dard" = pain | "sujan" = swelling | "bukhar" = fever | "kamzori" = weakness
- "X-ray karaya" = X-ray done | "dawai likh do" = write medication

You must call the generate_soap_note tool."""


def load_system_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "v1" / "soap_generation.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return DEFAULT_SYSTEM_PROMPT


def generate_soap_note(transcript: str, patient_context: str = "") -> dict:
    start = time.time()
    user_message = (
        f"Patient context: {patient_context or 'Not provided'}\n\n"
        f"Consultation transcript:\n{transcript}"
    )

    response = client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=2048,
        temperature=0,
        system=load_system_prompt(),
        tools=[SOAP_TOOL],
        tool_choice={"type": "tool", "name": "generate_soap_note"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_use = next(b for b in response.content if b.type == "tool_use")
    note_data = tool_use.input

    return {
        "subjective": note_data.get("subjective", "Not documented."),
        "objective": note_data.get("objective", "Not documented."),
        "assessment": note_data.get("assessment", "Not documented."),
        "plan": note_data.get("plan", "Not documented."),
        "missing_information": note_data.get("missing_information", []),
        "ai_model": settings.CLAUDE_MODEL,
        "generation_time_ms": int((time.time() - start) * 1000),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "raw_response": {"stop_reason": response.stop_reason},
    }
