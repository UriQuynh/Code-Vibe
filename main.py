from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

from utils.security import encrypt_token, ENCRYPTION_KEY
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

# Dummy Memory DB since Postgres setup isn't fully detailed in prompt
fake_db = {
    "tokens": {
        # "openai_encrypted": "..."
    }
}

from typing import Optional

class TokenPayload(BaseModel):
    openai_key: Optional[str] = None
    gemini_key: Optional[str] = None
    tiktok_token: Optional[str] = None
    shopee_token: Optional[str] = None
    replicate_token: Optional[str] = None

class LinkPayload(BaseModel):
    url: str

@app.post("/settings/save-tokens")
def save_tokens(payload: TokenPayload):
    # Encrypt and save to fake DB
    if payload.openai_key:
        fake_db["tokens"]["openai_encrypted"] = encrypt_token(payload.openai_key)
    if payload.gemini_key:
        fake_db["tokens"]["gemini_encrypted"] = encrypt_token(payload.gemini_key)
    if payload.tiktok_token:
        fake_db["tokens"]["tiktok_encrypted"] = encrypt_token(payload.tiktok_token)
    if payload.replicate_token:
        fake_db["tokens"]["replicate_encrypted"] = encrypt_token(payload.replicate_token)
        
    return {"message": "Tokens saved successfully"}

@app.post("/analyze/link")
def analyze_link(payload: LinkPayload):
    url = payload.url
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Fetch AI keys
    user_openai_key_encrypted = fake_db["tokens"].get("openai_encrypted")
    user_gemini_key_encrypted = fake_db["tokens"].get("gemini_encrypted")
    
    if not user_openai_key_encrypted and not user_gemini_key_encrypted:
        raise HTTPException(status_code=400, detail="Vui lòng thiết lập ít nhất Gemini hoặc OpenAI API Key trong Cài đặt.")
        
    if "shopee" in url:
        data = get_shopee_product_data(url)
        target_type = "shopee"
    elif "tiktok" in url:
        data = get_tiktok_video_data(url)
        target_type = "tiktok"
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ link Shopee hoặc TikTok")
    
    # Generate prompt using AI (Gemini ưu tiên, OpenAI fallback)
    prompts_json_str = generate_ai_prompts(data, target_type, user_openai_key_encrypted, user_gemini_key_encrypted)
    
    try:
        if "error" in prompts_json_str:
             return {"data": data, "prompts": prompts_json_str}
        prompts = json.loads(prompts_json_str)
    except:
        prompts = {"raw": prompts_json_str}
        
    return {
        "status": "success",
        "data": data,
        "prompts": prompts
    }

class GeneratePayload(BaseModel):
    prompt: str

@app.post("/generate/image")
def generate_image_api(payload: GeneratePayload):
    user_replicate_key_encrypted = fake_db["tokens"].get("replicate_encrypted")
    if not user_replicate_key_encrypted:
        raise HTTPException(status_code=400, detail="Vui lòng thiết lập Replicate API Key trong Cài đặt (Account Vault) trước.")
    
    from services.replicate_service import generate_product_image
    result = generate_product_image(payload.prompt, user_replicate_key_encrypted)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"url": result.get("url")}

@app.post("/generate/video")
def generate_video_api(payload: GeneratePayload):
    user_replicate_key_encrypted = fake_db["tokens"].get("replicate_encrypted")
    if not user_replicate_key_encrypted:
        raise HTTPException(status_code=400, detail="Vui lòng thiết lập Replicate API Key trong Cài đặt (Account Vault) trước.")
    
    from services.replicate_service import generate_product_video
    result = generate_product_video(payload.prompt, user_replicate_key_encrypted)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"url": result.get("url")}

@app.get("/health")
def health_check():
    return {"status": "ok"}
