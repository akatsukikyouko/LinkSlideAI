import json
import json_repair
import os
import asyncio
from dataclasses import dataclass
from datetime import datetime

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.mcp import MCPServerStreamableHTTP

from image_tool import generate_slide_image_tool
from image_tool_pro import generate_slide_image_tool_pro
from ppt_renderer import create_presentation


def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json_repair.load(f)


@dataclass
class Deps:
    session_id: str
    use_pro: bool


class PPTAgent:
    def __init__(self, session_id: str, use_pro: bool = False):
        cfg = load_config()
        self.session_id = session_id
        self.use_pro = use_pro

        self.deps = Deps(
            session_id=session_id,
            use_pro=use_pro
        )

        # 创建 MCP server
        mcp_server = MCPServerStreamableHTTP(
            url=cfg['mcp']['url'],
            headers={"Authorization": cfg['mcp']['api_key']}
        )

        # 创建模型
        model = OpenAIChatModel(
            cfg['llm']['model_id'],
            provider=OpenAIProvider(
                base_url=cfg['llm']['base_url'],
                api_key=cfg['llm']['api_key'],
            ),
        )


        self.agent = Agent(
            model=model,
            system_prompt=f"""
            你是一个全自动的PPT生成智能体。
            Session ID: {session_id}
            生图模式: {'Pro模式 (高质量)' if use_pro else '标准模式'}

            执行流程：
            1. 如有需要，直接使用 search 工具搜索最新信息。
            2. 规划PPT结构（建议5-8页），详细思考每页标题、内容与画面。
            3. 依次调用 generate_slide 生成每一页（page_index 从1开始递增）。
               - prompt 必须极度详细，至少200字，包含完整文字、布局、背景、颜色、风格等。
               - script 为该页演讲稿。
            4. 全部生成完毕后，必须调用 finish_ppt 打包。

            请多输出思考过程，每一步向用户汇报进度。
            当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            **注意**
            - `generate_slide` 工具生图提示词必须十分详细，要非常长，细节描述非常精确，至少200字以上。并一定要要求文字准确无错别字，清晰可见。
            - 在生成的最后，不需要告诉用户在哪下载，因为结果会自动推送到前端。
            """,
            toolsets=[mcp_server],  # MCP 搜索工具
            # 移除 deps=...
        )

        # 自定义工具
        @self.agent.tool
        async def generate_slide(ctx: RunContext[Deps], prompt: str, script: str, page_index: int) -> str:
            if ctx.deps.use_pro:
                print(f"--- Using Pro Image Tool for Slide {page_index} ---")
                image_path = generate_slide_image_tool_pro(prompt, page_index, ctx.deps.session_id)
            else:
                print(f"--- Using Standard Image Tool for Slide {page_index} ---")
                image_path = generate_slide_image_tool(prompt, page_index, ctx.deps.session_id)

            data_dir = os.path.join("static", "output", ctx.deps.session_id)
            os.makedirs(data_dir, exist_ok=True)
            meta_file = os.path.join(data_dir, "slides_meta.json")

            slide_data = {
                "page": page_index,
                "image_path": image_path,
                "script": script
            }

            existing = []
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                except:
                    existing = []

            existing.append(slide_data)
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)

            return f"第 {page_index} 页已生成：{image_path}"

        @self.agent.tool
        async def finish_ppt(ctx: RunContext[Deps]) -> str:
            data_dir = os.path.join("static", "output", ctx.deps.session_id)
            meta_file = os.path.join(data_dir, "slides_meta.json")

            if not os.path.exists(meta_file):
                return "Error: 未生成任何幻灯片"

            with open(meta_file, 'r', encoding='utf-8') as f:
                slides = json.load(f)

            slides.sort(key=lambda x: x['page'])
            html_path, zip_path = create_presentation(ctx.deps.session_id, slides)

            return json.dumps({
                "html_url": f"/static/output/{ctx.deps.session_id}/index.html",
                "zip_url": f"/static/output/{ctx.deps.session_id}/presentation.zip"
            })

    def get_agent(self):
        return self.agent

    def get_deps(self):
        return self.deps