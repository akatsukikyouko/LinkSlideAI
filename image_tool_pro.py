import json
import os
import time
from PIL import Image
from io import BytesIO
import requests
# Install SDK:  pip install 'volcengine-python-sdk[ark]'
from volcenginesdkarkruntime import Ark 

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_slide_image_tool_pro(prompt: str, slide_index: int, session_id: str, max_retries: int = 3) -> str:
    """
    调用豆包生图生成PPT单页图片，包含重试机制。
    """
    config = load_config()
    pro_config = config['image_tool_pro']
    
    client = Ark(
        base_url=pro_config['base_url'],
        api_key=pro_config['api_key'], 
    )

    print(f"--- [Tool Pro] Start Generating Slide {slide_index} (Session: {session_id}) ---")
    
    # === 重试循环 ===
    for attempt in range(1, max_retries + 1):
        try:
            # 1. 发起生成请求
            print(f"   > Attempt {attempt}/{max_retries}: Submitting task...")
            
            imagesResponse = client.images.generate( 
                model=pro_config['model_id'],
                prompt=prompt,
                size="2560x1440",
                response_format="url",
                watermark=False
            ) 
            
            if not imagesResponse.data or not imagesResponse.data[0].url:
                raise Exception("No image URL returned from API")
                
            img_url = imagesResponse.data[0].url
            print(f"   > Image generated, URL: {img_url}")
            
            # 2. 保存图片
            save_dir = os.path.join("static", "output", session_id)
            os.makedirs(save_dir, exist_ok=True)
            filename = f"slide_{slide_index}.jpg"
            filepath = os.path.join(save_dir, filename)
            
            # 下载图片内容
            img_data = requests.get(img_url, timeout=30).content
            image = Image.open(BytesIO(img_data))
            image.save(filepath)
            
            print(f"   > Success! Saved to {filepath}")
            return f"/static/output/{session_id}/{filename}"
            
        except Exception as e:
            print(f"   [Retry] Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                time.sleep(3) # 重试前冷静一下
            else:
                return f"Error: All {max_retries} attempts failed. Reason: {str(e)}"

    return "Error: Unknown failure"
