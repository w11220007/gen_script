from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
from langchain.prompts import PromptTemplate
import os
import json
import html

# Set API key
os.environ["GEMINI-API-KEY"] = settings.gemini_api_key

notification_types = ["Celebrations", "Important Announcements", "Additional Content"]

def generate_notification(event_info):
    try:
        prompt = PromptTemplate(
            input_variables=["category", "title", "date", "details"],
            template="""
            Bạn là giáo viên chủ nhiệm cần gửi thông báo đến phụ huynh học sinh về một sự kiện.
            Hãy viết một thông báo trang trọng, rõ ràng và chuyên nghiệp dựa trên thông tin sau:
            - **Loại thông báo:** {category}
            - **Tiêu đề:** {title}
            - **Ngày:** {date}
            - **Nội dung:** {details}
            Hãy viết theo giọng trang trọng và dễ hiểu cho phụ huynh. Kết thúc bằng 'Trân trọng'.
            """
        )

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=settings.gemini_api_key,  # Directly use settings instead of getenv
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )

        # Ensure event_info contains all necessary keys
        required_keys = ["category", "title", "date", "details"]
        missing_keys = [key for key in required_keys if key not in event_info]
        if missing_keys:
            raise ValueError(f"Missing required keys in event_info: {', '.join(missing_keys)}")

        prompt_text = prompt.format(
            category=event_info["category"],
            title=event_info["title"],
            date=event_info["date"],
            details=event_info["details"]
        )

        response = llm.invoke(prompt_text)

        # Xử lý đầu ra từ Gemini
        script_output = response.content.strip()

        return script_output  # Trả về kết quả dưới dạng markdown

    except Exception as e:
        raise RuntimeError(f"Error generating script: {str(e)}")

def save_output(output, output_format, file_name):
    if not isinstance(output, str):
        raise TypeError("Output must be a string.")

    if output_format == "markdown":
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(output)

    elif output_format == "html":
        escaped_content = html.escape(output)
        html_content = f"<html><body><pre>{escaped_content}</pre></body></html>"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(html_content)

    elif output_format == "json":
        tvc_json = format_script_to_json(output)
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(tvc_json, f, indent=4, ensure_ascii=False)

    else:
        raise ValueError(f"Unsupported output format: {output_format}")

# Hàm chuyển đổi kịch bản TVC thành JSON
def format_script_to_json(output):
    lines = output.split("\n")
    scenes = []
    current_scene = None

    for line in lines:
        line = line.strip()
        if line.startswith("📌"):  # Scene marker
            if current_scene:
                scenes.append(current_scene)
            current_scene = {"scene": line.replace("📌", "").strip(), "details": []}
        elif current_scene and line:
            current_scene["details"].append(line)

    if current_scene:
        scenes.append(current_scene)

    return {"tvc_script": scenes if scenes else [{"scene": "General", "details": lines}]}
