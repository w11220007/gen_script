import os
import json
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.core.settings import settings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from docx import Document
from typing import List


# Set GEMINI API key
os.environ["GEMINI-API-KEY"] = settings.gemini_api_key

# Function to read uploaded file
def read_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while reading the file: {e}"
        )
def process_data(data: List[dict]) -> dict:
    result = [d for d in data if d.get("value", 0 > 10)]
    return result


# Function to suggest study plan
def suggest_study_plan(student_name, subject, grade_level, weaknesses, areas_to_improve):
    try:
        prompt_template = PromptTemplate(
            input_variables=["student_name", "subject", "grade_level", "weaknesses", "areas_to_improve"],
            template="""You are an expert tutor for {subject}.
Your task is to provide solutions for a student named {student_name}, who is in grade {grade_level}.

Here are the student's weaknesses and areas to improve:
- Weaknesses: {weaknesses}
- Areas to Improve: {areas_to_improve}

Provide:
1. Specific learning strategies or techniques to address these weaknesses.
2. Recommend books, guides, or resources suitable for grade {grade_level}.
3. If the subject is Math or Science, create tailored practice exercises to help the student improve.

Be concise, clear, and motivational."""
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=settings.gemini_api_key,
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )

        study_plan = llm(prompt_template.format(
            student_name=student_name,
            subject=subject,
            grade_level=grade_level,
            weaknesses=", ".join(weaknesses),
            areas_to_improve=", ".join(areas_to_improve),
        ))

        return study_plan
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating the study plan: {e}"
        )

# Function to save the output
def save_output_suggest_exercise(output, output_format, file_name):
    try:
        if output_format == "markdown":
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(output)
        elif output_format == "html":
            html_content = f"<html><body><pre>{output}</pre></body></html>"
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(html_content)
        elif output_format == "json":
            kahoot_json = {"content": output}
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(kahoot_json, f, indent=4)
        else:
            raise ValueError("Unsupported output format.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving the file: {e}"
        )
