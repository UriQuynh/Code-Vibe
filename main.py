from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os

from utils.security import encrypt_token, decrypt_token, ENCRYPTION_KEY
from services.scraper_service import get_shopee_product_data, get_tiktok_video_data
from services.ai_service import generate_ai_prompts

app = FastAPI(title="AI E-com Suite Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= Persistent Token Storage =========
TOKEN_FILE = "/tmp/ecom_tokens.json"

def load_tokens():
    """Load tokens từ file JSON (tồn tại qua restart, mất khi redeploy)"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_tokens_to_file(tokens: dict):
    """Lưu tokens vào file JSON"""
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f)
    except Exception:
        pass

# Load tokens on startup
token_store = load_tokens()

# ========= Models =========
class TokenPayload(BaseModel):
    openai_key: Optional[str] = None
    gemini_key: Optional[str] = None
    tiktok_token: Optional[str] = None
    shopee_token: Optional[str] = None
    replicate_token: Optional[str] = None

class LinkPayload(BaseModel):
    url: str

class GeneratePayload(BaseModel):
    prompt: str

# ========= Endpoints =========
@app.post("/settings/save-tokens")
def save_tokens(payload: TokenPayload):
    """Mã hóa và lưu API Keys an toàn"""
    if payload.openai_key:
        token_store["openai_encrypted"] = encrypt_token(payload.openai_key)
    if payload.gemini_key:
        token_store["gemini_encrypted"] = encrypt_token(payload.gemini_key)
    if payload.tiktok_token:
        token_store["tiktok_encrypted"] = encrypt_token(payload.tiktok_token)
    if payload.replicate_token:
        token_store["replicate_encrypted"] = encrypt_token(payload.replicate_token)
    
    # Persist to file
    save_tokens_to_file(token_store)
    
    return {"message": "Tokens saved successfully"}


@app.post("/analyze/link")
def analyze_link(payload: LinkPayload):
    """Phân tích link TikTok/Shopee và tạo AI Content"""
    url = payload.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Lấy AI keys
    user_openai_key = token_store.get("openai_encrypted")
    user_gemini_key = token_store.get("gemini_encrypted")
    
    if not user_openai_key and not user_gemini_key:
        raise HTTPException(
            status_code=400, 
            detail="Vui lòng vào Settings nhập ít nhất Gemini hoặc OpenAI API Key trước."
        )
    
    # Scrape dữ liệu thật
    if "shopee" in url:
        data = get_shopee_product_data(url)
        target_type = "shopee"
    elif "tiktok" in url:
        data = get_tiktok_video_data(url)
        target_type = "tiktok"
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ link Shopee hoặc TikTok")
    
    # Generate AI prompts (Gemini ưu tiên, OpenAI fallback)
    prompts_json_str = generate_ai_prompts(data, target_type, user_openai_key, user_gemini_key)
    
    try:
        prompts = json.loads(prompts_json_str)
    except Exception:
        prompts = {"raw": prompts_json_str}
    
    return {
        "status": "success",
        "data": data,
        "prompts": prompts
    }


@app.post("/generate/image")
def generate_image_api(payload: GeneratePayload):
    """Tạo ảnh sản phẩm bằng Replicate AI"""
    user_replicate_key = token_store.get("replicate_encrypted")
    if not user_replicate_key:
        raise HTTPException(
            status_code=400, 
            detail="Vui lòng thiết lập Replicate API Key trong Settings trước."
        )
    
    from services.replicate_service import generate_product_image
    result = generate_product_image(payload.prompt, user_replicate_key)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"url": result.get("url")}


@app.post("/generate/video")
def generate_video_api(payload: GeneratePayload):
    """Tạo video sản phẩm bằng Replicate AI"""
    user_replicate_key = token_store.get("replicate_encrypted")
    if not user_replicate_key:
        raise HTTPException(
            status_code=400, 
            detail="Vui lòng thiết lập Replicate API Key trong Settings trước."
        )
    
    from services.replicate_service import generate_product_video
    result = generate_product_video(payload.prompt, user_replicate_key)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"url": result.get("url")}


@app.get("/health")
def health_check():
    """Kiểm tra trạng thái backend"""
    keys_configured = []
    if token_store.get("gemini_encrypted"):
        keys_configured.append("gemini")
    if token_store.get("openai_encrypted"):
        keys_configured.append("openai")
    if token_store.get("replicate_encrypted"):
        keys_configured.append("replicate")
    
    return {
        "status": "ok",
        "keys_configured": keys_configured,
        "total_keys": len(keys_configured)
    }
