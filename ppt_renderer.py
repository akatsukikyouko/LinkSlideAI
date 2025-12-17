import os
import zipfile

# -------------------------------------------------------------------------
# 重点修改了底部的 Reveal.initialize({{ hash: true }});
# -------------------------------------------------------------------------
HTML_TEMPLATE = """
<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>Generated Presentation</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/theme/black.css">
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                {slides_html}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.5.0/dist/reveal.js"></script>
        <script>
            // 注意这里：使用了双花括号 {{ }} 来转义，
            // 这样 Python .format() 就不会把它当成变量了。
            Reveal.initialize({{ hash: true }});
        </script>
    </body>
</html>
"""

def create_presentation(session_id, slides_data):
    """
    生成可下载的 PPT 包。
    """
    slides_html = ""
    
    # 1. 构建 HTML 内容
    for slide in slides_data:
        # 只取文件名，确保相对路径正确
        filename = os.path.basename(slide['image_path'])
        
        slides_html += f"""
        <section data-background-image="{filename}" data-background-size="contain">
            <aside class="notes">{slide.get('script', '')}</aside>
        </section>
        """
    
    # 2. 准备输出路径
    output_dir = os.path.join("static", "output", session_id)
    html_path = os.path.join(output_dir, "index.html")
    
    # 3. 写入 index.html (此时 format 不会再报错了)
    html_content = HTML_TEMPLATE.format(slides_html=slides_html)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # 4. 创建 ZIP 包
    zip_path = os.path.join(output_dir, "presentation.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(html_path, arcname="index.html")
        for slide in slides_data:
            fs_path = slide['image_path'].lstrip('/') 
            filename = os.path.basename(fs_path)
            if os.path.exists(fs_path):
                 zipf.write(fs_path, arcname=filename)
                 
    return html_path, zip_path