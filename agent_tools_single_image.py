"""
Agent工具：单张图片重新生成
"""
from pathlib import Path
import json


def regenerate_single_image_tool(project_name: str, scene_index: int, new_prompt: str = None):
    """
    重新生成单张分镜图片
    
    Args:
        project_name: 项目名称
        scene_index: 场景索引（从1开始）
        new_prompt: 新的提示词（可选，如果不提供则使用现有提示词）
    
    Returns:
        dict: 执行结果
    """
    try:
        from main import VideoGenerator
        import torch
        import gc
        
        print(f"\n🎨 单图重生工具: scene_{scene_index:04d}")
        
        # 初始化生成器
        generator = VideoGenerator(project_name, "")
        
        # 读取提示词
        prompts_file = generator.project_dir / 'Prompts.json'
        if not prompts_file.exists():
            return {
                "success": False,
                "error": "提示词文件不存在"
            }
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        # 如果提供了新提示词，更新它
        if new_prompt:
            updated = False
            for scene in prompts_data.get('scene_prompts', []):
                if scene['index'] == scene_index:
                    scene['prompt'] = new_prompt
                    updated = True
                    break
            
            if updated:
                with open(prompts_file, 'w', encoding='utf-8') as f:
                    json.dump(prompts_data, f, ensure_ascii=False, indent=2)
                print(f"✓ 提示词已更新")
        
        # 找到对应的提示词
        scene_prompt = None
        for scene in prompts_data.get('scene_prompts', []):
            if scene['index'] == scene_index:
                scene_prompt = scene['prompt']
                break
        
        if not scene_prompt:
            return {
                "success": False,
                "error": f"找不到场景 {scene_index} 的提示词"
            }
        
        print(f"提示词: {scene_prompt[:80]}...")
        
        # 加载SDXL模型（使用与main.py完全相同的配置）
        from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
        
        # 使用正确的模型路径
        model_dir = Path("sdxl/models/prefectIllustriousXL_40")
        model_path_file = model_dir / "prefectIllustriousXL_40.safetensors"
        
        if not model_path_file.exists():
            return {
                "success": False,
                "error": f"模型文件不存在: {model_path_file}"
            }
        
        print("加载SDXL模型...")
        print(f"✓ 使用模型: Prefect Illustrious XL 40")
        
        pipe = StableDiffusionXLPipeline.from_single_file(
            str(model_path_file),
            torch_dtype=torch.float16,
            config=str(model_dir),
            local_files_only=True
        ).to("cuda")
        
        # 加载DMD2 LoRA
        dmd2_lora_path = Path("sdxl/models/loras/dmd2_sdxl_4step_lora.safetensors")
        if dmd2_lora_path.exists():
            pipe.load_lora_weights(
                str(dmd2_lora_path.parent),
                weight_name=dmd2_lora_path.name,
                adapter_name="dmd2"
            )
            pipe.set_adapters(["dmd2"], adapter_weights=[0.8])
            print("✓ DMD2 LoRA已加载")
        
        # 使用Euler Ancestral调度器
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
            pipe.scheduler.config
        )
        
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()
        
        # 生成图像（使用与main.py完全相同的参数）
        print("生成图像...")
        torch.cuda.empty_cache()
        import random
        seed = random.randint(0, 2**32 - 1)
        generator_obj = torch.Generator(device="cuda").manual_seed(seed)
        
        # 负面词（Illustrious专用 - 更全面的质量控制）
        negative_prompt = "lazyneg, lazyhand, child, (censored, mosaic censoring, bar_censor), lowres, text, error, cropped, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, out of frame, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck, username, watermark, signature"
        
        # 添加质量标签到提示词（Illustrious专用PE格式）
        quality_tags = "score_9, score_8_up, score_7_up, masterpiece, best quality, amazing quality, absurdres, newest"
        enhanced_prompt = f"{quality_tags}, BREAK {scene_prompt}"
        
        # 使用DMD2加速模式
        use_dmd2 = dmd2_lora_path.exists()
        if use_dmd2:
            # DMD2: 12步，CFG=2.5（原始稳定配置）
            image = pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=12,
                guidance_scale=2.5,
                width=1024,
                height=1024,
                generator=generator_obj,
                clip_skip=2
            ).images[0]
        else:
            # 标准模式: 20步，CFG=7.0（原始配置）
            image = pipe(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=20,
                guidance_scale=7.0,
                width=1024,
                height=1024,
                generator=generator_obj,
                clip_skip=2
            ).images[0]
        
        # 保存图像
        img_path = generator.imgs_dir / f"scene_{scene_index:04d}.png"
        image.save(img_path)
        print(f"✓ 图像已保存: {img_path}")
        
        # 释放显存
        del pipe
        torch.cuda.empty_cache()
        gc.collect()
        
        return {
            "success": True,
            "message": f"场景 {scene_index} 已重新生成",
            "image_path": str(img_path),
            "prompt": scene_prompt
        }
        
    except Exception as e:
        print(f"❌ 单图重生失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
