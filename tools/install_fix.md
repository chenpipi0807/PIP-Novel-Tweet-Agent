# 🔧 安装问题修复指南

## 问题诊断

你遇到的主要问题：

1. ❌ **Python版本不兼容** - 当前：3.12.3，要求：3.8-3.11
2. ❌ **pynini编译失败** - Windows编译器问题
3. ❌ **缺少依赖** - omegaconf等模块

## 解决方案

### 方案1：使用Python 3.11（推荐）

#### 步骤1：安装Python 3.11

1. 下载Python 3.11：https://www.python.org/downloads/release/python-3119/
2. 选择 "Windows installer (64-bit)"
3. 安装时勾选 "Add Python to PATH"
4. 安装到独立目录，例如：`C:\Python311`

#### 步骤2：创建虚拟环境

```powershell
# 使用Python 3.11创建虚拟环境
C:\Python311\python.exe -m venv C:\PIP_Agent\venv_tts

# 激活虚拟环境
C:\PIP_Agent\venv_tts\Scripts\activate

# 验证Python版本
python --version  # 应该显示 Python 3.11.x
```

#### 步骤3：安装依赖

```powershell
# 安装PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装IndexTTS（在虚拟环境中）
cd C:\PIP_Agent\index-tts
pip install -e .

# 如果遇到pynini问题，跳过它
pip install -e . --no-deps
pip install -r requirements.txt --no-deps
# 然后手动安装除pynini外的依赖
```

---

### 方案2：绕过完整安装（快速方案）⭐

不安装完整的IndexTTS包，直接安装核心依赖：

```powershell
cd C:\PIP_Agent\tools

# 安装核心依赖（跳过pynini）
pip install omegaconf
pip install gradio
pip install inflect
pip install unidecode
pip install encodec
pip install vocos
pip install vector-quantize-pytorch
pip install einops
pip install rotary-embedding-torch
pip install transformers
pip install librosa
pip install soundfile
pip install tqdm
pip install pyyaml
```

---

### 方案3：使用conda（最稳定）

```powershell
# 安装Miniconda
# 下载：https://docs.conda.io/en/latest/miniconda.html

# 创建Python 3.11环境
conda create -n indextts python=3.11
conda activate indextts

# 安装pynini（conda版本不需要编译）
conda install -c conda-forge pynini=2.1.6

# 安装PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装IndexTTS
cd C:\PIP_Agent\index-tts
pip install -e .
```

---

## 快速测试（方案2后）

创建测试文件 `C:\PIP_Agent\tools\test_simple.py`:

```python
import sys
sys.path.insert(0, r'C:\PIP_Agent\index-tts')

try:
    from indextts.infer import IndexTTS
    print("✓ IndexTTS导入成功！")
    
    # 初始化
    tts = IndexTTS(
        model_dir=r"C:\PIP_Agent\models",
        cfg_path=r"C:\PIP_Agent\models\config.yaml"
    )
    print("✓ 模型加载成功！")
    
    # 测试合成
    tts.infer(
        voice=r"C:\PIP_Agent\Timbre\温柔学姐.mp3",
        text="你好，这是一个测试。",
        output_path="test_output.wav"
    )
    print("✓ 语音合成成功！")
    
except Exception as e:
    print(f"✗ 错误: {e}")
    import traceback
    traceback.print_exc()
```

运行测试：
```powershell
cd C:\PIP_Agent\tools
python test_simple.py
```

---

## 我的推荐

**立即可用的方案**：使用方案2，然后运行我创建的简化工具。

执行以下命令：

```powershell
cd C:\PIP_Agent\tools

# 安装缺失的依赖
pip install omegaconf gradio inflect unidecode encodec vocos vector-quantize-pytorch rotary-embedding-torch

# 测试
python test_simple.py
```

如果还有问题，我会创建一个完全独立的工具，不依赖IndexTTS的安装。
