"""
下载Hyper-SDXL LoRA
4步采样，支持CFG，兼容AnimagineXL
"""
from huggingface_hub import hf_hub_download
from pathlib import Path

print("正在下载Hyper-SDXL LoRA...")
print("模型: ByteDance/Hyper-SD")
print("文件: Hyper-SDXL-4steps-lora.safetensors")

lora_dir = Path("sdxl/models/loras")
lora_dir.mkdir(parents=True, exist_ok=True)

try:
    lora_path = hf_hub_download(
        repo_id="ByteDance/Hyper-SD",
        filename="Hyper-SDXL-4steps-lora.safetensors",
        local_dir=str(lora_dir)
    )
    
    print(f"\n✓ 下载完成！")
    print(f"  保存位置: {lora_path}")
    print("\n特点:")
    print("  - 4步采样")
    print("  - 支持CFG (guidance_scale)")
    print("  - 兼容AnimagineXL")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
