from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os
import json
from app.core.settings import settings

os.environ["GEMINI-API-KEY"] = settings.gemini_api_key

llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            api_key=settings.gemini_api_key,  # Directly use settings instead of getenv
            temperature=0.5,
            max_tokens=1024,
            timeout=30,
            max_retries=3,
        )

# Hàm tạo prompt để phân tích vấn đề
def generate_analysis(problem_statement):
    prompt = PromptTemplate(
        input_variables=["problem_statement"],
        template="""
        Bạn là một chuyên gia giáo dục giàu kinh nghiệm.
        Hãy phân tích vấn đề sau và đề xuất các chiến lược quản lý lớp học hiệu quả.

        **Vấn đề:** {problem_statement}

        🔹 **Chiến lược đề xuất:**
        - Cung cấp ít nhất 2 chiến lược giải quyết vấn đề này.
        - Mô tả cách triển khai từng chiến lược với các bước thực tế.

        🔹 **Lời khuyên bổ sung:**
        - Đưa ra các phương pháp hỗ trợ giáo viên xử lý tình huống này.
        - Các phương pháp khuyến khích học sinh tập trung hơn.

        🔹 **Chiến lược phòng ngừa:**
        - Gợi ý cách thiết lập quy tắc, môi trường học tập hiệu quả.
        - Các kỹ thuật giúp giảm thiểu tình trạng mất tập trung trong lớp học.

        Hãy viết rõ ràng, ngắn gọn, dễ hiểu và có thể áp dụng thực tế.
        """
    )

    # Gửi prompt đến AI
    prompt_text = prompt.format(problem_statement=problem_statement)
    response = llm.invoke(prompt_text)

    # Trích xuất nội dung phản hồi
    analysis_result = response.content.strip()
    return analysis_result


# Hàm lưu kết quả ra file với định dạng khác nhau
def save_analysis_output(content, output_format="markdown",
                         file_name="classroom_management"):
    if output_format == "markdown":
        with open(f"{file_name}.md", "w", encoding="utf-8") as f:
            f.write(content)
    elif output_format == "html":
        html_content = f"<html><body><pre>{content}</pre></body></html>"
        with open(f"{file_name}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    elif output_format == "json":
        analysis_json = {"analysis": content}
        with open(f"{file_name}.json", "w", encoding="utf-8") as f:
            json.dump(analysis_json, f, indent=4, ensure_ascii=False)
    else:
        raise ValueError("Unsupported output format.")


