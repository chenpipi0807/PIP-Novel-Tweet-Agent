"""
下载SDXL Lightning LoRA
4步采样，速度提升7倍
"""
from huggingface_hub import hf_hub_download
from pathlib import Path

print("正在下载SDXL Lightning LoRA...")
print("模型: ByteDance/SDXL-Lightning")
print("文件: sdxl_lightning_4step_lora.safetensors")

lora_dir = Path("sdxl/models/loras")
lora_dir.mkdir(parents=True, exist_ok=True)

try:
    lora_path = hf_hub_download(
        repo_id="ByteDance/SDXL-Lightning",
        filename="sdxl_lightning_4step_lora.safetensors",
        local_dir=str(lora_dir)
    )
    
    print(f"\n✓ 下载完成！")
    print(f"  保存位置: {lora_path}")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
