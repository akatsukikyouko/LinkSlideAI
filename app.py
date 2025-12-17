from flask import Flask, render_template, request, Response, session, redirect, url_for, stream_with_context
import json
import uuid
import os
import asyncio
from agent_core import PPTAgent

app = Flask(__name__)
app.secret_key = 'z_ppt_2512'


def get_styles_from_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('styles', [{"name": "默认风格", "prompt": ""}])
    except Exception as e:
        print(f"Error reading config: {e}")
        return [{"name": "默认风格", "prompt": ""}]


@app.route('/', methods=['GET', 'POST'])
def index():
    styles = get_styles_from_config()
    return render_template('index.html', styles=styles)
#    if session.get('logged_in'):
#        styles = get_styles_from_config()
#        return render_template('index.html', styles=styles)
#
#    error = None
#    if request.method == 'POST':
#        if request.form.get('password') == 'testpassword':
#            session['logged_in'] = True
#            return redirect(url_for('index'))
#        else:
#            error = "密码错误，请重试"
#
#    return f'''
#    <!DOCTYPE html>
#    <html class="dark">
#    <body style="background-color: #121212; color: #e0e0e0; font-family: sans-serif; height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0;">
#        <form method="post" style="background: #1e1e1e; padding: 40px; border-radius: 12px; border: 1px solid #333; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
#            <h2 style="margin-top: 0; margin-bottom: 20px; font-size: 1.2rem;">LinkSlide 认证</h2>
#            {f'<p style="color: #ff4d4d; font-size: 0.9rem;">{error}</p>' if error else ''}
#            <input type="password" name="password" placeholder="请输入访问密码" autofocus 
#                   style="width: 200px; padding: 10px; border-radius: 6px; border: 1px solid #444; background: #2d2d2d; color: white; outline: none; display: block; margin: 0 auto 20px;">
#            <button type="submit" 
#                    style="background: white; color: black; border: none; padding: 10px 24px; border-radius: 20px; font-weight: bold; cursor: pointer;">
#                进入系统
#            </button>
#        </form>
#    </body>
#    </html>
#    '''



@app.route('/generate_stream', methods=['POST'])
@stream_with_context
def generate_stream():
#    if not session.get('logged_in'):
#        return Response("data: " + json.dumps({'type': 'error', 'message': '认证已失效'}) + "\n\n", mimetype='text/event-stream')

    data = request.json
    topic = data.get('topic', '').strip()
    use_pro = data.get('use_pro', False)
    style_prompt = data.get('style_prompt', '')
    color_hex = data.get('color_hex', '')

    session_id = str(uuid.uuid4())

    final_prompt = topic
    if style_prompt:
        final_prompt += f"\n{style_prompt}"
    if color_hex:
        final_prompt += f"\n主色调请使用 {color_hex}"

    def event_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            wrapper = PPTAgent(session_id, use_pro=use_pro)
            agent = wrapper.get_agent()
            deps = wrapper.get_deps()

            mode = "Pro 模式 (高质量)" if use_pro else "标准模式"
            yield f"data: {json.dumps({'type': 'step', 'status': 'planning', 'message': f'Agent 已启动 ({mode})，正在规划PPT...'})}\n\n"

            # 使用 run_stream_events 获取所有事件
            event_gen = agent.run_stream_events(final_prompt, deps=deps)

            # 用来避免重复发送相同工具进度
            last_tool_progress = set()

            while True:
                try:
                    event = loop.run_until_complete(event_gen.__anext__())

                    # 1. LLM 思考文本增量
                    if hasattr(event, 'delta') and hasattr(event.delta, 'content_delta'):
                        text = event.delta.content_delta
                        if text and text.strip():
                            yield f"data: {json.dumps({'type': 'step', 'status': 'thinking', 'message': text})}\n\n"

                    # 2. 工具调用开始（FunctionToolCallEvent）
                    elif str(type(event)).find('FunctionToolCallEvent') != -1:
                        tool_name = getattr(event.part, 'tool_name', 'unknown')
                        args = {}
                        if hasattr(event.part, 'args'):
                            args = event.part.args
                            if not isinstance(args, dict):
                                args = {}

                        progress_key = f"{tool_name}_{args.get('page_index', '')}"

                        if progress_key not in last_tool_progress:
                            last_tool_progress.add(progress_key)

                            if tool_name == "search":
                                yield f"data: {json.dumps({'type': 'step', 'status': 'searching', 'message': '正在搜索网页信息...'})}\n\n"
                            elif tool_name == "generate_slide":
                                page = args.get('page_index', '1')
                                hint = " (Pro 高质量)" if use_pro else ""
                                yield f"data: {json.dumps({'type': 'step', 'status': 'generating', 'message': f'正在生成第 {page} 页幻灯片{hint}...'})}\n\n"
                            elif tool_name == "finish_ppt":
                                yield f"data: {json.dumps({'type': 'step', 'status': 'bundling', 'message': '正在打包PPT文件...'})}\n\n"

                except StopAsyncIteration:
                    break
                except Exception as inner_e:
                    print(f"Event processing error: {inner_e}")
                    continue

            # 发送每页完成图片
            meta_path = os.path.join("static", "output", session_id, "slides_meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    slides = json.load(f)
                    slides.sort(key=lambda x: x['page'])
                    for slide in slides:
                        yield f"data: {json.dumps({'type': 'slide_done', 'data': slide})}\n\n"

            result_payload = {
                "html_url": f"/static/output/{session_id}/index.html",
                "zip_url": f"/static/output/{session_id}/presentation.zip"
            }
            yield f"data: {json.dumps({'type': 'finish', 'data': result_payload})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': f'运行失败: {str(e)}'})}\n\n"
        finally:
            loop.close()

    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5809, debug=False)