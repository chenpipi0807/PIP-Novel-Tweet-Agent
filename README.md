# 🎬 PIP 小说推文 - AI Agent 智能视频生成系统

> **从小说到视频，一键生成**  
> 基于 AI Agent 的智能决策系统，自动将小说文本转换为带配音、字幕和运镜效果的短视频

<img width="1896" height="904" alt="image" src="https://github.com/user-attachments/assets/77d8d170-ff23-4778-a779-c2f5c57c6efd" />
<img width="1865" height="823" alt="image" src="https://github.com/user-attachments/assets/93fc6905-c43b-418a-a468-6dc3269baf50" />
<img width="1918" height="526" alt="image" src="https://github.com/user-attachments/assets/f844431a-f11c-4828-ae01-2cd828d750da" />
<img width="1902" height="913" alt="image" src="https://github.com/user-attachments/assets/579b0786-d87f-44df-ba91-e6628f0ba539" />

## 🆕 最新更新 (v2.0)

### 🤖 AI Agent 大改造
- ✅ **智能工作流** - Agent 自动检查项目状态，智能决策下一步操作
- ✅ **质量控制** - 自动评估生成质量，不满意自动重新生成
- ✅ **单图重生** - 支持单独重新生成某张图片，无需重跑整个流程
- ✅ **提示词优化** - Agent 可以自动优化提示词提升图片质量
- ✅ **Web 界面升级** - 现代化 ReactPy UI，支持实时编辑和预览

### 🎨 新增功能
- 🖼️ **缩略图网格** - 紧凑展示所有分镜，一目了然
- ✏️ **在线编辑** - 点击编辑按钮，弹窗修改提示词
- 🔄 **单图重生** - 某张图不满意？直接点击重新生成
- 📊 **项目管理** - 完整的项目列表和状态追踪
- 🎯 **质量目标** - 设置目标质量分数，Agent 自动优化到达标

## ✨ 核心特点

### 🤖 AI Agent 模式
- **自动决策** - Agent 自动分析项目状态，决定下一步操作
- **质量驱动** - 基于质量评分自动优化，直到达到目标
- **工具丰富** - 10+ Agent 工具，涵盖检查、生成、优化、修复
- **智能重试** - 失败自动重试，参数自动调整

### 🎨 传统工作流模式
- **固定流程** - 按顺序执行：音频 → 提示词 → 图像 → 视频
- **手动控制** - 每一步都可以手动干预和调整
- **适合调试** - 方便测试和优化各个环节

### 🌐 现代化 Web 界面
- **ReactPy 构建** - 响应式单页应用
- **实时更新** - 任务进度实时显示
- **在线编辑** - 直接在浏览器中编辑提示词
- **缩略图预览** - 网格布局，快速浏览所有图片

## 🎯 工作流程

### Agent 模式（推荐）

```
输入小说 → Agent 自动决策 → 质量评估 → 自动优化 → 输出视频
```

**Agent 工作流程：**
1. 📋 **检查项目状态** - 分析已完成的步骤和存在的问题
2. 🎯 **智能决策** - 决定下一步操作（生成/优化/修复）
3. 🎨 **执行任务** - 调用相应工具完成任务
4. 📊 **质量评估** - 评估生成质量（0-1分）
5. 🔄 **自动优化** - 质量不达标自动重新生成或优化
6. ✅ **达标输出** - 质量达到目标后输出最终视频

### 传统模式

```
小说文本 → TTS配音 → AI生成提示词 → SDXL生成图像 → 视频合成
```

**详细步骤：**

1. **TTS 生成音频和字幕**
   - 输入：小说文本
   - 使用：Edge TTS
   - 输出：`Audio/audio.mp3` + `Subtitles.json`

2. **AI 生成图像提示词**
   - 输入：字幕文件
   - 使用：Kimi API (Moonshot)
   - 输出：`Prompts.json`（包含每个分镜的详细提示词）

3. **SDXL 生成图像**
   - 输入：提示词文件
   - 使用：Prefect Illustrious XL 40 + DMD2 LoRA
   - 输出：`Imgs/scene_*.png`（1024x1024）

4. **视频合成**
   - 输入：图片 + 音频 + 字幕
   - 添加：运镜效果、转场、字幕
   - 输出：`Videos/{项目名}_final.mp4`

## 🚀 快速开始

### 环境要求

- Python 3.10+
- CUDA 兼容的 NVIDIA GPU（推荐 8GB+ VRAM）
- FFmpeg

### 安装

1. **克隆仓库**
```bash
git clone https://github.com/chenpipi0807/PIP-Novel-Tweet-Agent.git
cd PIP_Agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装 FFmpeg**

FFmpeg 用于视频合成，需要单独安装：

```bash
# 自动安装（Windows）
python tools/install_ffmpeg.py

# 或手动下载并解压到 ffmpeg/bin/ 目录
```

详细安装说明请查看 [INSTALL_FFMPEG.md](INSTALL_FFMPEG.md)

4. **下载模型**

需要手动下载以下模型：

**主模型：Prefect Illustrious XL 40**
- 下载地址：[HuggingFace](https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0)
- 保存到：`sdxl/models/prefectIllustriousXL_40/prefectIllustriousXL_40.safetensors`

**加速 LoRA：DMD2**
- 下载地址：[HuggingFace](https://huggingface.co/tianweiy/DMD2)
- 保存到：`sdxl/models/loras/dmd2_sdxl_4step_lora.safetensors`

5. **配置 API Key**

在 `config.json` 中配置 Kimi API Key：
```json
{
  "kimi_api_key": "sk-your-kimi-api-key"
}
```

获取 API Key：[Moonshot AI](https://platform.moonshot.cn/)

### 使用方法

#### 方式一：Web 界面（推荐）

```bash
python start_web.py
```

然后在浏览器打开 `http://localhost:5000`

**Web 界面功能：**
- 📝 创建新项目（输入小说文本）
- 🤖 选择 Agent 模式或传统模式
- 🎯 设置质量目标（Agent 模式）
- 📊 查看项目列表和状态
- 🖼️ 缩略图网格预览所有分镜
- ✏️ 在线编辑提示词
- 🔄 单独重新生成某张图片
- 🎬 预览最终视频

#### 方式二：命令行

```bash
python main.py
```

按提示输入项目名称和小说文本（仅支持传统模式）。

## 📁 项目结构

```
PIP_Agent/
├── main.py                      # 主程序（传统模式）
├── app.py                       # Flask Web 服务器
├── react_ui.py                  # ReactPy 前端界面
├── start_web.py                 # Web 启动脚本
├── agent.py                     # AI Agent 核心逻辑
├── agent_tools.py               # Agent 工具集
├── agent_tools_single_image.py  # 单图重生工具
├── project_inspector.py         # 项目状态检查器
├── requirements.txt             # Python 依赖
├── config.json                  # 配置文件（API Key）
├── PE/                          # Prompt Engineering 模板
│   └── novel_to_prompts_batch.txt
├── tools/                       # 工具模块
│   ├── tts_generator.py         # TTS 生成
│   ├── generate_prompts.py      # 提示词生成
│   ├── kimi_api.py              # Kimi API 封装
│   └── video_composer.py        # 视频合成
├── sdxl/                        # SDXL 模型目录
│   └── models/
│       ├── prefectIllustriousXL_40/
│       │   └── prefectIllustriousXL_40.safetensors
│       └── loras/
│           └── dmd2_sdxl_4step_lora.safetensors
└── projects/                    # 项目输出目录
    └── {项目名}/
        ├── Audio/               # 音频文件
        │   ├── audio.mp3
        │   └── Subtitles.json
        ├── Prompts.json         # 图像提示词
        ├── Imgs/                # 生成的图像
        │   └── scene_*.png
        └── Videos/              # 最终视频
            └── {项目名}_final.mp4
```

## ⚙️ 配置说明

### SDXL 生成参数

当前使用的配置：

```python
模型: Prefect Illustrious XL 40
LoRA: DMD2 (强度 0.8)
调度器: Euler Ancestral
步数: 12 (DMD2) / 20 (标准)
CFG Scale: 2.5 (DMD2) / 7.0 (标准)
分辨率: 1024x1024
Clip Skip: 2
```

**质量标签（Illustrious 专用）：**
```
score_9, score_8_up, score_7_up, masterpiece, best quality, amazing quality, absurdres, newest
```

**负面提示词：**
```
lazyneg, lazyhand, child, censored, lowres, worst quality, low quality, bad anatomy, ...
```

**性能：**
- 单张图片：~10-15 秒（DMD2 加速）
- 100 张图片：~15-25 分钟

### 提示词格式

```
[艺术风格], [自然语言描述], [镜头类型], {角色通配符} [动作+表情], [互动], [地点], [光线], [氛围], masterpiece, best quality, highly detailed, anime
```

**示例：**
```
manga style, a healer waiting for a visitor at clinic entrance, medium shot, {顾衡} standing with anticipation expression, {白菲儿} walking towards him gracefully, warm interaction, traditional chinese street, afternoon golden hour, cinematic, atmospheric, masterpiece, best quality, highly detailed, anime
```

### 角色一致性

系统自动替换角色通配符（如 `{顾衡}`）为详细外貌描述，确保角色在所有分镜中保持一致。

## 🎨 视频效果

- **运镜类型**：缩放、平移、静态
- **转场效果**：淡入淡出、滑动、擦除等（随机选择）
- **字幕样式**：白色文字 + 黑色描边，底部居中
- **帧率**：24 FPS
- **音频**：AAC 128kbps

## 🔧 Agent 工具集

Agent 拥有以下工具来完成任务：

### 核心工作流工具
- `inspect_and_continue` - 🆕 检查项目状态并自动继续（推荐）
- `inspect_project` - 检查项目状态
- `generate_audio` - 生成音频和字幕
- `generate_prompts` - 生成图像提示词
- `generate_images` - 生成所有分镜图像
- `compose_video` - 合成最终视频
- `evaluate_quality` - 评估生成质量

### 图像处理工具
- `regenerate_scene` - 🆕 重新生成单个场景
- `regenerate_scenes_batch` - 🆕 批量重新生成多个场景

### 提示词处理工具
- `refine_prompts` - 🆕 自动优化提示词
- `validate_prompts` - 🆕 验证提示词质量

### 质量控制工具
- `check_image_quality` - 🆕 检查图像质量
- `auto_fix_issues` - 🆕 自动修复问题

### 参数调整工具
- `adjust_parameters` - 根据质量评估调整生成参数

## 🎨 高级功能

### 自定义 Prompt 模板

编辑 `PE/novel_to_prompts_batch.txt` 来自定义提示词生成规则。

### 质量目标设置

在 Agent 模式下，可以设置质量目标（0.0-1.0）：
- `0.6` - 基本可用
- `0.7` - 良好质量（推荐）
- `0.8` - 高质量
- `0.9+` - 极致质量（可能需要多次优化）

## 📊 性能优化

1. **DMD2 LoRA** - 将生成步数从 28 步降至 12 步，速度提升 2.3 倍
2. **Attention Slicing** - 降低 VRAM 占用
3. **VAE Slicing** - 优化大图生成
4. **批量处理** - 自动跳过已生成的图像

## 🐛 常见问题

### Q: CUDA out of memory
**A:** 降低批量大小或使用更小的分辨率（如 768x768）

### Q: 生成的图片质量不好
**A:** 
- 检查提示词是否遵循格式规范
- 尝试调整 CFG Scale（推荐 2.0-3.0）
- 增加采样步数（推荐 12-16）

### Q: 字幕时间轴不准确
**A:** Edge TTS 的时间戳可能有偏差，可以在 `Subtitles.json` 中手动调整

### Q: 视频合成失败
**A:** 确保安装了 FFmpeg 并添加到系统 PATH

## 📝 开发路线

### 已完成 ✅
- [x] AI Agent 智能决策系统
- [x] 质量评估和自动优化
- [x] 单图重生功能
- [x] Web 界面升级（ReactPy）
- [x] 项目状态检查器
- [x] 在线编辑提示词
- [x] 缩略图网格预览

### 进行中 🚧
- [ ] 优化 SDXL 图像生成质量
- [ ] 改进提示词生成算法
- [ ] 增强 Agent 决策能力

### 计划中 📋
- [ ] 支持更多图像模型（Flux、SDXL Turbo）
- [ ] 支持更多 TTS 引擎（Azure TTS、OpenAI TTS）
- [ ] 添加角色表情控制
- [ ] 支持多角色对话场景
- [ ] 视频效果模板库
- [ ] 批量项目管理

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Illustrious XL](https://huggingface.co/OnomaAIResearch/Illustrious-xl-early-release-v0) - 高质量动漫风格图像生成
- [DMD2](https://huggingface.co/tianweiy/DMD2) - 快速采样加速
- [Moonshot AI (Kimi)](https://www.moonshot.cn/) - 强大的 LLM API
- [Edge TTS](https://github.com/rany2/edge-tts) - 免费高质量 TTS
- [Diffusers](https://github.com/huggingface/diffusers) - Stable Diffusion 推理库
- [ReactPy](https://reactpy.dev/) - Python Web 框架

## 📊 项目统计

- **代码行数**：~5000+ 行
- **Agent 工具**：15+ 个
- **支持的模型**：SDXL 系列
- **生成速度**：~10-15 秒/张（DMD2 加速）

## 📧 联系方式

- **GitHub Issues**：[提交问题](https://github.com/chenpipi0807/PIP-Novel-Tweet-Agent/issues)
- **项目主页**：[PIP-Novel-Tweet-Agent](https://github.com/chenpipi0807/PIP-Novel-Tweet-Agent)

## 📜 更新日志

### v2.0 (2025-10-25)
- 🤖 重构为 AI Agent 架构
- ✨ 新增 10+ Agent 工具
- 🎨 Web 界面全面升级
- 🔄 支持单图重生
- ✏️ 在线编辑提示词
- 📊 项目状态检查器

### v1.0 (2025-10-19)
- 🎉 初始版本发布
- 🎙️ TTS 音频生成
- 🎨 SDXL 图像生成
- 🎬 视频合成
- 🌐 基础 Web 界面

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
