# 📚 小说转视频 AI Agent

自动将小说文本转换为带配音、字幕和运镜效果的短视频。

## ✨ 功能特点

- 🎙️ **智能配音** - 使用 Edge TTS 生成自然流畅的中文配音
- 🎨 **AI 绘图** - 基于 AnimagineXL 4.0 + DMD2 LoRA 生成高质量漫画风格图像
- 🎬 **自动运镜** - 智能添加缩放、平移等运镜效果
- 📝 **字幕合成** - 自动生成并嵌入时间轴精准的字幕
- 🔄 **随机转场** - 每个视频使用不同的转场效果
- 🌐 **Web 界面** - 简洁易用的浏览器操作界面

## 🎯 工作流程

```
小说文本 → TTS配音 → AI生成提示词 → SDXL生成图像 → 视频合成
```

### 详细步骤

1. **TTS 生成音频和字幕**
   - 输入：小说文本
   - 输出：`projects/{项目名}/Audio/audio.mp3` 和 `Subtitles.json`

2. **AI 生成图像提示词**
   - 使用 Kimi API 分析字幕，生成分镜脚本
   - 输出：`projects/{项目名}/Prompts.json`

3. **SDXL 生成图像**
   - 使用 AnimagineXL 4.0 + DMD2 LoRA
   - 输出：`projects/{项目名}/Imgs/scene_*.png`

4. **视频合成**
   - 添加运镜效果（缩放、平移）
   - 嵌入字幕
   - 随机转场
   - 输出：`projects/{项目名}/Videos/{项目名}_final.mp4`

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

运行以下脚本自动下载所需模型：

```bash
# 下载 AnimagineXL 4.0
python download_animagine.py

# 下载 DMD2 LoRA（加速生成）
python download_dmd2.py
```

模型将保存到 `sdxl/models/` 目录。

5. **配置 API Key**

在 `config.json` 中配置 Kimi API Key：
```json
{
  "kimi_api_key": "sk-your-kimi-api-key"
}
```

### 使用方法

#### 方式一：Web 界面（推荐）

```bash
python start_web.py
```

然后在浏览器打开 `http://localhost:5000`

#### 方式二：命令行

```bash
python main.py
```

按提示输入项目名称和小说文本。

## 📁 项目结构

```
PIP_Agent/
├── main.py                 # 主程序
├── app.py                  # Web 服务器
├── start_web.py            # Web 启动脚本
├── requirements.txt        # Python 依赖
├── agent流程设计.md         # 流程设计文档
├── PE/                     # Prompt Engineering 模板
│   └── novel_to_prompts_batch.txt
├── sdxl/                   # SDXL 模型目录
│   └── models/
│       ├── animagine-xl-4.0/
│       └── loras/
│           └── dmd2_sdxl_4step_lora.safetensors
└── projects/               # 项目输出目录
    └── {项目名}/
        ├── Audio/          # 音频文件
        │   ├── audio.mp3
        │   └── Subtitles.json
        ├── Prompts.json    # 图像提示词
        ├── Imgs/           # 生成的图像
        │   └── scene_*.png
        └── Videos/         # 最终视频
            └── {项目名}_final.mp4
```

## ⚙️ 配置说明

### SDXL 生成参数

当前使用的最佳配置（经过测试优化）：

```python
模型: AnimagineXL 4.0
LoRA: DMD2 (强度 0.8)
采样器: Euler Ancestral
步数: 12
CFG Scale: 2.5
分辨率: 1024x1024
```

**性能：**
- 单张图片：~13 秒
- 100 张图片：~22 分钟

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

## 🔧 高级功能

### 参数测试

使用测试脚本找到最佳生成参数：

```bash
python test_dmd2_params.py
```

测试不同的采样器、步数、CFG 组合，结果保存到 `temp/` 目录。

### 自定义 Prompt 模板

编辑 `PE/novel_to_prompts_batch.txt` 来自定义提示词生成规则。

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

## 📝 TODO

- [ ] 支持更多 TTS 引擎（Azure TTS、OpenAI TTS）
- [ ] 支持更多图像模型（Flux、SD3）
- [ ] 添加角色表情控制
- [ ] 支持多角色对话场景
- [ ] 优化长视频生成性能
- [ ] 添加视频预览功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [AnimagineXL](https://huggingface.co/cagliostrolab/animagine-xl-4.0) - 高质量动漫风格图像生成
- [DMD2](https://huggingface.co/tianweiy/DMD2) - 快速采样加速
- [Index TTS](https://github.com/index-tts/index-tts) - 免费高质量 TTS
- [Diffusers](https://github.com/huggingface/diffusers) - Stable Diffusion 推理库

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
