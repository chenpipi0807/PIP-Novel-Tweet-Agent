"""
AnimagineXL图像生成
支持中文提示词（自动翻译）
"""
import torch
from diffusers import StableDiffusionXLPipeline
import time
from pathlib import Path
import re

print("=" * 70)
print("AnimagineXL 图像生成")
print("=" * 70)

# 检查GPU
print("\n[1/4] 检查环境...")
print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
print(f"✓ 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# 加载模型
print("\n[2/4] 加载模型...")
model_path = str(Path(__file__).parent / "models" / "animagine-xl-4.0")

pipe = StableDiffusionXLPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    use_safetensors=True
).to("cuda")

print("✓ 模型加载成功")

# 启用优化
print("\n[3/4] 启用优化...")
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()
print("✓ 优化已启用")

# 中文检测
def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

# 简单翻译（后续可接入API）
def translate_prompt(prompt):
    """
    简单的中文到英文映射
    后续可以接入Kimi API
    """
    if not has_chinese(prompt):
        return prompt
    
    # 简单映射表
    mappings = {
        "老道士": "old taoist priest",
        "蓝色长袍": "blue robe",
        "神秘": "mysterious",
        "微笑": "smile",
        "中国风": "chinese style",
        "现代都市": "modern city",
        "街道": "street",
        "黄昏": "sunset",
        "温暖": "warm",
        "光线": "lighting",
        "电影感": "cinematic",
        "高质量": "high quality",
        "细节": "detailed",
    }
    
    result = prompt
    for cn, en in mappings.items():
        result = result.replace(cn, en)
    
    print(f"  [翻译] {prompt} -> {result}")
    return result

# 生成图像
print("\n[4/4] 生成图像...")
print("-" * 70)

# 测试提示词（中文）
prompt_cn = "一个穿蓝色长袍的老道士，神秘的微笑，中国风，高质量"

print(f"\n原始提示词: {prompt_cn}")

# 翻译
prompt_en = translate_prompt(prompt_cn)
print(f"英文提示词: {prompt_en}")

print("\n分辨率: 1024x1024")
print("推理步数: 28")
print("\n正在生成...")

torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()

start_time = time.time()

image = pipe(
    prompt=prompt_en,
    negative_prompt="low quality, blurry, distorted",
    num_inference_steps=28,
    guidance_scale=7.0,
    height=1024,
    width=1024
).images[0]

elapsed = time.time() - start_time
memory = torch.cuda.max_memory_allocated() / 1024**3

# 保存
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
output_path = output_dir / "test_老道士.png"
image.save(output_path)

print(f"\n✓ 生成完成！")
print(f"  生成时间: {elapsed:.2f} 秒")
print(f"  显存占用: {memory:.2f} GB")
print(f"  保存位置: {output_path.absolute()}")

# 再生成一张
print("\n" + "-" * 70)
print("生成第二张...")

prompt_cn2 = "现代都市街道，黄昏，温暖光线，电影感"
prompt_en2 = translate_prompt(prompt_cn2)

torch.cuda.empty_cache()
start_time = time.time()

image2 = pipe(
    prompt=prompt_en2,
    negative_prompt="low quality, blurry",
    num_inference_steps=28,
    guidance_scale=7.0,
    height=1024,
    width=1024
).images[0]

elapsed2 = time.time() - start_time
output_path2 = output_dir / "test_都市.png"
image2.save(output_path2)

print(f"\n✓ 生成完成！")
print(f"  生成时间: {elapsed2:.2f} 秒")
print(f"  保存位置: {output_path2.absolute()}")

# 总结
print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)
print(f"\n平均速度: {(elapsed + elapsed2) / 2:.2f} 秒/张")
print(f"显存占用: {memory:.2f} GB")

if (elapsed + elapsed2) / 2 < 30:
    print("\n🚀 速度优秀！")
else:
    print("\n✓ 速度可接受")

print("\n提示:")
print("  - 支持中文提示词（简单翻译）")
print("  - 后续可接入Kimi API实现更好的翻译")
print("  - 使用英文提示词效果更好")

print("\n" + "=" * 70)
