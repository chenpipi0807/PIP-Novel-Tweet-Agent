# 🚀 快速开始指南

## 一、安装依赖（首次使用）

```powershell
# 1. 安装PyTorch (GPU版本)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 2. 安装IndexTTS
cd C:\PIP_Agent\index-tts
pip install -e .

# 3. 安装TTS工具依赖
cd ..\tools
pip install -r requirements_tts.txt
```

## 二、验证环境

```powershell
# 检查GPU是否可用
python -c "import torch; print('GPU可用:', torch.cuda.is_available()); print('GPU型号:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

## 三、快速测试

### 方法1：命令行测试

```powershell
cd C:\PIP_Agent\tools

# 查看所有可用音色
python tts_tool.py --list-timbres

# 合成一句话
python tts_tool.py --text "大家好，我是短剧配音演员，很高兴为大家服务！" --timbre "温柔学姐" --output test.wav
```

### 方法2：运行示例程序

```powershell
cd C:\PIP_Agent\tools
python tts_example.py
```

选择示例1或2进行测试。

### 方法3：Python代码测试

创建 `test.py`:

```python
from tts_tool import ShortDramaTTS

# 初始化
tts = ShortDramaTTS()

# 查看可用音色
print("可用音色:", tts.list_timbres()[:5])

# 合成语音
success = tts.synthesize(
    text="你好，这是一个测试。",
    timbre="温柔学姐",
    output_path="test_output.wav"
)

print("合成成功!" if success else "合成失败")
```

运行：
```powershell
python test.py
```

## 四、短剧制作流程

### 步骤1：准备脚本

创建 `my_script.json`:

```json
[
    {
        "text": "第一集：相遇",
        "timbre": "播音中年男",
        "filename": "01_title.wav"
    },
    {
        "text": "你好，很高兴认识你。",
        "timbre": "温润青年",
        "filename": "02_male.wav"
    },
    {
        "text": "我也是，你好。",
        "timbre": "温柔学姐",
        "filename": "03_female.wav"
    }
]
```

### 步骤2：批量合成

```powershell
python tts_tool.py --batch my_script.json
```

输出文件会保存在 `outputs/` 文件夹。

## 五、常用音色推荐

### 男声
- **温润青年** - 适合男主角
- **温润男声** - 成熟男性
- **播音中年男** - 旁白、解说
- **沉稳高管** - 反派、领导

### 女声
- **温柔学姐** - 女主角
- **温暖少女** - 活泼女孩
- **甜美女声** - 可爱角色
- **傲娇御姐** - 御姐型角色

### 特殊
- **播音中年男** - 旁白最佳选择
- **新闻女声** - 正式场合

## 六、目录结构

```
C:\PIP_Agent\
├── models/                    # ✅ 你的模型文件
├── Timbre/                    # ✅ 你的音色库（57个音色）
├── index-tts/                 # IndexTTS源码
└── tools/                     # 🎯 TTS工具（这里）
    ├── tts_tool.py           # 主工具
    ├── tts_example.py        # 示例代码
    ├── TTS_README.md         # 详细文档
    ├── QUICKSTART.md         # 本文档
    ├── requirements_tts.txt  # 依赖列表
    └── scripts_template.json # 脚本模板
```

## 七、故障排除

### 问题1：找不到模块
```powershell
# 确保在正确的目录
cd C:\PIP_Agent\tools
```

### 问题2：GPU不可用
```powershell
# 使用CPU模式（较慢）
python tts_tool.py --no-gpu --text "测试" --timbre "温柔学姐" --output test.wav
```

### 问题3：音色找不到
```powershell
# 先查看可用音色列表
python tts_tool.py --list-timbres
```

## 八、下一步

- 📖 阅读详细文档：`TTS_README.md`
- 💡 查看示例代码：`tts_example.py`
- 🎬 开始制作你的短剧！

## 需要帮助？

- QQ群：663272642, 1013410623
- Discord：https://discord.gg/uT32E7KDmy
- Email：indexspeech@bilibili.com
