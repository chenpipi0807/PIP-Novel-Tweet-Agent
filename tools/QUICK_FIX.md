# ⚡ 快速修复指南

## 问题原因

你的Python版本是 **3.12.3**，但IndexTTS要求 **3.8-3.11**。

numba和pynini等包不支持Python 3.12。

---

## 🎯 立即可用的解决方案

### 步骤1：安装缺失的依赖

```powershell
cd C:\PIP_Agent\tools

# 运行依赖安装脚本
powershell -ExecutionPolicy Bypass -File install_deps.ps1
```

或者手动安装：

```powershell
pip install omegaconf gradio inflect unidecode encodec vocos vector-quantize-pytorch rotary-embedding-torch
```

### 步骤2：运行测试

```powershell
python test_simple.py
```

如果测试通过，你就可以使用TTS工具了！

### 步骤3：使用工具

```powershell
# 查看音色列表
python tts_tool.py --list-timbres

# 合成语音
python tts_tool.py --text "你好世界" --timbre "温柔学姐" --output test.wav
```

---

## 🔧 如果还是失败

### 选项A：降级Python（推荐）

1. **下载Python 3.11.9**
   - 访问：https://www.python.org/downloads/release/python-3119/
   - 下载：Windows installer (64-bit)

2. **安装到独立目录**
   ```
   安装路径：C:\Python311
   ✓ 勾选 "Add Python to PATH"
   ```

3. **创建虚拟环境**
   ```powershell
   C:\Python311\python.exe -m venv C:\PIP_Agent\venv_tts
   C:\PIP_Agent\venv_tts\Scripts\activate
   ```

4. **重新安装**
   ```powershell
   # 在虚拟环境中
   pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
   cd C:\PIP_Agent\index-tts
   pip install -e .
   ```

### 选项B：使用Conda

```powershell
# 安装Miniconda：https://docs.conda.io/en/latest/miniconda.html

# 创建环境
conda create -n indextts python=3.11 -y
conda activate indextts

# 安装pynini（conda不需要编译）
conda install -c conda-forge pynini=2.1.6 -y

# 安装PyTorch
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装IndexTTS
cd C:\PIP_Agent\index-tts
pip install -e .

# 测试
cd C:\PIP_Agent\tools
python test_simple.py
```

---

## 📊 当前状态检查

运行这个命令查看你的环境：

```powershell
python -c "import sys; print(f'Python版本: {sys.version}'); import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

你应该看到：
- ✓ Python版本: 3.11.x（不是3.12）
- ✓ PyTorch: 2.x
- ✓ CUDA: True

---

## 🎬 最简单的方法（如果上面都不行）

我可以为你创建一个**完全独立的版本**，不需要安装IndexTTS包，直接使用模型文件。

告诉我是否需要这个方案。

---

## 需要帮助？

如果遇到问题，请告诉我：
1. 你选择了哪个方案
2. 具体的错误信息
3. `python --version` 的输出

我会继续帮你解决！
