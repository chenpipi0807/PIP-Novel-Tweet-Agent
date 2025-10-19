"""
下载AnimagineXL v4.0模型
"""
import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("AnimagineXL v4.0 下载器")
print("=" * 70)

# 创建模型目录
model_dir = Path(__file__).parent / "models"
model_dir.mkdir(exist_ok=True)

print("\n选择下载方式:")
print("1. HuggingFace (推荐)")
print("2. 手动下载")

choice = input("\n请选择 (1/2，默认1): ").strip() or "1"

if choice == "1":
    print("\n安装huggingface-hub...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-U", "huggingface-hub"], check=True)
    
    print("\n开始下载AnimagineXL v4.0...")
    print("模型大小: 约7GB")
    print("这可能需要10-20分钟...")
    
    # 使用国内镜像
    import os
    os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    subprocess.run([
        "huggingface-cli", "download",
        "Cagliostrolab/animagine-xl-4.0",
        "--local-dir", str(model_dir / "animagine-xl-4.0")
    ], check=True)
    
    print("\n✓ 下载完成！")
    
    # 保存配置
    config_path = model_dir / "config.txt"
    with open(config_path, 'w') as f:
        f.write("model_name=animagine-xl-4.0\n")
        f.write("model_path=models/animagine-xl-4.0\n")
        f.write("supports_chinese=no\n")
    
    print(f"✓ 配置已保存: {config_path}")

else:
    print("\n手动下载:")
    print("1. 访问: https://huggingface.co/Cagliostrolab/animagine-xl-4.0")
    print("2. 下载所有文件到: C:\\PIP_Agent\\sdxl\\models\\animagine-xl-4.0")
    print("3. 重新运行此脚本")

print("\n" + "=" * 70)
print("下一步: python test_generate.py")
print("=" * 70)
