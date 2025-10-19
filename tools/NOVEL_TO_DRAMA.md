# 📚 小说转短剧工具使用说明

## 功能介绍

这个工具可以将长篇小说文本自动转换为短剧音频+字幕，包括：

✅ **自动拆分文本** - 按标点符号智能拆分长文本  
✅ **生成音频文件** - 每句话一个独立的音频文件  
✅ **时间轴计算** - 自动计算每句的开始/结束时间  
✅ **字幕生成** - 生成SRT和JSON两种格式的字幕  
✅ **项目管理** - 自动创建项目文件夹，组织所有文件  

---

## 快速开始

### 方法1：使用Python脚本

```python
from novel_to_drama import NovelToDrama

# 读取小说文本
with open('your_novel.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# 创建转换器
converter = NovelToDrama(timbre_name="播音中年男")

# 处理文本
converter.process_novel(
    text=text,
    project_name="my_drama",  # 项目名称
    timbre_name="播音中年男",  # 音色
    max_sentence_length=50     # 单句最大长度
)
```

### 方法2：命令行

```powershell
cd C:\PIP_Agent\tools

# 处理文本文件
python novel_to_drama.py --input your_novel.txt --project my_drama --timbre 播音中年男

# 查看可用音色
python novel_to_drama.py --list-timbres
```

### 方法3：处理test.txt

```powershell
cd C:\PIP_Agent\tools
python process_test.py
```

---

## 输出结构

处理完成后会生成如下目录结构：

```
projects/
└── my_drama/                    # 项目文件夹
    ├── audio/                   # 音频文件夹
    │   ├── my_drama_0001.wav   # 第1句音频
    │   ├── my_drama_0002.wav   # 第2句音频
    │   ├── my_drama_0003.wav   # 第3句音频
    │   └── ...
    ├── my_drama.srt            # SRT字幕文件
    ├── my_drama.json           # JSON字幕文件
    ├── my_drama_original.txt   # 原始文本
    └── project_info.json       # 项目信息
```

---

## 字幕格式说明

### SRT格式 (my_drama.srt)

```srt
1
00:00:00,000 --> 00:00:03,450
下班路上，一个穿蓝色长袍的老道儿叫住我。

2
00:00:03,450 --> 00:00:07,200
竟准确说出我毕业院校和工作情况。

3
00:00:07,200 --> 00:00:10,800
还留下句"先上后下，南上北下"就走了。
```

### JSON格式 (my_drama.json)

```json
{
  "total_duration": 180.5,
  "total_sentences": 50,
  "subtitles": [
    {
      "index": 1,
      "text": "下班路上，一个穿蓝色长袍的老道儿叫住我。",
      "filename": "my_drama_0001.wav",
      "start_time": 0.0,
      "end_time": 3.45,
      "duration": 3.45
    },
    {
      "index": 2,
      "text": "竟准确说出我毕业院校和工作情况。",
      "filename": "my_drama_0002.wav",
      "start_time": 3.45,
      "end_time": 7.2,
      "duration": 3.75
    }
  ]
}
```

---

## 参数说明

### NovelToDrama 类

```python
converter = NovelToDrama(timbre_name="播音中年男")
```

**参数：**
- `timbre_name`: 默认音色名称

### process_novel 方法

```python
converter.process_novel(
    text="...",              # 小说文本
    project_name="test",     # 项目名称
    timbre_name="播音中年男", # 音色（可选）
    max_sentence_length=50   # 单句最大长度
)
```

**参数：**
- `text`: 要处理的文本内容
- `project_name`: 项目名称（用作文件夹名和文件前缀）
- `timbre_name`: 音色名称（可选，默认使用初始化时的音色）
- `max_sentence_length`: 单句最大字数，超过会按逗号再拆分

---

## 推荐音色

### 旁白类
- **播音中年男** - 专业旁白，推荐用于小说朗读
- **新闻女声** - 正式场合
- **电台男主播** - 磁性声音

### 角色类
- **温润青年** - 男主角
- **温柔学姐** - 女主角
- **沉稳高管** - 成熟角色
- **甜美女声** - 可爱角色

---

## 使用技巧

### 1. 文本预处理

建议先清理文本：
- 删除多余的空行
- 统一标点符号（全角/半角）
- 删除特殊符号

### 2. 控制句子长度

```python
# 短句模式（适合快节奏）
max_sentence_length=30

# 标准模式（推荐）
max_sentence_length=50

# 长句模式（适合慢节奏）
max_sentence_length=80
```

### 3. 多角色处理

如果需要不同角色不同音色，可以手动处理：

```python
from novel_to_drama import NovelToDrama

converter = NovelToDrama()

# 拆分文本
sentences = converter.split_text(text)

# 为不同句子指定不同音色
for i, sentence in enumerate(sentences):
    # 判断角色（根据你的逻辑）
    if "我说" in sentence:
        timbre = "温润青年"
    elif "她说" in sentence:
        timbre = "温柔学姐"
    else:
        timbre = "播音中年男"
    
    # 生成音频
    converter.tts.synthesize(
        text=sentence,
        timbre_name=timbre,
        output_path=f"audio/{i:04d}.wav"
    )
```

### 4. 批量处理多个文件

```python
from pathlib import Path
from novel_to_drama import NovelToDrama

converter = NovelToDrama()

# 处理文件夹中的所有txt文件
input_dir = Path("novels")
for txt_file in input_dir.glob("*.txt"):
    with open(txt_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    project_name = txt_file.stem  # 使用文件名作为项目名
    converter.process_novel(text, project_name)
```

---

## 性能参考

基于你的配置（RTX 3060, 12GB）：

- **处理速度**: 约2秒/句
- **100句文本**: 约3-5分钟
- **1000句文本**: 约30-50分钟
- **实时率**: 0.46（比实时快2倍）

---

## 常见问题

### Q1: 句子拆分不理想怎么办？

**A:** 调整`max_sentence_length`参数，或手动预处理文本。

### Q2: 生成的音频太长/太短？

**A:** 这是正常的，TTS会根据文本内容自动调整语速。

### Q3: 如何合并所有音频？

**A:** 可以使用ffmpeg或Python的pydub库：

```python
from pydub import AudioSegment

# 读取所有音频
audio_files = sorted(Path("audio").glob("*.wav"))
combined = AudioSegment.empty()

for audio_file in audio_files:
    audio = AudioSegment.from_wav(str(audio_file))
    combined += audio

# 导出
combined.export("final.mp3", format="mp3")
```

### Q4: 字幕时间不准确？

**A:** 时间轴是根据实际音频文件计算的，应该是准确的。如果有问题，检查音频文件是否正常生成。

### Q5: 可以暂停和恢复吗？

**A:** 目前不支持。建议分段处理大文件。

---

## 进阶功能

### 自定义时间轴

```python
# 获取时间轴信息
timeline = converter.generate_audio_files(sentences, output_dir)

# 修改时间轴（例如添加间隔）
for item in timeline:
    item['start_time'] += 0.5  # 每句前加0.5秒
    item['end_time'] += 0.5

# 重新生成字幕
converter.generate_srt(timeline, "custom.srt")
converter.generate_json(timeline, "custom.json")
```

### 添加背景音乐

```python
from pydub import AudioSegment

# 加载音频和背景音乐
voice = AudioSegment.from_wav("voice.wav")
bgm = AudioSegment.from_mp3("bgm.mp3")

# 降低背景音乐音量
bgm = bgm - 20  # 降低20dB

# 混合
combined = voice.overlay(bgm)
combined.export("final.wav", format="wav")
```

---

## 示例：处理test.txt

```powershell
cd C:\PIP_Agent\tools
python process_test.py
```

这会：
1. 读取`C:\PIP_Agent\test.txt`
2. 拆分成多个句子
3. 为每句生成音频
4. 生成字幕文件
5. 保存到`projects/test/`目录

预计处理时间：根据文本长度，约10-30分钟

---

## 技术支持

遇到问题？
1. 查看日志输出
2. 检查`project_info.json`
3. 参考`TTS_README.md`

---

**开始制作你的有声小说吧！** 🎬📚
