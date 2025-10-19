"""
AnimagineXL图像生成（支持Kimi翻译）
"""
import torch
from diffusers import StableDiffusionXLPipeline
import time
from pathlib import Path
import re
import os

print("=" * 70)
print("AnimagineXL 图像生成（支持中文翻译）")
print("=" * 70)

# 导入翻译模块
from translate_kimi import translate_with_kimi, simple_translate

# 检查GPU
print("\n[1/5] 检查环境...")
print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
print(f"✓ 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# 检查Kimi API
kimi_key = os.environ.get('KIMI_API_KEY')
if kimi_key:
    print("✓ Kimi API已配置")
else:
    print("⚠ Kimi API未配置，使用简单翻译")
    print("  设置方法: set KIMI_API_KEY=your_key")

# 加载模型
print("\n[2/5] 加载模型...")
model_path = str(Path(__file__).parent / "models" / "animagine-xl-4.0")

pipe = StableDiffusionXLPipeline.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    use_safetensors=True
).to("cuda")

print("✓ 模型加载成功")

# 启用优化
print("\n[3/5] 启用优化...")
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()
print("✓ 优化已启用")

# 中文检测
def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

# 翻译函数
def translate_prompt(prompt):
    if not has_chinese(prompt):
        return prompt
    
    if kimi_key:
        return translate_with_kimi(prompt, kimi_key)
    else:
        translated = simple_translate(prompt)
        print(f"  [简单翻译] {prompt} -> {translated}")
        return translated

# 生成函数
def generate_image(prompt_cn, output_name, steps=28):
    print(f"\n原始提示词: {prompt_cn}")
    
    # 翻译
    prompt_en = translate_prompt(prompt_cn)
    print(f"英文提示词: {prompt_en}")
    
    print(f"\n分辨率: 1024x1024")
    print(f"推理步数: {steps}")
    print("正在生成...")
    
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    start_time = time.time()
    
    image = pipe(
        prompt=prompt_en,
        negative_prompt="low quality, blurry, distorted, bad anatomy",
        num_inference_steps=steps,
        guidance_scale=7.0,
        height=1024,
        width=1024
    ).images[0]
    
    elapsed = time.time() - start_time
    memory = torch.cuda.max_memory_allocated() / 1024**3
    
    # 保存
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / output_name
    image.save(output_path)
    
    print(f"\n✓ 生成完成！")
    print(f"  生成时间: {elapsed:.2f} 秒")
    print(f"  显存占用: {memory:.2f} GB")
    print(f"  保存位置: {output_path.absolute()}")
    
    return elapsed, memory

# 测试生成
print("\n[4/5] 生成测试图像...")
print("-" * 70)

test_prompts = [
    ("一个穿蓝色长袍的老道士，神秘的微笑，中国风，高质量，细节丰富", "test_老道士.png"),
    ("现代都市街道，黄昏时分，温暖的光线，电影感，高质量", "test_都市.png"),
]

times = []
for i, (prompt, filename) in enumerate(test_prompts, 1):
    print(f"\n测试 {i}/{len(test_prompts)}")
    print("-" * 70)
    elapsed, memory = generate_image(prompt, filename)
    times.append(elapsed)

# 总结
print("\n[5/5] 测试完成！")
print("=" * 70)
print(f"\n平均速度: {sum(times) / len(times):.2f} 秒/张")
print(f"显存占用: {memory:.2f} GB")

avg_time = sum(times) / len(times)
if avg_time < 15:
    print("\n🚀 速度优秀！完全满足批量生成需求")
elif avg_time < 30:
    print("\n✓ 速度良好，可以接受")
else:
    print("\n⚠ 速度一般")

print("\n使用说明:")
print("  1. 直接输入中文提示词")
print("  2. 自动翻译成英文")
print("  3. 配置Kimi API获得更好的翻译效果")
print("     set KIMI_API_KEY=your_key")

print("\n" + "=" * 70)
