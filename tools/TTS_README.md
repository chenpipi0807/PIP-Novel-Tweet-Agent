# IndexTTS 1.5 短剧TTS工具使用说明

## 📋 目录

- [简介](#简介)
- [环境配置](#环境配置)
- [快速开始](#快速开始)
- [详细使用](#详细使用)
- [API参考](#api参考)
- [常见问题](#常见问题)

---

## 简介

这是一个基于IndexTTS 1.5的短剧语音合成工具，专为短剧视频制作设计。支持：

- ✅ **零样本音色克隆** - 只需一段参考音频即可克隆音色
- ✅ **多角色支持** - 轻松管理多个角色的音色
- ✅ **批量合成** - 高效处理大量台词
- ✅ **GPU加速** - 支持NVIDIA GPU加速推理
- ✅ **中英文混合** - 支持中英文混合文本

---

## 环境配置

### 1. 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **GPU**: NVIDIA GPU (推荐，显存 ≥ 6GB)
- **CUDA**: 11.8 或更高版本

### 2. 安装依赖

```powershell
# 进入项目目录
cd C:\PIP_Agent

# 安装PyTorch (CUDA版本)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装IndexTTS依赖
cd index-tts
pip install -e .

# 安装TTS工具依赖
cd ..\tools
pip install -r requirements_tts.txt
```

### 3. 验证GPU

```powershell
python
>>> import torch
>>> print(torch.cuda.is_available())  # 应该输出 True
>>> print(torch.cuda.get_device_name(0))  # 显示GPU型号
>>> exit()
```

### 4. 目录结构

```
C:\PIP_Agent\
├── models/                 # IndexTTS 1.5 模型文件
│   ├── config.yaml
│   ├── gpt.pth
│   ├── dvae.pth
│   ├── bigvgan_generator.pth
│   └── ...
├── Timbre/                 # 音色参考音频库
│   ├── 温柔学姐.mp3
│   ├── 温润青年.mp3
│   ├── 播音中年男.mp3
│   └── ...
├── index-tts/              # IndexTTS源码
└── tools/                  # TTS工具
    ├── tts_tool.py         # 主工具脚本
    ├── tts_example.py      # 使用示例
    ├── requirements_tts.txt
    └── TTS_README.md       # 本文档
```

---

## 快速开始

### 方式1: 命令行使用

```powershell
cd C:\PIP_Agent\tools

# 查看所有可用音色
python tts_tool.py --list-timbres

# 合成单句
python tts_tool.py --text "大家好，我是短剧配音演员" --timbre "温柔学姐" --output output.wav

# 批量合成（使用JSON文件）
python tts_tool.py --batch scripts.json
```

### 方式2: Python脚本使用

```python
from tts_tool import ShortDramaTTS

# 初始化
tts = ShortDramaTTS()

# 合成语音
tts.synthesize(
    text="大家好，我是短剧配音演员",
    timbre="温柔学姐",
    output_path="output.wav"
)
```

### 方式3: 运行示例

```powershell
cd C:\PIP_Agent\tools
python tts_example.py
```

---

## 详细使用

### 1. 查看可用音色

#### 命令行方式

```powershell
python tts_tool.py --list-timbres
```

#### Python方式

```python
from tts_tool import ShortDramaTTS

tts = ShortDramaTTS()
timbres = tts.list_timbres()

for timbre in timbres:
    print(timbre)
```

### 2. 单句合成

#### 基本用法

```python
from tts_tool import ShortDramaTTS

tts = ShortDramaTTS()

# 使用Timbre文件夹中的音色
tts.synthesize(
    text="今天天气真不错",
    timbre="温柔学姐",
    output_path="output.wav"
)
```

#### 使用自定义音色

```python
# 使用自己的音频文件作为音色参考
tts.synthesize(
    text="今天天气真不错",
    timbre_name="",  # 留空
    output_path="output.wav",
    timbre_audio_path="path/to/your/voice.wav"
)
```

### 3. 多角色对话

```python
from tts_tool import ShortDramaTTS
from pathlib import Path

tts = ShortDramaTTS()

# 定义角色和对话
dialogue = [
    {"character": "男主", "timbre": "温润青年", "text": "你好，很高兴认识你。"},
    {"character": "女主", "timbre": "温柔学姐", "text": "我也是，你好。"},
    {"character": "旁白", "timbre": "播音中年男", "text": "两人相视一笑。"}
]

# 逐句合成
output_dir = Path("outputs/dialogue")
output_dir.mkdir(parents=True, exist_ok=True)

for i, line in enumerate(dialogue, 1):
    output_file = output_dir / f"{i:02d}_{line['character']}.wav"
    tts.synthesize(
        text=line['text'],
        timbre=line['timbre'],
        output_path=str(output_file)
    )
```

### 4. 批量合成

#### 准备JSON脚本文件

创建 `scripts.json`:

```json
[
    {
        "text": "第一集：命运的相遇",
        "timbre": "播音中年男",
        "filename": "ep01_title.wav"
    },
    {
        "text": "在一个阳光明媚的早晨，故事开始了。",
        "timbre": "播音中年男",
        "filename": "ep01_narration_01.wav"
    },
    {
        "text": "你好，我是李明。",
        "timbre": "温润青年",
        "filename": "ep01_male_01.wav"
    }
]
```

#### 执行批量合成

```powershell
# 命令行方式
python tts_tool.py --batch scripts.json
```

```python
# Python方式
from tts_tool import ShortDramaTTS
import json

tts = ShortDramaTTS()

with open('scripts.json', 'r', encoding='utf-8') as f:
    scripts = json.load(f)

success_files = tts.batch_synthesize(scripts, "outputs")
print(f"成功合成 {len(success_files)} 个文件")
```

### 5. 完整工作流示例

```python
from tts_tool import ShortDramaTTS
from pathlib import Path

# 初始化
tts = ShortDramaTTS()

# 短剧配置
episode_config = {
    "episode": 1,
    "scene": 1,
    "characters": {
        "narrator": "播音中年男",
        "hero": "温润青年",
        "heroine": "温柔学姐"
    },
    "lines": [
        {"speaker": "narrator", "text": "第一集第一场：咖啡厅"},
        {"speaker": "hero", "text": "你好，可以坐这里吗？"},
        {"speaker": "heroine", "text": "当然可以，请坐。"}
    ]
}

# 创建输出目录
output_dir = Path(f"outputs/ep{episode_config['episode']:02d}_scene{episode_config['scene']:02d}")
output_dir.mkdir(parents=True, exist_ok=True)

# 逐句合成
for i, line in enumerate(episode_config['lines'], 1):
    speaker = line['speaker']
    timbre = episode_config['characters'][speaker]
    text = line['text']
    output_file = output_dir / f"{i:03d}_{speaker}.wav"
    
    print(f"[{i}/{len(episode_config['lines'])}] {speaker}: {text}")
    tts.synthesize(text, timbre, str(output_file))

print(f"完成！文件保存在: {output_dir}")
```

---

## API参考

### ShortDramaTTS 类

#### 初始化

```python
tts = ShortDramaTTS(
    model_dir=None,      # 模型文件夹路径，默认 ../models
    config_path=None,    # 配置文件路径，默认 ../models/config.yaml
    timbre_dir=None,     # 音色文件夹路径，默认 ../Timbre
    use_gpu=True         # 是否使用GPU
)
```

#### 方法

##### list_timbres()

列出所有可用的音色名称。

```python
timbres = tts.list_timbres()
# 返回: List[str]
```

##### get_timbre_path(timbre_name)

根据音色名称获取音频文件路径。

```python
path = tts.get_timbre_path("温柔学姐")
# 返回: Optional[str]
```

##### synthesize(text, timbre_name, output_path, timbre_audio_path=None)

合成单句语音。

**参数:**
- `text` (str): 要合成的文本
- `timbre_name` (str): 音色名称
- `output_path` (str): 输出文件路径
- `timbre_audio_path` (Optional[str]): 自定义音色参考音频路径

**返回:** bool - 是否成功

```python
success = tts.synthesize(
    text="你好",
    timbre_name="温柔学姐",
    output_path="output.wav"
)
```

##### batch_synthesize(scripts, output_dir)

批量合成语音。

**参数:**
- `scripts` (List[Dict]): 脚本列表，每个元素包含:
  - `text`: 文本内容
  - `timbre`: 音色名称
  - `filename`: 输出文件名（可选）
- `output_dir` (str): 输出文件夹路径

**返回:** List[str] - 成功生成的文件路径列表

```python
scripts = [
    {"text": "第一句", "timbre": "温柔学姐", "filename": "01.wav"},
    {"text": "第二句", "timbre": "温润青年", "filename": "02.wav"}
]
success_files = tts.batch_synthesize(scripts, "outputs")
```

---

## 常见问题

### Q1: 如何添加新的音色？

**A:** 将音频文件（.wav, .mp3, .flac）放入 `C:\PIP_Agent\Timbre` 文件夹即可。文件名（不含扩展名）将作为音色名称。

**建议:**
- 音频时长: 3-10秒
- 音质: 清晰，无背景噪音
- 内容: 包含完整的句子，语调自然

### Q2: GPU显存不足怎么办？

**A:** 
1. 关闭其他占用GPU的程序
2. 使用CPU模式（速度较慢）:
   ```python
   tts = ShortDramaTTS(use_gpu=False)
   ```
3. 减少批量处理的数量

### Q3: 合成的语音不自然？

**A:** 
1. 检查参考音频质量
2. 确保文本有合适的标点符号
3. 避免过长的句子（建议 ≤ 50字）
4. 尝试不同的音色参考

### Q4: 支持哪些文本格式？

**A:** 
- 纯中文
- 纯英文
- 中英文混合
- 支持标点符号控制停顿

### Q5: 如何控制语速和语调？

**A:** IndexTTS 1.5 会自动从参考音频中学习语速和语调。选择合适的参考音频很重要。

### Q6: 批量合成时如何查看进度？

**A:** 工具会在控制台输出详细的进度信息：

```
[1/10] 处理中...
正在合成: 第一句话...
合成完成: outputs/01.wav
```

### Q7: 可以用于商业项目吗？

**A:** 请查看IndexTTS的开源协议。建议联系 indexspeech@bilibili.com 了解商业授权。

### Q8: 如何提高合成速度？

**A:** 
1. 使用GPU加速
2. 批量合成而非逐句合成
3. 使用SSD存储
4. 确保CUDA版本正确

### Q9: 支持实时合成吗？

**A:** IndexTTS 1.5 主要用于离线合成，不适合实时场景。

### Q10: 如何处理特殊字符和数字？

**A:** 
- 数字会自动转换为中文读法
- 特殊符号可能影响合成，建议使用标准标点
- 可以使用拼音标注来控制发音

---

## 技术支持

- **GitHub**: https://github.com/index-tts/index-tts
- **QQ群**: 663272642 (No.4), 1013410623 (No.5)
- **Discord**: https://discord.gg/uT32E7KDmy
- **Email**: indexspeech@bilibili.com

---

## 更新日志

### v1.0 (2025-01-19)
- ✅ 初始版本
- ✅ 支持IndexTTS 1.5
- ✅ 命令行和Python API
- ✅ 批量合成功能
- ✅ 完整示例代码

---

## 许可证

本工具基于IndexTTS项目，请遵守相关开源协议。
