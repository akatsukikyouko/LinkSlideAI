import json
import time
import requests
from PIL import Image
from io import BytesIO
import os

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_slide_image_tool(prompt: str, slide_index: int, session_id: str, max_retries: int = 3) -> str:
    """
    调用Z-Image生成PPT单页图片，包含重试机制。
    """
    config = load_config()
    ms_config = config['modelscope']
    
    headers = {
        "Authorization": f"Bearer {ms_config['api_key']}",
        "Content-Type": "application/json",
        "X-ModelScope-Async-Mode": "true"
    }

    print(f"--- [Tool] Start Generating Slide {slide_index} (Session: {session_id}) ---")
    
    # === 重试循环 ===
    for attempt in range(1, max_retries + 1):
        try:
            # 1. 发起生成请求
            print(f"   > Attempt {attempt}/{max_retries}: Submitting task...")
            
            payload = {
                "model": ms_config['model_id'],
                "prompt": prompt,
                "size": "1600x900"
            }
            
            response = requests.post(
                f"{ms_config['base_url']}v1/images/generations",
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                timeout=30 # 设置提交超时
            )
            
            # 检查 HTTP 状态码
            if response.status_code != 200:
                print(f"   [Error] API Error: Status {response.status_code} - {response.text}")
                raise Exception(f"HTTP {response.status_code}")

            # 解析 Task ID
            try:
                task_id = response.json()["task_id"]
            except Exception as e:
                print(f"   [Error] Failed to parse response json: {response.text}")
                raise e

            print(f"   > Task ID: {task_id}, Waiting for result...")

            # 2. 轮询结果 (最多等待 90 秒)
            for _ in range(45): 
                time.sleep(2)
                try:
                    result = requests.get(
                        f"{ms_config['base_url']}v1/tasks/{task_id}",
                        headers={**headers, "X-ModelScope-Task-Type": "image_generation"},
                        timeout=10
                    )
                    
                    if result.status_code != 200:
                        print(f"   [Warning] Polling status {result.status_code}, retrying...")
                        continue
                        
                    data = result.json()
                    status = data.get("task_status")

                    if status == "SUCCEED":
                        img_url = data["output_images"][0]
                        # 保存图片
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
                    
                    elif status == "FAILED":
                        error_msg = data.get("message", "Unknown error")
                        print(f"   [Error] Task Failed: {error_msg}")
                        raise Exception(f"ModelScope Task Failed: {error_msg}")
                        
                except requests.exceptions.RequestException as re:
                    print(f"   [Warning] Network glitch during polling: {re}")
                    continue

            # 如果轮询结束还在跑，抛出超时异常
            raise Exception("Polling Timeout")

        except Exception as e:
            print(f"   [Retry] Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                time.sleep(3) # 重试前冷静一下
            else:
                return f"Error: All {max_retries} attempts failed. Reason: {str(e)}"

    return "Error: Unknown failure"