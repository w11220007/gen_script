from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.routing import APIRouter
from app.schemas.request_schema import GenerateTextRequest
from app.utils.api_utils import make_response
from app.web.api import echo, monitoring
from app.repositories.lesson_plan import generate_plan, load_grade_content, save_output_lesson_plan
from app.repositories.content_seo_text import generate_seo_content, get_links_from_tavily_content, integrate_links_into_content, save_output_seo
from app.repositories.text_seo_content import generate_seo_content_with_citations, get_links_from_tavily, compile_summary_with_citations, fetch_content_from_url, save_output
from app.repositories.suggested_exercises import read_file, suggest_study_plan, save_output_suggest_exercise
from app.repositories.rubric_generator import save_result, create_student_evaluation
from app.repositories.review_SEO import analyze_seo_content, save_output_review
from app.repositories.rewrite_content import generate_new_text, format_text, save_result_SEO_content
from app.repositories.generate_script_product_video import save_output_script, generate_script, format_script_to_json, extract_text, analyze_text
from app.repositories.generate_script_TVC import save_out_TVC, extract_text_from_pdf, process_tvc_script
from app.repositories.Class_newsletter import generate_notification, save_output, notification_types
from app.repositories.classroom_management import save_analysis_output, generate_analysis
from app.repositories.email_family import save_output_email, generate_email
from fastapi import HTTPException, Form, UploadFile, File
from app.core.settings import settings
import json
from app.repositories.model import SEORequest
import traceback
import logging
import os
from datetime import datetime

api_router = APIRouter()
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(echo.router, prefix="/echo", tags=["echo"])

logger = logging.getLogger(__name__)
@api_router.post("/generate_text")
async def generate_text(request: GenerateTextRequest) -> StreamingResponse:
    """Test generator text response."""
    text = request.input_text
    generated_text = generate_text(text)
    return make_response(content=generated_text)
@api_router.post("/generate_study_plan")
async def generate_study_plan(grade: str, topic: str, output_format: str = "markdown") -> StreamingResponse:
    """
    Generate study plan and learning objectives and save in the specified format..
    """
    try:
        # Load grade content from an external file
        grade_content = load_grade_content("app/grade_content.json")

        # Generate plan and objectives
        generated_plan = generate_plan(grade, topic, grade_content)

        # Validate output format
        if output_format not in ["markdown", "html", "json"]:
            return make_response(
                {"error": f"Unsupported output format: {output_format}"}, 400)

        # Save the generated plan to a file in the specified format
        file_name = f"study_plan.{output_format}"
        save_output(generated_plan, output_format, file_name)

        # Return the file as a StreamingResponse
        file = open(file_name, "r")
        media_type = (
            "text/markdown" if output_format == "markdown"
            else "text/html" if output_format == "html"
            else "application/json"
        )
        return StreamingResponse(file, media_type=media_type)

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return make_response({"error": str(e)}, 400)

@api_router.post("/generate_seo")
async def generate_seo(topic: str, sub_keywords: str, target_audience: str, tone: str, query: str):
    """
    Generate SEO content with integrated links from Tavily.
    """
    try:
        # Generate SEO content
        sub_keywords_list = sub_keywords.split(',')
        content = generate_seo_content(topic, sub_keywords_list, target_audience, tone)

        # Fetch related links from Tavily
        links = get_links_from_tavily(query)

        # Integrate links into the SEO content
        final_content = integrate_links_into_content(content, links)

        # Save the final content to a file
        output_file = "generated_seo_content.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(final_content)

        # Return the file as a streaming response
        file = open(output_file, "r", encoding="utf-8")
        return StreamingResponse(file, media_type="text/plain")

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/text_seo_content")
async def text_seo_content(topic: str, sub_keywords: str, target_audience: str, tone: str, output_format: str):
    try:
        # Step 1: Validate output format
        valid_formats = ["markdown", "html", "json"]
        if output_format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported output format: {output_format}")

        # Step 2: Search for links using Tavily
        content_dict = get_links_from_tavily(topic)
        if not content_dict:
            raise HTTPException(status_code=404, detail="No content found for the given topic.")

        # Step 3: Compile a summary with citations
        summary = compile_summary_with_citations(content_dict)

        # Step 4: Generate SEO content
        seo_content = generate_seo_content_with_citations(topic, sub_keywords, target_audience, tone, summary)

        # Step 5: Save the generated content to a file
        file_name = f"{topic.replace(' ', '_')}_seo_content.{output_format}"
        output_path = os.path.join(settings.media_dir_static, file_name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write the content to the file
        with open(output_path, "w") as f:
            f.write(seo_content if isinstance(seo_content, str) else seo_content["text"])  # Handle dict or string output

        # Step 6: Return the file as a streaming response
        media_type = {
            "markdown": "text/markdown",
            "html": "text/html",
            "json": "application/json",
        }.get(output_format, "text/plain")

        return StreamingResponse(open(output_path, "rb"), media_type=media_type)

    except HTTPException as http_exc:
        raise http_exc  # Reraise known HTTP exceptions
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@api_router.post("/generate_rubric")
async def generate_rubric(
    grade: str,
    topic: str,
    point_scale,
    language: str,
    output_format: str = "markdown",
) -> StreamingResponse:
    try:
        # Generate the evaluation content
        generated_rubric = create_student_evaluation(grade, topic, point_scale, language)

        # Validate output format
        if output_format not in ["markdown", "html", "json"]:
            return make_response({"error": f"Unsupported output format: {output_format}"}, 400)

        # Save the generated rubric to a file in the specified format
        file_name = f"rubric.{output_format}"
        save_output(generated_rubric, output_format, file_name)

        # Return the file as a StreamingResponse
        file = open(file_name, "r", encoding="utf-8")
        media_type = (
            "text/markdown" if output_format == "markdown"
            else "text/html" if output_format == "html"
            else "application/json"
        )
        return StreamingResponse(file, media_type=media_type)

    except Exception as e:
        import traceback
        print("Error:", traceback.format_exc())
        return make_response({"error": str(e)}, 400)

# FastAPI endpoint for file upload and study plan generation
@api_router.post("/generate-suggested-exercise")
async def generate_suggested_exercise(file: UploadFile, output_format="markdown"):
    """
    Generate a study plan based on uploaded file data.
    """
    try:
        # Save uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(await file.read())

        # Read file content
        file_content = read_file(temp_file_path)

        # Save output
        output_file = f"suggested_exercise.{output_format}"

        # Return the file as a response
        file = open(output_file, "r", encoding="utf-8")
        media_type = (
            "text/markdown" if output_format == "markdown"
            else "text/html" if output_format == "html"
            else "application/json"
        )
        return StreamingResponse(file, media_type=media_type)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}"
        )
    finally:
        # Clean up temporary files
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@api_router.post("/analyze-seo")
async def analyze_seo(content: str = Form(...), keyword: str = Form(...),
                      output_format: str = Form("markdown")):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=300, detail="Missing API Key")

        # Phân tích nội dung SEO
        result = analyze_seo_content(content, keyword)

        # Lưu kết quả
        file_name = f"seo_analysis.{output_format}"
        save_output_review(result, output_format, file_name)

        return {"message": "SEO analysis completed successfully", "file": file_name,
                "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/process-seo-evaluation")
async def process_seo_evaluation_api(
    input_text: str,
    tone: str,
    output_format: str = Form("markdown")
):
    """
    API endpoint to process SEO evaluation by rewriting the input text with a specific tone.
    """
    try:
        if output_format not in ["markdown", "json", "html"]:
            raise HTTPException(status_code=400, detail="Unsupported output format")

        # Generate new text with requested tone
        rewritten_text = generate_new_text(input_text, tone)

        # Format the output text to match the original layout
        formatted_text = format_text(input_text, rewritten_text)

        # Define the output file path
        output_file = f"SEO_content.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        # Save the formatted result
        save_result_SEO_content(formatted_text, output_format, output_path)

        return JSONResponse(
            content={
                "message": "SEO evaluation and text transformation completed successfully",
                "file": output_file,
                "rewritten_text": formatted_text
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/generate-video-script")
async def generate_video_script(
    output_format: str = Form(...),
    file: UploadFile = File(None)  # Cho phép gửi file JSON
):
    """API tạo kịch bản TVC với lời thoại + cảnh quay, hỗ trợ brand storytelling."""
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    content = await file.read()
    try:
        file_ext = file.filename.split(".")[-1].lower()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty.")

        if file_ext == "json":
            try:
                text_content = content.decode("utf-8")
                data = json.loads(text_content)
                text = data.get("text", "").strip()
                if not text:
                    raise HTTPException(status_code=400, detail="JSON must contain 'text' field.")
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

        elif file_ext == "pdf":
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(content)
                temp_pdf_path = temp_pdf.name

            try:
                text = extract_text(temp_pdf_path)
            finally:
                os.remove(temp_pdf_path)

            if not text.strip():
                raise HTTPException(status_code=400, detail="PDF has no readable text.")

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format (only JSON or PDF).")

        script_type = analyze_text(text)
        script = generate_script(text, script_type)

        # Tạo tên file an toàn
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"video_{timestamp}.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        # Lưu file output
        save_output_script(script, output_format, output_path)

        return JSONResponse(
            content={
                "message": "TVC script generated successfully",
                "file": output_path,
                "video_script": script
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate_tvc_script")
async def generate_tvc_script(
    company_name: str,
    output_format: str = Form(...),
    file: UploadFile = File(None)
):
    """API tạo kịch bản TVC với lời thoại + cảnh quay, hỗ trợ brand storytelling."""
    if file is None:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    content = await file.read()
    try:
        file_ext = file.filename.split(".")[-1].lower()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty.")

        if file_ext == "json":
            try:
                text_content = content.decode("utf-8")
                data = json.loads(text_content)
                text = data.get("text", "").strip()
                if not text:
                    raise HTTPException(status_code=400, detail="JSON must contain 'text' field.")
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")

        elif file_ext == "pdf":
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(content)
                temp_pdf_path = temp_pdf.name

            try:
                text = extract_text_from_pdf(temp_pdf_path)
            finally:
                os.remove(temp_pdf_path)

            if not text.strip():
                raise HTTPException(status_code=400, detail="PDF has no readable text.")

        else:
            raise HTTPException(status_code=400, detail="Unsupported file format (only JSON or PDF).")

        # Gọi AI để tạo kịch bản TVC
        script = process_tvc_script(company_name, text)

        # Tạo tên file an toàn
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"{company_name}_TVC_{timestamp}.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        # Lưu file output
        save_out_TVC(script, output_format, output_path)

        return JSONResponse(
            content={
                "message": "TVC script generated successfully",
                "file": output_path,
                "tvc_script": script,

            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/class_newsletter")
async def class_newsletter(
    category: str = Form(...),
    title: str = Form(...),
    date: str = Form(...),
    details: str = Form(...),
    output_format: str = Form("markdown")
):
    """
    API endpoint to generate a class newsletter notification.
    """
    try:
        # Validate category
        if category not in notification_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Must be one of: {', '.join(notification_types)}"
            )

        # Prepare event info
        event_info = {
            "category": category,
            "title": title,
            "date": date,
            "details": details
        }

        # Generate notification text
        notification_text = generate_notification(event_info)

        # Create a timestamped filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"class_newsletter_{timestamp}.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        # Save output
        save_out_TVC(notification_text, output_format, output_path)

        return JSONResponse(
            content={
                "message": "Class newsletter generated successfully",
                "file": output_path,
                "notification": notification_text
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze_classroom_issue")
async def analyze_classroom_issue_api(
    problem_statement: str = Form(...),
    output_format: str = Form("markdown")
):
    """
    API để phân tích vấn đề lớp học và đưa ra chiến lược.
    """
    try:
        # Gọi AI để phân tích
        analysis_result = generate_analysis(problem_statement)

        # Tạo tên file theo thời gian
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"classroom_analysis_{timestamp}.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        return JSONResponse(
            content={
                "message": "Classroom analysis completed successfully",
                "file": output_path,
                "analysis": analysis_result
            }
        )
    except Exception as e:
        raise HTTPException(status_code = 500, detail=str(e))

@api_router.post("/generate_email")
async def generate_email_api(
    title: str = Form(...),
    date: str = Form(...),
    details: str = Form(...),
    output_format: str = Form("markdown")
):
    """
    API để tạo email thông báo từ giáo viên đến phụ huynh.
    """
    try:
        event_info = {
            "title": title,
            "date": date,
            "details": details
        }

        # Gọi hàm để tạo nội dung email
        email_content = generate_email(event_info)

        output_file = f"email.{output_format}"
        output_path = os.path.join(settings.media_dir_static, output_file)

        # Lưu file
        save_output_email(email_content, output_format, output_path)

        return JSONResponse(
            content={
                "message": "Email generated successfully",
                "file": output_path,
                "email_content": email_content
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
