# core/ai_utils.py

import google.generativeai as genai
from django.conf import settings
import json

def generate_quiz_questions(exam_name, subject, description, num_questions, difficulty="Medium", custom_material=None):
    """
    Generates a high-quality quiz using the Gemini API with a structured JSON output.

    This version provides the AI with specific, styled JSON examples for ApexCharts
    and detailed formatting instructions for all question types.
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    # NOTE: You mentioned "gemini-2.5-pro", but as of my last update, the stable model is "gemini-1.0-pro".
    # If "2.5-pro" gives you an error, please switch back to "gemini-1.0-pro".
    model = genai.GenerativeModel('gemini-2.5-pro')

    # --- Dynamic Prompt Building ---
    prompt_parts = [
        f"**Role**: You are an expert question paper setter and data visualizer for competitive entrance examinations.",
        f"**Task**: Generate a high-quality, multiple-choice quiz based on the provided details.",
        f"**Exam Details**:",
        f"* **Exam Name**: {exam_name}",
        f"* **Subject**: {subject}",
        f"* **Difficulty Level**: {difficulty}",
        f"* **Number of Questions**: {num_questions}",
    ]

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

        "1.  **`passage` (string | null):**",
        "    * If the subject is 'Verbal Ability & Reading Comprehension', this MUST contain the full reading passage text.",
        "    * For all other subjects, this MUST be `null`.",

        "2.  **`chart_data` (object | null):**",
        "    * If the subject is 'Data Interpretation & Logical Reasoning', this MUST be a valid JSON object for the ApexCharts.js library, styled according to the examples below.",
        "    * For all other subjects, this MUST be `null`.",

        "3.  **`questions` (array of objects):**",
        "    * This MUST be a list of question objects.",
        "    * Each object MUST contain these exact keys: `question_text`, `option1`, `option2`, `option3`, `option4`, `correct_option` (correct option should be like option1, option2 or whatever the correct option is).",

        "**Content-Specific Instructions**:",
        "* **For Para-Jumble Questions (VARC):** The `question_text` MUST contain the instruction and all sentences separated by a newline character (`\\n`). The `options` must be the sequence arrangements (e.g., 'CABD').",
        "* **For Reading Comprehension (VARC):** The `passage` key must contain the passage, and the `question_text` in each question object must only be the question itself.",
        "* **For Quantitative Aptitude (QA):** All mathematical notation MUST be in LaTeX format (e.g., `$\\frac{a}{b}$`).",

        "---",
        "**CHART STYLING EXAMPLES (Use these styles for DILR)**",

        "**Bar Chart Style Example:**",
        "```json",
        "{\"chart\": {\"type\": \"bar\", \"height\": 350, \"toolbar\": {\"show\": false}}, \"plotOptions\": {\"bar\": {\"horizontal\": true}}, \"dataLabels\": {\"enabled\": false}, \"series\": [{\"name\": \"Sales\", \"data\": [400, 430, 448, 470, 540]}], \"xaxis\": {\"categories\": [\"2018\", \"2019\", \"2020\", \"2021\", \"2022\"]}, \"colors\": [\"#604ae3\"], \"grid\": {\"borderColor\": \"#f1f3fa\"}}",
        "```",

        "**Line Chart Style Example:**",
        "```json",
        "{\"chart\": {\"type\": \"line\", \"height\": 350, \"toolbar\": {\"show\": false}}, \"series\": [{\"name\": \"Visits\", \"data\": [10, 41, 35, 51, 49, 62, 69]}], \"xaxis\": {\"categories\": [\"Jan\", \"Feb\", \"Mar\", \"Apr\", \"May\", \"Jun\", \"Jul\"]}, \"stroke\": {\"curve\": \"smooth\", \"width\": 2}, \"colors\": [\"#604ae3\"], \"markers\": {\"size\": 4}}",
        "```",

        "**Pie Chart (Donut) Style Example:**",
        "```json",
        "{\"chart\": {\"type\": \"donut\", \"height\": 350}, \"series\": [44, 55, 41, 17], \"labels\": [\"Product A\", \"Product B\", \"Product C\", \"Product D\"], \"colors\": [\"#604ae3\", \"#ff7f5b\", \"#25c2e3\", \"#fdc240\"], \"legend\": {\"position\": \"bottom\"}, \"responsive\": [{\"breakpoint\": 480, \"options\": {\"chart\": {\"width\": 200}, \"legend\": {\"position\": \"bottom\"}}}]}",
        "```",
        "---"
    ])

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"An error occurred during AI generation: {e}")
        return None
