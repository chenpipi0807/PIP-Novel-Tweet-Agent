"""
短剧AI生成系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, send_file, url_for
from pathlib import Path
import json
import threading
import queue
import time
from datetime import datetime
from main import VideoGenerator
from tools.project_manager import ProjectManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 任务队列
task_queue = queue.Queue()
current_task = None
task_history = []
task_lock = threading.Lock()


class Task:
    """任务类"""
    def __init__(self, task_id, project_name, novel_text, timbre=None):
        self.task_id = task_id
        self.project_name = project_name
        self.novel_text = novel_text
        self.timbre = timbre if timbre else "默认"
        self.status = 'pending'  # pending, running, completed, failed
        self.progress = 0
        self.current_step = ''
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.error = None
        self.video_path = None
        
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'project_name': self.project_name,
            'novel_text': self.novel_text[:100] + '...' if len(self.novel_text) > 100 else self.novel_text,
            'timbre': self.timbre,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'duration': f"{self.duration:.1f}秒" if self.duration else None,
            'error': self.error,
            'video_path': self.video_path
        }


def task_worker():
    """任务处理线程"""
    global current_task
    
    while True:
        task = task_queue.get()
        
        with task_lock:
            current_task = task
            task.status = 'running'
            task.start_time = datetime.now()
        
        try:
            # 执行任务
            generator = VideoGenerator(task.project_name, task.novel_text, task.timbre)
            
            # 步骤1: TTS
            task.current_step = '步骤1/4: 生成音频和字幕'
            task.progress = 10
            if not generator.step1_generate_audio_and_subtitles():
                raise Exception("音频生成失败")
            
            # 步骤2: 提示词
            task.current_step = '步骤2/4: 生成AI绘画提示词'
            task.progress = 30
            if not generator.step2_generate_prompts():
                raise Exception("提示词生成失败")
            
            # 步骤3: 图像
            task.current_step = '步骤3/4: 生成分镜图像'
            task.progress = 50
            if not generator.step3_generate_images():
                raise Exception("图像生成失败")
            
            # 步骤4: 视频
            task.current_step = '步骤4/4: 合成视频'
            task.progress = 80
            video_path = generator.step4_generate_video()
            if not video_path:
                raise Exception("视频合成失败")
            
            # 完成
            task.status = 'completed'
            task.progress = 100
            task.current_step = '完成'
            task.video_path = video_path
            
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            
        finally:
            task.end_time = datetime.now()
            task.duration = (task.end_time - task.start_time).total_seconds()
            
            with task_lock:
                task_history.append(task)
                current_task = None
            
            task_queue.task_done()


# 启动任务处理线程
worker_thread = threading.Thread(target=task_worker, daemon=True)
worker_thread.start()


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/timbres')
def get_timbres():
    """获取音色列表"""
    timbre_dir = Path('Timbre')
    timbres = []
    
    if timbre_dir.exists():
        for file in timbre_dir.glob('*'):
            if file.suffix.lower() in ['.wav', '.mp3']:
                timbres.append(file.name)
    
    return jsonify(timbres)


@app.route('/api/create_task', methods=['POST'])
def create_task():
    """创建新任务"""
    data = request.json
    
    project_name = data.get('project_name')
    novel_text = data.get('novel_text')
    timbre = data.get('timbre')
    
    if not project_name or not novel_text:
        return jsonify({'error': '项目名称和小说文本不能为空'}), 400
    
    # 创建任务
    task_id = f"task_{int(time.time())}"
    task = Task(task_id, project_name, novel_text, timbre)
    
    # 加入队列
    task_queue.put(task)
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '任务已加入队列'
    })


@app.route('/api/tasks')
def get_tasks():
    """获取所有任务（包括本地项目）"""
    with task_lock:
        tasks = []
        task_project_names = set()
        
        # 当前任务
        if current_task:
            tasks.append(current_task.to_dict())
            task_project_names.add(current_task.project_name)
        
        # 队列中的任务
        for task in list(task_queue.queue):
            tasks.append(task.to_dict())
            task_project_names.add(task.project_name)
        
        # 历史任务
        for task in reversed(task_history[-10:]):  # 最近10个
            tasks.append(task.to_dict())
            task_project_names.add(task.project_name)
        
        # 扫描本地项目，添加未在任务列表中的项目
        manager = ProjectManager()
        local_projects = manager.scan_projects()
        
        for project in local_projects:
            if project['project_name'] not in task_project_names:
                # 转换为任务格式
                task_dict = {
                    'task_id': f"local_{project['project_name']}",
                    'project_name': project['project_name'],
                    'novel_text': '',
                    'timbre': '',
                    'status': project['status'],
                    'progress': project['progress'],
                    'current_step': f"步骤{project['current_step']}/4",
                    'start_time': project['created_time'],
                    'end_time': project['modified_time'] if project['status'] == 'completed' else None,
                    'duration': None,
                    'error': None,
                    'video_path': None,
                    'can_continue': manager.can_continue(project['project_name']),
                    'missing_scenes': project['missing_scenes'],
                    'completed_scenes': project['completed_scenes'],
                    'total_scenes': project['total_scenes']
                }
                tasks.append(task_dict)
    
    return jsonify(tasks)


@app.route('/api/prompts/<project_name>')
def get_prompts(project_name):
    """获取项目的提示词"""
    prompts_file = Path('projects') / project_name / 'Prompts.json'
    
    if not prompts_file.exists():
        return jsonify({'error': '提示词文件不存在'}), 404
    
    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    return jsonify(prompts)


@app.route('/api/prompts/<project_name>', methods=['POST'])
def update_prompts(project_name):
    """更新项目的提示词"""
    prompts_file = Path('projects') / project_name / 'Prompts.json'
    
    data = request.json
    
    # 保存更新后的提示词
    with open(prompts_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return jsonify({'success': True, 'message': '提示词已更新'})


@app.route('/api/video/<project_name>')
def get_video(project_name):
    """获取视频文件"""
    video_dir = Path('projects') / project_name / 'Videos'
    
    # 查找视频文件
    video_files = list(video_dir.glob('*.mp4'))
    
    if not video_files:
        return jsonify({'error': '视频文件不存在'}), 404
    
    return send_file(video_files[0], mimetype='video/mp4')


@app.route('/projects')
def projects_page():
    """项目列表页面"""
    return render_template('projects.html')


@app.route('/tasks')
def tasks_page():
    """任务管理页面"""
    return render_template('tasks.html')


@app.route('/edit/<project_name>')
def edit_page(project_name):
    """提示词编辑页面"""
    return render_template('edit.html', project_name=project_name)


@app.route('/project/<project_name>')
def project_detail(project_name):
    """项目详情页面"""
    return render_template('project_detail.html', project_name=project_name)


@app.route('/api/image/<project_name>/<int:scene_index>')
def get_image(project_name, scene_index):
    """获取分镜图片"""
    img_file = Path('projects') / project_name / 'Imgs' / f'scene_{scene_index:04d}.png'
    
    if not img_file.exists():
        return jsonify({'error': '图片不存在'}), 404
    
    return send_file(img_file, mimetype='image/png')


@app.route('/api/regenerate_scene/<project_name>/<int:scene_index>', methods=['POST'])
def regenerate_scene(project_name, scene_index):
    """重新生成单个分镜"""
    try:
        from main import VideoGenerator
        import torch
        import gc
        
        generator = VideoGenerator(project_name, "")
        
        # 读取提示词
        prompts_file = Path('projects') / project_name / 'Prompts.json'
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        # 找到对应的提示词
        scene_prompt = None
        for scene in prompts_data.get('scene_prompts', []):
            if scene['index'] == scene_index:
                scene_prompt = scene['prompt']
                break
        
        if not scene_prompt:
            return jsonify({'error': '找不到对应的提示词'}), 404
        
        # 清理显存
        torch.cuda.empty_cache()
        gc.collect()
        
        # 加载SDXL模型
        from diffusers import StableDiffusionXLPipeline
        
        model_path = "sdxl/models/animagine-xl-4.0"
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            use_safetensors=True
        ).to("cuda")
        
        pipe.enable_attention_slicing()
        pipe.enable_vae_slicing()
        
        # 生成图像（使用随机种子）
        import random
        seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device="cuda").manual_seed(seed)
        
        image = pipe(
            prompt=scene_prompt,
            negative_prompt="low quality, blurry, distorted, bad anatomy",
            num_inference_steps=28,
            guidance_scale=7.0,
            width=1024,
            height=1024,
            generator=generator
        ).images[0]
        
        # 保存图像
        img_path = generator.imgs_dir / f"scene_{scene_index:04d}.png"
        image.save(img_path)
        
        # 释放显存
        del pipe
        torch.cuda.empty_cache()
        gc.collect()
        
        return jsonify({'success': True, 'message': '图像已重新生成'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regenerate_images/<project_name>', methods=['POST'])
def regenerate_images(project_name):
    """重新生成所有图像"""
    try:
        from main import VideoGenerator
        
        generator = VideoGenerator(project_name, "")
        
        # 调用生成图像方法（跳过已存在检查）
        if generator.step3_generate_images(skip_if_exists=False):
            return jsonify({'success': True, 'message': '所有图像已重新生成'})
        else:
            return jsonify({'error': '图像生成失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regenerate_video/<project_name>', methods=['POST'])
def regenerate_video(project_name):
    """重新合成视频"""
    try:
        from main import VideoGenerator
        
        generator = VideoGenerator(project_name, "")
        
        # 调用视频合成方法
        video_path = generator.step4_generate_video()
        
        if video_path:
            return jsonify({'success': True, 'message': '视频已重新合成', 'video_path': video_path})
        else:
            return jsonify({'error': '视频合成失败'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/continue_project/<project_name>', methods=['POST'])
def continue_project(project_name):
    """继续未完成的项目"""
    try:
        manager = ProjectManager()
        
        # 检查项目状态
        if not manager.can_continue(project_name):
            return jsonify({'error': '项目无法继续'}), 400
        
        # 获取下一步
        next_step = manager.get_next_step(project_name)
        
        if not next_step or next_step == 'completed':
            return jsonify({'error': '项目已完成'}), 400
        
        # 创建继续任务
        task_id = f"continue_{int(time.time())}"
        task = Task(task_id, project_name, "", "")
        task.status = 'pending'
        
        # 加入队列
        task_queue.put(task)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'next_step': next_step,
            'message': f'项目将从{next_step}继续执行'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/project_status/<project_name>')
def get_project_status(project_name):
    """获取项目详细状态"""
    try:
        manager = ProjectManager()
        status = manager.get_project_status(project_name)
        
        if not status:
            return jsonify({'error': '项目不存在'}), 404
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
