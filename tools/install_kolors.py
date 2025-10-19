"""
Kolors依赖安装脚本
"""
import subprocess
import sys

print("=" * 60)
print("Kolors 依赖安装")
print("=" * 60)

packages = [
    "diffusers>=0.30.0",
    "transformers>=4.40.0",
    "accelerate>=0.26.0",
    "sentencepiece>=0.1.99",
    "protobuf>=3.20.0",
    "xformers",  # 可选但强烈推荐
]

print("\n安装以下包:")
for pkg in packages:
    print(f"  - {pkg}")

print("\n开始安装...")

for pkg in packages:
    print(f"\n安装 {pkg}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
        print(f"✓ {pkg} 安装成功")
    except:
        print(f"⚠ {pkg} 安装失败（可能已安装或不兼容）")

print("\n" + "=" * 60)
print("安装完成！")
print("=" * 60)
print("\n下一步:")
print("  python test_kolors.py")
