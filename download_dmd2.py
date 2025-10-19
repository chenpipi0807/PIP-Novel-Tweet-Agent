"""
下载DMD2 LoRA
4步采样，专为SDXL优化
"""
from huggingface_hub import hf_hub_download
from pathlib import Path

print("正在下载DMD2 LoRA...")
print("模型: tianweiy/DMD2")
print("文件: dmd2_sdxl_4step_lora.safetensors")

lora_dir = Path("sdxl/models/loras")
lora_dir.mkdir(parents=True, exist_ok=True)

try:
    lora_path = hf_hub_download(
        repo_id="tianweiy/DMD2",
        filename="dmd2_sdxl_4step_lora.safetensors",
        local_dir=str(lora_dir)
    )
    
    print(f"\n✓ 下载完成！")
    print(f"  保存位置: {lora_path}")
    print("\n特点:")
    print("  - 4步采样")
    print("  - 专为SDXL优化")
    print("  - 高质量输出")
    
except Exception as e:
    print(f"\n❌ 下载失败: {e}")
