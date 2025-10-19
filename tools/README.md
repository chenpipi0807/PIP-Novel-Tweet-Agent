# 🎬 IndexTTS 1.5 短剧制作工具集

完整的短剧/有声小说制作工具，基于IndexTTS 1.5。

---

## 📦 工具列表

### 1. TTS基础工具 (`tts_tool.py`)

**功能：** 单句/批量语音合成

**使用：**
```python
from tts_tool import ShortDramaTTS

tts = ShortDramaTTS()
tts.synthesize(text="你好", timbre_name="温柔学姐", output_path="out.wav")
```

**文档：** `TTS_README.md`

---

### 2. 小说转短剧工具 (`novel_to_drama.py`) ⭐ 新功能

**功能：** 
- ✅ 自动拆分长文本
- ✅ 生成音频文件（每句一个）
- ✅ 生成字幕文件（SRT + JSON）
- ✅ 自动计算时间轴
- ✅ 项目文件管理

**使用：**
```python
from novel_to_drama import NovelToDrama

converter = NovelToDrama(timbre_name="播音中年男")
converter.process_novel(
    text=your_text,
    project_name="my_drama"
)
```

**输出：**
```
projects/my_drama/
├── audio/              # 音频文件
│   ├── my_drama_0001.wav
│   ├── my_drama_0002.wav
│   └── ...
├── my_drama.srt       # SRT字幕
├── my_drama.json      # JSON字幕
└── project_info.json  # 项目信息
```

**文档：** `NOVEL_TO_DRAMA.md`

---

## 🚀 快速开始

### 处理你的test.txt

```powershell
cd C:\PIP_Agent\tools
python process_test.py
```

这会自动：
1. 读取`test.txt`（你的长文本）
2. 拆分成句子
3. 为每句生成音频
4. 生成字幕文件
5. 保存到`projects/test/`

### 自定义处理

```python
from novel_to_drama import NovelToDrama

# 读取文本
with open('your_novel.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 处理
converter = NovelToDrama()
converter.process_novel(
    text=text,
    project_name="my_project",
    timbre_name="播音中年男",
    max_sentence_length=50
)
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| `README.md` | 本文档 - 工具总览 |
| `TTS_README.md` | TTS基础工具详细文档 |
| `NOVEL_TO_DRAMA.md` | 小说转短剧工具详细文档 |
| `SUCCESS.md` | 安装成功指南 |
| `QUICKSTART.md` | 快速开始 |
| `FINAL_SUMMARY.md` | 完整总结 |

---

## 🎯 使用场景

### 场景1：有声小说制作

```python
from novel_to_drama import NovelToDrama

# 读取小说
with open('novel.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 使用旁白音色
converter = NovelToDrama(timbre_name="播音中年男")
converter.process_novel(text, "my_novel")

# 得到：
# - 每句话的音频文件
# - 完整的字幕文件
# - 时间轴信息
```

### 场景2：短剧配音

```python
from tts_tool import ShortDramaTTS

tts = ShortDramaTTS()

# 多角色对话
dialogue = [
    {"text": "你好", "timbre": "温润青年", "file": "01.wav"},
    {"text": "你好", "timbre": "温柔学姐", "file": "02.wav"},
]

for line in dialogue:
    tts.synthesize(
        text=line['text'],
        timbre_name=line['timbre'],
        output_path=line['file']
    )
```

### 场景3：批量处理

```python
from novel_to_drama import NovelToDrama
from pathlib import Path

converter = NovelToDrama()

# 处理文件夹中所有txt
for txt_file in Path("novels").glob("*.txt"):
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()
    converter.process_novel(text, txt_file.stem)
```

---

## 🎨 可用音色（58个）

### 推荐旁白音色
- **播音中年男** - 专业旁白
- **新闻女声** - 正式场合
- **电台男主播** - 磁性声音

### 角色音色
- **男主**: 温润青年、温润男声
- **女主**: 温柔学姐、温暖少女、甜美女声
- **反派**: 沉稳高管
- **配角**: 傲娇御姐、清澈弟弟、软糯女孩

### 游戏角色
- 原神系列、星穹铁道系列、恋与深空系列
- FF7系列、鬼灭之刃系列

**查看完整列表：**
```python
from tts_tool import ShortDramaTTS
tts = ShortDramaTTS()
print(tts.list_timbres())
```

---

## ⚙️ 系统信息

- **Python**: 3.12.3
- **GPU**: NVIDIA RTX 3060 (12GB)
- **模型**: IndexTTS 1.5
- **推理速度**: RTF 0.46（比实时快2倍）

---

## 📊 性能参考

| 任务 | 时间 |
|------|------|
| 单句合成 | ~2秒 |
| 100句文本 | ~3-5分钟 |
| 1000句文本 | ~30-50分钟 |

---

## 🔧 工具文件

### 核心工具
- `tts_tool.py` - TTS基础工具类
- `novel_to_drama.py` - 小说转短剧工具
- `patch_front.py` - Python 3.12兼容补丁

### 测试脚本
- `test_simple.py` - 环境测试
- `test_tts.py` - TTS快速测试
- `process_test.py` - 处理test.txt示例

### 示例代码
- `tts_example.py` - 6个使用示例
- `scripts_template.json` - 批量脚本模板

### 配置文件
- `requirements_tts.txt` - 依赖列表
- `install_deps.ps1` - 依赖安装脚本

---

## 💡 常见问题

### Q: 如何处理超长文本？

**A:** 使用`novel_to_drama.py`，它会自动拆分并生成时间轴。

### Q: 如何更换音色？

**A:** 使用`timbre_name`参数指定音色名称。

### Q: 生成的音频如何合并？

**A:** 参考`NOVEL_TO_DRAMA.md`中的"合并音频"章节。

### Q: 字幕时间不准确？

**A:** 时间轴是根据实际音频计算的，应该准确。检查音频文件是否正常。

---

## 📞 技术支持

- **QQ群**: 663272642, 1013410623
- **Discord**: https://discord.gg/uT32E7KDmy
- **Email**: indexspeech@bilibili.com

---

## 🎊 开始使用

### 步骤1：测试环境

```powershell
cd C:\PIP_Agent\tools
python test_simple.py
```

### 步骤2：处理你的文本

```powershell
python process_test.py
```

### 步骤3：查看结果

```
projects/test/
├── audio/           # 所有音频文件
├── test.srt        # 字幕文件
└── test.json       # 时间轴数据
```

---

**开始制作你的短剧/有声小说吧！** 🎬📚✨
