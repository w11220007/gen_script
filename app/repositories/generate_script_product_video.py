import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.settings import settings
import json
import fitz
import re
from langchain.prompts import PromptTemplate
os.environ['GEMINI-API-KEY'] = settings.gemini_api_key

llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )
if not settings.gemini_api_key:
    raise ValueError("GEMINI API key is missing. Check your settings.")
def extract_text(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text") + "\n"
    return text.strip()

def extract_json(response_text):
    try:
        # Tìm đoạn JSON hợp lệ trong response
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("Không tìm thấy JSON hợp lệ trong phản hồi.")
    except json.JSONDecodeError:
        raise ValueError("Phản hồi không phải là JSON hợp lệ.")

def analyze_text(text):
    prompt_generate = PromptTemplate(
        input_variables=["text"],
        template="""
        Bạn là một chuyên gia về viết kịch bản quay video quảng cáo sản phẩm, dịch vụ trên các nền tảng thương mai điện tử.
        Hãy phân tích đoạn văn bản {text} và xác định phong cách viết phù hợp trong 33 cách sau:
        - Auto-select by AI
        - Pain Points + Harms + Solutions, using fear-based hooks
        - Pain Points + Harms + Solutions, using curiosity-based hooks
        - Pain Points + Harms + Solutions, using pitfall-based hooks
        - Pain Points + Harms + Solutions, using pain point hooks
        - Pain Points + Harms + Solutions, using hooks related to relationships
        - Attention-grabbing opening + Setting expectations + Solutions, using reveal-type hooks
        - Attention-grabbing opening + Setting expectations + Solutions, using pitfalls-based hooks
        - Attention-grabbing opening + Setting expectations + Solutions, using fear-based hooks
        - Attention-grabbing opening + Setting expectations + Solutions, using cognitive contrast hooks
        - Use a structure that foregrounds benefits and results
        - Revealing industry secrets + Setting expectations + Solutions structure
        - Leveraging celebrities/hot topics/public choices
        - Conveying benefits + Reinforcing expectations + Solutions
        - Share personal real stories, using curiosity hooks
        - Sharing personal true stories, using cautionary hooks
        - Sharing personal true stories
        - Contrast structure of mistakes and correct actions
        - Pain points + harms + Solutions with emoji
        - Attention-grabbing opening + Setting expectations + Solutions with emoji
        - Use a structure that foregrounds benefits and results, with emoji
        - Conveying benefits + reinforcing expectations + solution, with emoji
        - Revealing industry secrets + Setting expectations + Solutions structure, with emoji
        - pose a question to grab attention with a relatively formal tone
        - meticulous corporate introduction
        - Storytelling style
        - Concise and clear style
        - Comparative and analysis style
        - Brand-oriented, storytelling
        - Introduced from the user's first-person perspective
        - News broadcast style
        - Science Education Style
        - Daily life Style

        Hãy chỉ trả về phong cách phù hợp dưới dạng JSON:
        {{
            "style": "..."
        }}
        """
    )
    try:
        prompt_text = prompt_generate.format(text=text)
        response = llm.invoke(prompt_text)
        response_text = response.content.strip()
        response_text = re.sub(r"```json|```", "", response_text,
                               flags=re.DOTALL).strip()

        print(f"abc{response_text}")
        result = json.loads(response_text)
        return result
    except Exception as e:
        raise RuntimeError(f"Error analyze text: {str(e)}")


def generate_script(text, script_type):
    """Sử dụng Gemini để tạo kịch bản video."""
    try:
        generate_script_prompt = PromptTemplate(
            input_variables = ["text", "script_type"],
            template="""
            Bạn là một chuyển gia sáng tạo nội dung quảng cáo. Viết một đoạn kịch bản video ngắn 30s đến 1 phút quảng cáo sản phẩm
            dựa trên nội dung {text} và dựa theo phong cách viết nội dung{script_type}. Kịch bản giống như các content creater hiện nay chỉ nói một mình, và trong kịch bản chỉ cần đưa ra lời thoại là được.
            Hãy đảm bảo nội dung hấp dẫn, có câu mở đầu chú ý, cuối bài có lời kêu gọi mua hàng, phù hợp với SEO và có giá trị cho người xem."
        """

        )
        prompt_text = generate_script_prompt.format(text=text, script_type=script_type)
        response = llm.invoke(prompt_text)
        if isinstance(response, str):
            return response
        elif hasattr(response, "content"):  # Nếu là AIMessage có thuộc tính content
            return response.content
        elif isinstance(response, dict):  # Nếu là dạng JSON
            return response.get("content", "Không có nội dung được tạo.")
        else:
            return "Không thể tạo nội dung."


    except Exception as e:
        return f"Error generating script: {e}"


def save_output_script(output: str, output_format: str, output_path) -> str:
    if output_format not in ["markdown", "html", "json"]:
        raise ValueError("Unsupported output format.")

    media_dir = settings.media_dir_static
    os.makedirs(media_dir, exist_ok=True)

    output_file = f"video_script.{output_format}"
    output_path = os.path.join(media_dir, output_file)

    # Kiểm tra nếu output là JSON object
    if output_format == "json":
        try:
            output = json.dumps(json.loads(output), indent=4)
        except json.JSONDecodeError:
            output = json.dumps({"script": output}, indent=4)

    # Xử lý nội dung theo định dạng
    content = (
        output if output_format == "markdown"
        else f"<html><body><pre>{output}</pre></body></html>" if output_format == "html"
        else output
    )

    # Lưu file
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)

    return output_path


def format_script_to_json(output):
    """Chuyển đổi kịch bản sang JSON"""
    return {"script": output.split("\n")}
