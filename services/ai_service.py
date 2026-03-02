from openai import OpenAI
from utils.security import decrypt_token
from typing import Optional
import json
import traceback

SYSTEM_PROMPT = """
Bạn là chuyên gia sáng tạo nội dung E-commerce hàng đầu Việt Nam.
Dựa trên dữ liệu sản phẩm/video được cung cấp, hãy tạo ra 2 loại Prompt:

1. **sora_prompt** (Prompt cho Video AI - Sora/Runway/Luma):
   - Mô tả chuyển động camera (pan, zoom, dolly)
   - Ánh sáng (studio lighting, golden hour, neon...)
   - Góc quay (close-up sản phẩm, lifestyle shot...)
   - Bối cảnh (studio trắng, phòng khách sang trọng, ngoài trời...)
   - Thời lượng và nhịp điệu

2. **midjourney_prompt** (Prompt cho Ảnh AI - Midjourney/Flux):
   - Mô tả bối cảnh studio cao cấp
   - Phong cách nghệ thuật (minimalist, luxury, editorial...)
   - Ánh sáng và màu sắc
   - Tỷ lệ và bố cục

Trả về **JSON thuần** gồm đúng 2 keys: `sora_prompt` và `midjourney_prompt`.
Mỗi prompt phải viết bằng tiếng Anh, chi tiết ít nhất 3 dòng.
"""

def generate_ai_prompts(source_data: dict, target_type: str, user_encrypted_key: Optional[str] = None, gemini_encrypted_key: Optional[str] = None):
    """
    Ưu tiên dùng Gemini (miễn phí), fallback sang OpenAI.
    """
    errors = []
    
    # 1. Thử Gemini trước (miễn phí, không bị quota)
    if gemini_encrypted_key:
        try:
            result = _try_gemini(source_data, target_type, gemini_encrypted_key)
            # Kiểm tra xem kết quả có phải JSON hợp lệ không
            parsed = json.loads(result)
            if "sora_prompt" in parsed or "midjourney_prompt" in parsed:
                return result  # Thành công!
            if "error" in parsed:
                errors.append(f"Gemini: {parsed['error']}")
            else:
                return result  # JSON hợp lệ nhưng keys khác, vẫn trả về
        except json.JSONDecodeError:
            # Nếu Gemini trả về text không phải JSON, vẫn trả về
            if result and len(result) > 20:
                return json.dumps({"sora_prompt": result, "midjourney_prompt": result})
            errors.append(f"Gemini trả về dữ liệu không hợp lệ")
        except Exception as e:
            errors.append(f"Gemini: {str(e)}")

    # 2. Fallback sang OpenAI
    if user_encrypted_key:
        try:
            result = _try_openai(source_data, target_type, user_encrypted_key)
            parsed = json.loads(result)
            if "error" in parsed:
                errors.append(f"OpenAI: {parsed['error']}")
            else:
                return result
        except json.JSONDecodeError:
            if result and len(result) > 20:
                return json.dumps({"sora_prompt": result, "midjourney_prompt": result})
            errors.append(f"OpenAI trả về dữ liệu không hợp lệ")
        except Exception as e:
            errors.append(f"OpenAI: {str(e)}")

    # 3. Tất cả đều thất bại
    if errors:
        return json.dumps({"error": " | ".join(errors)}, ensure_ascii=False)
    
    return json.dumps({"error": "Chưa có API Key nào được cấu hình. Vui lòng vào Settings nhập Gemini hoặc OpenAI Key."}, ensure_ascii=False)


def _try_gemini(source_data: dict, target_type: str, gemini_encrypted_key: str) -> str:
    """Gọi Google Gemini API"""
    import google.generativeai as genai
    
    real_api_key = decrypt_token(gemini_encrypted_key)
    genai.configure(api_key=real_api_key)
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    user_content = f"Dữ liệu sản phẩm ({target_type}): {json.dumps(source_data, ensure_ascii=False)}"
    
    response = model.generate_content(
        f"{SYSTEM_PROMPT}\n\n{user_content}\n\nTrả về JSON thuần, không có markdown code block.",
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.7,
        )
    )
    
    return response.text


def _try_openai(source_data: dict, target_type: str, user_encrypted_key: str) -> str:
    """Gọi OpenAI API (fallback)"""
    real_api_key = decrypt_token(user_encrypted_key)
    client = OpenAI(api_key=real_api_key)
    
    user_content = f"Dữ liệu sản phẩm ({target_type}): {json.dumps(source_data, ensure_ascii=False)}"
    
    # Thử gpt-4o-mini trước (rẻ hơn 15x)
    for model_name in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            continue
    
    raise Exception("Tất cả model OpenAI đều lỗi. Kiểm tra lại API Key và Billing tại platform.openai.com")
