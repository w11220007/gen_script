import json
import os
from docx import Document
import fitz
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from langchain.prompts import PromptTemplate
import re

# Cấu hình API key
os.environ["GOOGLE_API_KEY"] = settings.gemini_api_key

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.5,
    max_tokens=1024,
    max_retries=3,
)


def extract_text_from_docx(docx_path):
    """Trích xuất nội dung từ file .docx."""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"File not found: {docx_path}")

    doc = Document(docx_path)
    content = [para.text.strip() for para in doc.paragraphs if para.text.strip()]

    return "\n".join(content)


def extract_text_from_pdf(pdf_path):
    """Trích xuất nội dung từ file PDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()


def extract_json(response_text):
    """Trích xuất JSON hợp lệ từ phản hồi."""
    try:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            raise ValueError("Không tìm thấy JSON hợp lệ trong phản hồi.")
    except json.JSONDecodeError:
        raise ValueError("Phản hồi không phải là JSON hợp lệ.")


def analyze_text(text):
    """Phân tích nội dung và trích xuất thông tin từ AI."""
    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
        Bạn là giáo viên đang chuẩn bị giáo án cho học sinh. Hãy phân tích đoạn văn sau đây và xác định:
         - Chủ đề bài học hôm nay là gì?
         - Hướng dẫn từng bước thực hiện như thế nào?
         - Tổng kết kiến thức cuối buổi cho học sinh.

         Kết quả trả về JSON hợp lệ:
         Văn bản: {text}

         **JSON output**
         {{
            "topic": "",
            "Guild": "",
            "Summarize": ""
         }}
        """
    )
    prompt_text = prompt.format(text=text)
    response = llm.invoke(prompt_text)
    response_text = response.content.strip()

    response_text = re.sub(r"```json|```", "", response_text, flags=re.DOTALL).strip()
    #print(extract_json(response_text))

    return extract_json(response_text)


def gen_script(text):
    """Tạo giáo án dựa trên nội dung phân tích."""
    try:
        analysis = analyze_text(text)
        topic = analysis.get("topic", "").strip()
        Guild = analysis.get("Guild", [])
        Summarize = analysis.get("Summarize", "").strip()
        Guild_steps = "\n".join(
            [f"{step['step']}: {step['description']}" for step in Guild])
        print(f"guild steps: ", Guild_steps )
        prompt_gen = PromptTemplate(
            input_variables=["topic", "Guild", "Summarize"],
            template="""
            Bạn là giáo viên chuẩn bị giáo án với chủ đề: {topic}.

            Hướng dẫn từng bước:
            {Guild}

            Hãy lấy 4 ví dụ minh họa để học sinh dễ hiểu.

            Sau đó, tổng kết bài học:
            {Summarize}

            Cuối cùng, giao bài tập về nhà.

            Định dạng JSON:
            ```json
            {{
                "topic": "{topic}",
                "subtitle": "",
                "Steps": [
                    {{"Step": "Bước 1", "Example": "Ví dụ 1"}},
                    {{"Step": "Bước 2", "Example": "Ví dụ 2"}},
                    {{"Step": "Bước 3", "Example": "Ví dụ 3"}},
                    {{"Step": "Bước 4", "Example": "Ví dụ 4"}}
                ],
                "Summarize": "{Summarize}",
                "Homework": ""
            }}
            ```
            """
        )


        prompt_text = prompt_gen.format(topic=topic, Guild=Guild_steps, Summarize=Summarize)
        if prompt_text is None or prompt_text.strip() == "":
            print("Loi prompt_text" )
            raise ValueError("Propmt format failed")
        response = llm.invoke(prompt_text)
        response_text = response.content.strip()
        print("🔄 Kết quả từ AI:\n", response_text)  # Debug
        response_text = re.sub(r"```json|```", "", response_text,
                               flags=re.DOTALL).strip()
        result = extract_json(response_text)

        print("Print result: ", result)
        #return extract_json(response_text)
        return result

    except Exception as e:
        raise RuntimeError(f"Error generating script: {str(e)}")


def save_script(output, file_name):
    """Lưu script vào file JSON."""
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
