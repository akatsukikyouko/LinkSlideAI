# LinkSlideAI

一个基于生图 AI 的全自动 PPT 生成工具，通过自然语言描述即可生成精美的演示文稿。支持使用模搭的z-image api接口和火山引擎的Seedream4.5 api接口。通过调用智谱联网搜索获取世界知识。

## ✨ 特性

- 🚀 **一键生成**: 输入主题，AI 自动规划并生成完整 PPT
- 🎨 **多种风格**: 内置 7 种专业设计风格（极简主义、卡片UI、时尚杂志等）
- 🎯 **双模式**: 标准模式快速生成，Pro 模式高质量输出
- 🌈 **自定义配色**: 支持自定义主色调
- 📦 **多格式导出**: 支持 HTML 在线预览和 ZIP 下载

## 🏗️ 技术架构

- **后端**: Flask + Pydantic AI
- **AI 模型**: 支持多种大语言模型（OpenAI 兼容）
- **图像生成**: ModelScope + 火山引擎
- **前端**: 原生 HTML/CSS/JavaScript + Tailwind CSS
- **搜索功能**: MCP 协议联网搜索


## 🚀 快速开始

### 配置 API 密钥
   
编辑 `config.json` 文件，填入你的 API 密钥：

### 使用启动脚本（推荐）

Windows 用户可以直接运行：

```bash
start_server.bat
```

脚本会自动：
- 检查 Python 环境
- 安装 uv 包管理器
- 创建虚拟环境
- 安装依赖包
- 启动服务

其他系统用户请自行将该命令行写成.sh等或者手动运行

## 访问应用
   打开浏览器访问：http://localhost:5809

## ⚙️ 配置说明

### API 配置

在 `config.json` 中配置以下服务：

| 服务 | 说明 | 示例 |
|------|------|------|
| `llm` | 大语言模型（用于生成PPT内容） | 智谱 GLM、OpenAI 等 |
| `modelscope` | 图像生成模型 | z-image |
| `image_tool_pro` | 高质量图像生成（Pro模式） | seedream4.5 |
| `mcp` | 联网搜索服务 | 智谱 MCP |

### 风格配置

内置 7 种设计风格：

- **无**: 默认风格，支持自己在prompt指定风格
- **极简主义**: 少即是多，高对比度，科技感
- **卡片UI**: 现代APP界面，圆角卡片，柔和渐变
- **时尚杂志**: 艺术海报风格，不对称构图
- **航空杂志**: 老钱风，低调奢华，商务格调
- **温馨插画**: 手绘质感，治愈风格
- **儿童读物**: 色彩斑斓，卡通风格

可以在 `config.json` 的 `styles` 数组中自定义风格。

## 🎯 使用指南

1. **输入主题**: 在输入框中输入 PPT 主题
2. **选择模式**: 
   - 标准模式：快速生成，适合一般需求
   - Pro 模式：高质量输出，适合重要演示
3. **选择风格**: 从下拉菜单选择设计风格
4. **设置配色**: 点击颜色选择器自定义主色调（可选）
5. **生成**: 点击发送按钮开始生成
6. **预览和下载**: 实时预览生成结果，完成后可下载 ZIP 包

## 📁 项目结构

```
LinkSlideAI/
├── agent_core.py          # AI 核心逻辑
├── app.py                 # Flask Web 应用
├── config.json            # 配置文件
├── image_tool.py          # 标准图像生成工具
├── image_tool_pro.py      # Pro 图像生成工具
├── ppt_renderer.py        # PPT 渲染器
├── requirements.txt       # Python 依赖
├── start_server.bat      # Windows 启动脚本
├── static/                # 静态文件
│   └── output/           # 生成的 PPT 输出
└── templates/             # HTML 模板
    └── index.html        # 主界面
```

## 🔧 开发说明

### 核心组件

- **PPTAgent**: AI 智能体，负责整体流程控制
- **图像生成工具**: 支持标准模式和 Pro 模式的图像生成
- **PPT 渲染器**: 将生成的图片打包成 HTML 和 ZIP 格式

### 扩展开发

**添加新风格**: 在 `config.json` 的 `styles` 数组中可以添加新的自定义风格。