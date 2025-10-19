"""
短剧AI生成系统 - 主控制流程
从小说文本到完整视频的自动化生成
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加tools目录到路径
sys.path.append(str(Path(__file__).parent / "tools"))

from generate_prompts import PromptGenerator
from kimi_api import KimiAPI


class VideoGenerator:
    def __init__(self, project_name, novel_text, timbre=None):
        """
        初始化视频生成器
        
        Args:
            project_name: 项目名称
            novel_text: 小说文本
            timbre: 音色文件名（可选）
        """
        self.project_name = project_name
        self.novel_text = novel_text
        self.timbre = timbre
        
        # 创建项目目录结构
        self.project_dir = Path("projects") / project_name
        self.audio_dir = self.project_dir / "Audio"
        self.imgs_dir = self.project_dir / "Imgs"
        self.videos_dir = self.project_dir / "Videos"
        
        # 创建所有必要目录
        for dir_path in [self.audio_dir, self.imgs_dir, self.videos_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.subtitle_file = self.audio_dir / "Subtitles.json"
        self.prompts_file = self.project_dir / "Prompts.json"
        
        print(f"✓ 项目初始化: {project_name}")
        print(f"  项目目录: {self.project_dir}")
    
    def step1_generate_audio_and_subtitles(self, skip_if_exists=True):
        """
        步骤1: 生成音频和字幕文件
        调用TTS系统生成音频和字幕
        
        Args:
            skip_if_exists: 如果字幕文件已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 1/5: 生成音频和字幕")
        print("=" * 70)
        
        # 检查是否已完成
        if skip_if_exists and self.subtitle_file.exists():
            print(f"✓ 字幕文件已存在，跳过此步骤")
            print(f"  文件: {self.subtitle_file}")
            return True
        
        # 导入TTS模块
        try:
            from tts_generator import generate_audio_and_subtitles
            
            # 调用TTS生成
            result = generate_audio_and_subtitles(
                text=self.novel_text,
                project_name=self.project_name,
                timbre_name=self.timbre
            )
            
            if result and self.subtitle_file.exists():
                print(f"✓ 字幕文件已生成: {self.subtitle_file}")
                
                # 读取字幕统计信息
                with open(self.subtitle_file, 'r', encoding='utf-8') as f:
                    subtitles = json.load(f)
                    print(f"  总句数: {subtitles.get('total_sentences', 0)}")
                    print(f"  总时长: {subtitles.get('total_duration', 0):.2f}秒")
                
                return True
            else:
                print("❌ 字幕文件生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 步骤1失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step2_generate_prompts(self, skip_if_exists=True):
        """
        步骤2: 生成AI绘画提示词
        调用Kimi API处理字幕文件
        
        Args:
            skip_if_exists: 如果提示词文件已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 2/5: 生成AI绘画提示词")
        print("=" * 70)
        
        # 检查是否已完成
        if skip_if_exists and self.prompts_file.exists():
            print(f"✓ 提示词文件已存在，跳过此步骤")
            print(f"  文件: {self.prompts_file}")
            return True
        
        if not self.subtitle_file.exists():
            print(f"❌ 字幕文件不存在: {self.subtitle_file}")
            return False
        
        try:
            # 使用PromptGenerator
            generator = PromptGenerator(self.project_name)
            prompts = generator.generate_prompts(str(self.subtitle_file))
            
            # 保存到项目目录
            generator.save_prompts(prompts, str(self.prompts_file))
            
            # 打印摘要
            generator.print_summary(prompts)
            
            return True
            
        except Exception as e:
            print(f"❌ 步骤2失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step3_generate_images(self, skip_if_exists=True):
        """
        步骤3: 生成分镜图像
        调用SDXL生成所有分镜图片
        
        Args:
            skip_if_exists: 如果图片已存在则跳过
        """
        print("\n" + "=" * 70)
        print("步骤 3/5: 生成分镜图像")
        print("=" * 70)
        
        if not self.prompts_file.exists():
            print(f"❌ 提示词文件不存在: {self.prompts_file}")
            return False
        
        try:
            # 清理显存（确保TTS模型已卸载）
            import torch
            import gc
            
            print("清理显存...")
            torch.cuda.empty_cache()
            gc.collect()
            
            # 读取提示词
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            scene_prompts = prompts_data.get('scene_prompts', [])
            total = len(scene_prompts)
            
            # 检查已生成的图像
            existing_images = list(self.imgs_dir.glob("scene_*.png"))
            if skip_if_exists and len(existing_images) == total:
                print(f"✓ 所有图像已存在（{total}张），跳过此步骤")
                return True
            
            print(f"需要生成 {total} 张图像")
            if existing_images:
                print(f"  已存在 {len(existing_images)} 张，将跳过")
            
            print("加载SDXL模型...")
            
            # 导入SDXL生成模块
            from diffusers import StableDiffusionXLPipeline, EulerAncestralDiscreteScheduler
            from pathlib import Path
            
            # 加载模型
            model_path = "sdxl/models/animagine-xl-4.0"
            pipe = StableDiffusionXLPipeline.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                use_safetensors=True
            ).to("cuda")
            
            # 加载DMD2 LoRA（使用测试最佳配置）
            dmd2_lora_path = Path("sdxl/models/loras/dmd2_sdxl_4step_lora.safetensors")
            use_dmd2 = False
            if dmd2_lora_path.exists():
                # LoRA强度 0.8
                pipe.load_lora_weights(
                    str(dmd2_lora_path.parent), 
                    weight_name=dmd2_lora_path.name,
                    adapter_name="dmd2"
                )
                pipe.set_adapters(["dmd2"], adapter_weights=[0.8])
                
                # 使用Euler Ancestral调度器（测试最佳配置）
                pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                    pipe.scheduler.config
                )
                
                use_dmd2 = True
                print("✓ DMD2 LoRA加载完成（强度0.8，Euler Ancestral调度器）")
            else:
                print("⚠ DMD2 LoRA未找到，使用28步采样")
            
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
            
            print("✓ 模型加载完成")
            
            # 生成图像
            for i, scene in enumerate(scene_prompts, 1):
                index = scene['index']
                prompt = scene['prompt']
                
                # 检查是否已存在
                img_filename = f"scene_{index:04d}.png"
                img_path = self.imgs_dir / img_filename
                
                if skip_if_exists and img_path.exists():
                    print(f"\n[{i}/{total}] 分镜 {index} 已存在，跳过")
                    continue
                
                print(f"\n[{i}/{total}] 生成分镜 {index}...")
                print(f"提示词: {prompt[:80]}...")
                
                # 生成图像（使用随机种子）
                torch.cuda.empty_cache()
                import random
                seed = random.randint(0, 2**32 - 1)
                generator_obj = torch.Generator(device="cuda").manual_seed(seed)
                
                # 使用DMD2 LoRA（测试最佳配置）
                if use_dmd2:
                    # DMD2: 12步，CFG=2.5（测试最佳配置：EulerA_Normal_steps12_cfg2.5）
                    image = pipe(
                        prompt=prompt,
                        negative_prompt="low quality, blurry, distorted, bad anatomy, ugly, duplicate, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face",
                        num_inference_steps=12,
                        guidance_scale=2.5,
                        width=1024,
                        height=1024,
                        generator=generator_obj
                    ).images[0]
                else:
                    # 标准模式: 28步
                    image = pipe(
                        prompt=prompt,
                        negative_prompt="low quality, blurry, distorted, bad anatomy",
                        num_inference_steps=28,
                        guidance_scale=7.0,
                        width=1024,
                        height=1024,
                        generator=generator_obj
                    ).images[0]
                
                # 保存图像
                img_filename = f"scene_{index:04d}.png"
                img_path = self.imgs_dir / img_filename
                image.save(img_path)
                
                print(f"✓ 已保存: {img_filename}")
            
            print(f"\n✓ 所有图像生成完成！共 {total} 张")
            
            # 卸载模型，释放显存
            print("释放显存...")
            del pipe
            torch.cuda.empty_cache()
            gc.collect()
            
            return True
            
        except Exception as e:
            print(f"❌ 步骤3失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def step4_generate_video(self):
        """
        步骤4: 合成视频
        将图片和音频合成为视频，添加随机转场
        """
        print("\n" + "=" * 70)
        print("步骤 4/5: 合成视频")
        print("=" * 70)
        
        # 检查ffmpeg
        from check_ffmpeg import check_ffmpeg
        if not check_ffmpeg():
            print("\n请先安装ffmpeg后再继续")
            return False
        
        try:
            # 导入视频合成模块（增强版：支持运镜和字幕）
            from video_composer_enhanced import compose_video
            
            video_path = compose_video(
                project_dir=str(self.project_dir),
                subtitle_file=str(self.subtitle_file),
                imgs_dir=str(self.imgs_dir),
                audio_dir=str(self.audio_dir),
                output_dir=str(self.videos_dir)
            )
            
            if video_path:
                print(f"✓ 视频生成完成: {video_path}")
                return True
            else:
                print("❌ 视频生成失败")
                return False
                
        except Exception as e:
            print(f"❌ 步骤4失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """执行完整流程"""
        print("\n" + "=" * 70)
        print(f"短剧AI生成系统 - {self.project_name}")
        print("=" * 70)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        start_time = datetime.now()
        
        # 执行各步骤
        steps = [
            ("生成音频和字幕", self.step1_generate_audio_and_subtitles),
            ("生成AI绘画提示词", self.step2_generate_prompts),
            ("生成分镜图像", self.step3_generate_images),
            ("合成视频", self.step4_generate_video),
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ 流程中断于: {step_name}")
                return False
        
        # 完成
        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 70)
        print("✓ 全部流程完成！")
        print("=" * 70)
        print(f"总耗时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
        print(f"项目目录: {self.project_dir.absolute()}")
        print(f"视频输出: {self.videos_dir.absolute()}")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='短剧AI生成系统')
    parser.add_argument('project_name', help='项目名称')
    parser.add_argument('--text', help='小说文本（直接输入）')
    parser.add_argument('--file', help='小说文本文件路径')
    
    args = parser.parse_args()
    
    # 获取小说文本
    if args.text:
        novel_text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            novel_text = f.read()
    else:
        print("错误: 必须提供 --text 或 --file 参数")
        return
    
    # 创建生成器并运行
    generator = VideoGenerator(args.project_name, novel_text)
    generator.run()


if __name__ == "__main__":
    main()
