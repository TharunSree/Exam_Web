# core/ai_utils.py

import google.generativeai as genai
from django.conf import settings
import json


def generate_quiz_questions(exam_name, subject, description, num_questions, difficulty="Medium", custom_material=None):
    """
    Generates a quiz, giving priority to custom study material if provided.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.0-pro')

    # --- New section to build the prompt dynamically ---
    prompt_parts = [
        f"**Role**: You are an expert question paper setter for competitive entrance examinations.",
        f"**Task**: Generate a high-quality, multiple-choice quiz based on the provided details.",
        f"**Exam Details**:",
        f"* **Exam Name**: {exam_name}",
        f"* **Subject**: {subject}",
        f"* **Difficulty Level**: {difficulty}",
        f"* **Number of Questions**: {num_questions}",
    ]

    # If custom material is provided, add it to the prompt and prioritize it
    if custom_material:
        prompt_parts.extend([
            "---",
            "**Primary Source Material (Prioritize this content)**:",
            "The following text is from the user's uploaded study material. You MUST generate questions based primarily on this content, while keeping the exam's style and difficulty in mind.",
            f"```text\n{custom_material}\n```",
            "---",
        ])
    else:
        prompt_parts.append(f"**Exam Description for Context**: {description}")

    prompt_parts.extend([
        "**JSON Output Instructions (VERY IMPORTANT)**:",
        "You MUST return a single, valid JSON object with three top-level keys: `passage`, `chart_data`, and `questions`.",
        # (The rest of the JSON instructions and examples for VARC, DILR, and QA remain the same)
    ])

    prompt = "\n".join(prompt_parts)
    # --- End of dynamic prompt building ---

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"An error occurred during AI generation: {e}")
        return None