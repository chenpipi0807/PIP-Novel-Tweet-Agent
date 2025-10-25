"""
短剧AI生成系统 - Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, send_file, url_for, redirect, Response
from reactpy.backend.flask import configure, Options
from react_ui import App
from pathlib import Path
import json
import threading
import queue
import time
from datetime import datetime
from main import VideoGenerator
from tools.project_manager import ProjectManager

app = Flask(__name__)

# ReactPy配置 - 自定义标题和图标
from reactpy import html
head_elements = [
    html.title({}, "PIP 小说推文"),
    html.meta({"charset": "utf-8"}),
    html.meta({"name": "viewport", "content": "width=device-width, initial-scale=1"}),
    # 使用电影图标作为favicon
    html.link({"rel": "icon", "href": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🎬</text></svg>"})
]

configure(app, App, Options(url_prefix="/react", serve_index_route=True, head=head_elements))

# 禁用Flask访问日志
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# 任务队列
task_queue = queue.Queue()
current_task = None
task_history = []
task_lock = threading.Lock()
sse_clients = []  # list of Queue objects for SSE
paused_tasks = set()  # task_id set for paused tasks


def broadcast_event(event: dict):
    try:
        data = json.dumps(event, ensure_ascii=False)
    except Exception:
        data = json.dumps({"type": "event", "payload": str(event)})
    for q in list(sse_clients):
        try:
            q.put(data, block=False)
        except Exception:
            try:
                sse_clients.remove(q)
            except Exception:
                pass


@app.route('/events')
def sse_events():
    def gen():
        q = queue.Queue()
        sse_clients.append(q)
        # initial heartbeat
        yield 'event: ping\ndata: {"ok":true}\n\n'
        try:
            while True:
                data = q.get()
                yield f'data: {data}\n\n'
        except GeneratorExit:
            pass
        finally:
            try:
                sse_clients.remove(q)
            except Exception:
                pass
    headers = {
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Content-Type': 'text/event-stream'
    }
    return Response(gen(), headers=headers)


class Task:
    """任务类"""
    def __init__(self, task_id, project_name, novel_text, timbre=None, mode='workflow', quality_target=0.8):
        self.task_id = task_id
        self.project_name = project_name
        self.novel_text = novel_text
        self.timbre = timbre if timbre else "随机"
        self.mode = mode  # workflow 或 agent
        self.quality_target = quality_target  # Agent模式的目标质量
        self.status = 'pending'  # pending, running, completed, failed
        self.progress = 0
        self.current_step = ''
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.error = None
        self.video_path = None
        self.thinking_log = []  # Agent思考日志
        self.quality_score = None  # 质量分数
        # 工具状态：idle|running|done|error，含次数与最后更新时间
        now = datetime.now().isoformat()
        self.tools = {
            'generate_audio':   {'status': 'idle', 'retries': 0, 'last_update': now},
            'generate_prompts': {'status': 'idle', 'retries': 0, 'last_update': now},
            'generate_images':  {'status': 'idle', 'retries': 0, 'last_update': now},
            'generate_video':   {'status': 'idle', 'retries': 0, 'last_update': now},
        }
        
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'project_name': self.project_name,
            'novel_text': self.novel_text[:100] + '...' if len(self.novel_text) > 100 else self.novel_text,
            'timbre': self.timbre,
            'mode': self.mode,
            'quality_target': self.quality_target,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'duration': f"{self.duration:.1f}秒" if self.duration else None,
            'error': self.error,
            'video_path': self.video_path,
            'thinking_log': self.thinking_log,
            'quality_score': self.quality_score
            , 'tools': self.tools
        }


def task_worker():
    """任务处理线程"""
    global current_task
    
    while True:
        task = task_queue.get()
        
        # 检查是否是单图重生任务（dict类型）
        if isinstance(task, dict) and task.get('type') == 'regenerate_single':
            # 处理单图重生任务
            try:
                print(f"🎨 处理单图重生任务: scene_{task['scene_index']:04d}")
                from agent_tools_single_image import regenerate_single_image_tool
                
                result = regenerate_single_image_tool(
                    project_name=task['project_name'],
                    scene_index=task['scene_index']
                )
                
                if result['success']:
                    print(f"✓ 单图重生完成: {result['message']}")
                else:
                    print(f"❌ 单图重生失败: {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ 单图重生任务失败: {e}")
                import traceback
                traceback.print_exc()
            
            continue  # 处理下一个任务
        
        # 正常的视频生成任务（Task对象）
        with task_lock:
            current_task = task
            task.status = 'running'
            task.start_time = datetime.now()
        broadcast_event({
            'type': 'task_update',
            'task': task.to_dict()
        })
        # pause gate before starting heavy work
        while task.task_id in paused_tasks:
            time.sleep(0.5)
        
        try:
            # 执行任务
            generator = VideoGenerator(task.project_name, task.novel_text, task.timbre)
            
            if task.mode == 'agent':
                # Agent模式 - 传递task对象用于实时更新
                task.current_step = '🤖 Agent模式启动中...'
                task.progress = 5
                _set_tool(task, 'generate_prompts', 'running')
                
                while task.task_id in paused_tasks:
                    time.sleep(0.5)
                result = generator.run_with_agent(quality_target=task.quality_target, task=task)
                
                if result and result.get('success'):
                    task.status = 'completed'
                    task.progress = 100
                    video_path = result.get('video_path')  # 设置video_path变量
                    task.video_path = video_path
                    task.thinking_log = result.get('thinking_log', [])
                    task.quality_score = result.get('quality_score')
                    task.current_step = f'✓ 完成 (质量: {task.quality_score:.2f})'
                    # 尽力标记工具完成（Agent内部已完成全流程）
                    _set_tool(task, 'generate_prompts', 'done')
                    _set_tool(task, 'generate_audio', 'done')
                    _set_tool(task, 'generate_images', 'done')
                    _set_tool(task, 'generate_video', 'done')
                else:
                    raise Exception("Agent执行失败")
            else:
                # 传统工作流模式
                # 步骤1: TTS
                task.current_step = '步骤1/4: 生成音频和字幕'
                task.progress = 10
                broadcast_event({'type': 'task_update', 'task': task.to_dict()})
                while task.task_id in paused_tasks:
                    time.sleep(0.5)
                _set_tool(task, 'generate_audio', 'running')
                if not generator.step1_generate_audio_and_subtitles():
                    _set_tool(task, 'generate_audio', 'error')
                    raise Exception("音频生成失败")
                _set_tool(task, 'generate_audio', 'done')
                
                # 步骤2: 提示词
                task.current_step = '步骤2/4: 生成AI绘画提示词'
                task.progress = 30
                broadcast_event({'type': 'task_update', 'task': task.to_dict()})
                while task.task_id in paused_tasks:
                    time.sleep(0.5)
                _set_tool(task, 'generate_prompts', 'running')
                if not generator.step2_generate_prompts():
                    _set_tool(task, 'generate_prompts', 'error')
                    raise Exception("提示词生成失败")
                _set_tool(task, 'generate_prompts', 'done')
                
                # 步骤3: 图像
                task.current_step = '步骤3/4: 生成分镜图像'
                task.progress = 50
                broadcast_event({'type': 'task_update', 'task': task.to_dict()})
                while task.task_id in paused_tasks:
                    time.sleep(0.5)
                _set_tool(task, 'generate_images', 'running')
                if not generator.step3_generate_images():
                    _set_tool(task, 'generate_images', 'error')
                    raise Exception("图像生成失败")
                _set_tool(task, 'generate_images', 'done')
                
                # 步骤4: 视频
                task.current_step = '步骤4/4: 合成视频'
                task.progress = 80
                broadcast_event({'type': 'task_update', 'task': task.to_dict()})
                while task.task_id in paused_tasks:
                    time.sleep(0.5)
                _set_tool(task, 'generate_video', 'running')
                video_path = generator.step4_generate_video()
                if not video_path:
                    _set_tool(task, 'generate_video', 'error')
                    raise Exception("视频合成失败")
                
                # 完成
                task.status = 'completed'
                task.progress = 100
                task.current_step = '✓ 完成'
                task.video_path = video_path
                broadcast_event({'type': 'task_update', 'task': task.to_dict()})
            
            # Agent模式已经设置了video_path，这里不需要再设置
            if task.mode != 'agent':
                task.current_step = '✓ 完成'
            
        except Exception as e:
            task.status = 'failed'
            task.error = str(e)
            # 将运行中的工具置为error
            try:
                for name, info in task.tools.items():
                    if info.get('status') == 'running':
                        _set_tool(task, name, 'error')
            except Exception:
                pass
            broadcast_event({'type': 'task_update', 'task': task.to_dict()})
            
        finally:
            task.end_time = datetime.now()
            task.duration = (task.end_time - task.start_time).total_seconds()
            
            with task_lock:
                task_history.append(task)
                current_task = None
            
            task_queue.task_done()


def _set_tool(task: 'Task', name: str, status: str):
    info = task.tools.get(name) or {'status': 'idle', 'retries': 0, 'last_update': datetime.now().isoformat()}
    if status == 'running' and info.get('status') == 'error':
        # 重试
        info['retries'] = int(info.get('retries') or 0) + 1
    info['status'] = status
    info['last_update'] = datetime.now().isoformat()
    task.tools[name] = info
    try:
        broadcast_event({'type': 'tool_update', 'task_id': task.task_id, 'tool': name, 'info': info})
    except Exception:
        pass


# 启动任务处理线程
worker_thread = threading.Thread(target=task_worker, daemon=True)
worker_thread.start()


@app.route('/')
def index():
    """首页"""
    return redirect('/react?view=agent')


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
    mode = data.get('mode', 'workflow')  # workflow 或 agent
    quality_target = float(data.get('quality_target', 0.8))  # Agent模式的目标质量
    
    if not project_name or not novel_text:
        return jsonify({'error': '项目名称和小说文本不能为空'}), 400
    
    # 处理音色：如果是空字符串，则随机选择一个
    if not timbre:
        import random
        timbre_dir = Path('Timbre')
        if timbre_dir.exists():
            timbre_files = [f.name for f in timbre_dir.glob('*.wav')]
            if timbre_files:
                timbre = random.choice(timbre_files)
                print(f"🎲 随机选择音色: {timbre}")
            else:
                timbre = None
        else:
            timbre = None
    
    # 创建任务
    task_id = f"task_{int(time.time())}"
    task = Task(task_id, project_name, novel_text, timbre, mode, quality_target)
    
    # 保存任务元数据
    project_dir = Path('projects') / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        'task_id': task_id,
        'project_name': project_name,
        'novel_text': novel_text,
        'timbre': timbre,
        'mode': mode,
        'quality_target': quality_target,
        'created_time': datetime.now().isoformat(),
        'status': 'pending',
        'agent_messages': [] if mode == 'agent' else None,
        'thinking_log': [] if mode == 'agent' else None
    }
    
    metadata_file = project_dir / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 元数据已保存: {metadata_file}")
    
    # 加入队列
    task_queue.put(task)
    
    mode_name = "Agent模式" if mode == 'agent' else "工作流模式"
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'mode': mode,
        'message': f'任务已加入队列 ({mode_name})'
    })


@app.route('/api/tasks')
def get_tasks():
    """获取所有任务（包括本地项目）"""
    with task_lock:
        tasks = []
        task_project_names = set()
        
        # 当前任务
        if current_task:
            d = current_task.to_dict()
            d['paused'] = current_task.task_id in paused_tasks
            tasks.append(d)
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
                # 检查是否有metadata.json（Agent任务）
                metadata_file = Path("projects") / project['project_name'] / "metadata.json"
                task_id = f"local_{project['project_name']}"
                mode = 'workflow'
                
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            # 使用真实的task_id
                            if 'task_id' in metadata:
                                task_id = metadata['task_id']
                            if 'mode' in metadata:
                                mode = metadata['mode']
                    except:
                        pass
                
                # 转换为任务格式
                task_dict = {
                    'task_id': task_id,
                    'project_name': project['project_name'],
                    'novel_text': '',
                    'timbre': '',
                    'mode': mode,
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


@app.route('/api/task/pause/<task_id>', methods=['POST'])
def pause_task(task_id):
    with task_lock:
        paused_tasks.add(task_id)
        if current_task and current_task.task_id == task_id:
            current_task.current_step = (current_task.current_step or '') + ' ⏸ 已暂停'
            broadcast_event({'type': 'task_update', 'task': current_task.to_dict()})
    return jsonify({'success': True})


@app.route('/api/queue/remove/<task_id>', methods=['POST'])
def remove_from_queue(task_id):
    """从等待队列移除任务（仅对pending且未运行的任务生效）"""
    with task_lock:
        new_q = queue.Queue()
        removed = False
        while not task_queue.empty():
            t = task_queue.get()
            if getattr(t, 'task_id', None) == task_id and not removed:
                removed = True
                continue
            new_q.put(t)
        # 替换队列
        while not new_q.empty():
            task_queue.put(new_q.get())
    return jsonify({"success": True, "removed": removed})


@app.route('/api/queue/top/<task_id>', methods=['POST'])
def move_task_to_top(task_id):
    """将等待中的任务置顶（放到队首）"""
    with task_lock:
        tasks_list = []
        target = None
        while not task_queue.empty():
            t = task_queue.get()
            if getattr(t, 'task_id', None) == task_id and target is None:
                target = t
            else:
                tasks_list.append(t)
        # 目标放到最前
        if target is not None:
            task_queue.put(target)
        for t in tasks_list:
            task_queue.put(t)
    return jsonify({"success": True, "moved": target is not None})


@app.route('/api/project_delete/<project_name>', methods=['DELETE'])
def project_delete(project_name):
    """删除本地项目目录（谨慎操作）"""
    from pathlib import Path
    import shutil
    project_dir = Path('projects') / project_name
    if not project_dir.exists():
        return jsonify({"success": False, "error": "项目不存在"}), 404
    # 不允许删除当前运行中的项目
    with task_lock:
        if current_task and current_task.project_name == project_name:
            return jsonify({"success": False, "error": "当前项目正在运行，无法删除"}), 400
    try:
        shutil.rmtree(project_dir)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/task/resume/<task_id>', methods=['POST'])
def resume_task(task_id):
    with task_lock:
        if task_id in paused_tasks:
            paused_tasks.discard(task_id)
            if current_task and current_task.task_id == task_id:
                broadcast_event({'type': 'task_update', 'task': current_task.to_dict()})
    return jsonify({'success': True})


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


@app.route('/static/projects/<path:filepath>')
def serve_project_files(filepath):
    """提供项目静态文件（图片等）"""
    file_path = Path('projects') / filepath
    if file_path.exists() and file_path.is_file():
        return send_file(file_path)
    return jsonify({'error': '文件不存在'}), 404


@app.route('/projects')
def projects_page():
    """项目列表页面（重定向到ReactPy）"""
    return redirect('/react?view=projects')


@app.route('/tasks')
def tasks_page():
    """任务管理页面（重定向到ReactPy）"""
    return redirect('/react?view=tasks')


@app.route('/edit/<project_name>')
def edit_page(project_name):
    """提示词编辑页面（重定向到ReactPy）"""
    return redirect(f'/react?view=edit&name={project_name}')


@app.route('/project/<project_name>')
def project_detail(project_name):
    """项目详情页面（重定向到ReactPy）"""
    return redirect(f'/react?view=project&name={project_name}')


@app.route('/agent')
def agent_workspace():
    """Agent智能工作台（独立页面，重定向到ReactPy）"""
    return redirect('/react?view=agent')


@app.route('/agent_chat')
def agent_chat():
    """Agent对话页面（兼容旧链接，重定向到ReactPy）"""
    return redirect('/react?view=agent')


# 用户消息队列（task_id -> 消息列表）
user_messages = {}

@app.route('/api/agent_message/<task_id>', methods=['POST'])
def send_agent_message(task_id):
    """发送消息给Agent"""
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400
    
    print(f"\n📨 收到用户消息 [task_id={task_id}]: {message}")
    
    # 检查任务状态
    with task_lock:
        task = None
        for t in task_history:
            if t.task_id == task_id:
                task = t
                break
        if current_task and current_task.task_id == task_id:
            task = current_task
        
        # 如果内存中没有，尝试从metadata.json恢复
        if not task:
            # 扫描所有项目，查找匹配的task_id
            projects_dir = Path("projects")
            if projects_dir.exists():
                for project_dir in projects_dir.iterdir():
                    if project_dir.is_dir():
                        metadata_file = project_dir / "metadata.json"
                        if metadata_file.exists():
                            try:
                                with open(metadata_file, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)
                                    if metadata.get('task_id') == task_id:
                                        # 找到了！从metadata恢复任务
                                        from agent import NovelToVideoAgent
                                        from agent_tools import AgentTools
                                        from kimi_api import KimiAPI
                                        
                                        # 创建Task对象
                                        task = Task(
                                            task_id=metadata['task_id'],
                                            project_name=metadata['project_name'],
                                            novel_text=metadata['novel_text'],
                                            timbre=metadata['timbre'],
                                            mode=metadata.get('mode', 'agent'),
                                            quality_target=metadata.get('quality_target', 0.8)
                                        )
                                        task.status = metadata.get('status', 'pending')
                                        
                                        # 添加到历史记录
                                        task_history.append(task)
                                        
                                        print(f"✓ 从metadata恢复任务: {task_id}")
                                        break
                            except Exception as e:
                                print(f"恢复任务失败: {e}")
                                continue
    
    if not task:
        print(f"⚠️ 任务不存在: {task_id}")
        return jsonify({'success': False, 'error': '任务不存在'}), 404
    
    if task.status == 'completed':
        print(f"⚠️ 任务已完成，无法继续。请创建新任务。")
        return jsonify({
            'success': False, 
            'error': '任务已完成，Agent模式不支持继续优化。如需重新生成，请创建新任务。'
        }), 400
    
    # 存储用户消息到内存
    if task_id not in user_messages:
        user_messages[task_id] = []
    
    user_messages[task_id].append({
        'message': message,
        'timestamp': time.time()
    })
    
    print(f"✓ 消息已加入队列，等待Agent处理...")
    # SSE: broadcast user message immediately
    try:
        broadcast_event({
            'type': 'agent_message',
            'task_id': task_id,
            'role': 'user',
            'message': message,
            'timestamp': time.time()
        })
    except Exception:
        pass
    
    # 如果任务是恢复的（不在运行中），需要重新启动Agent
    if task.mode == 'agent' and task.status == 'pending':
        print(f"🔄 检测到恢复的Agent任务，重新启动Agent...")
        
        # 将任务加入队列
        with task_lock:
            if task not in list(task_queue.queue) and task != current_task:
                task_queue.put(task)
                print(f"✓ 任务已加入执行队列")
        
        # 如果没有worker在运行，启动一个
        global worker_thread
        if worker_thread is None or not worker_thread.is_alive():
            worker_thread = threading.Thread(target=task_worker, daemon=True)
            worker_thread.start()
            print(f"✓ Agent工作线程已启动")
    
    # 保存到元数据文件
    try:
        # 从task_id找到project_name
        with task_lock:
            task = None
            for t in task_history:
                if t.task_id == task_id:
                    task = t
                    break
            if current_task and current_task.task_id == task_id:
                task = current_task
        
        if task:
            metadata_file = Path('projects') / task.project_name / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                if 'agent_messages' not in metadata:
                    metadata['agent_messages'] = []
                
                metadata['agent_messages'].append({
                    'role': 'user',
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                })
                
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存消息到元数据失败: {e}")
    
    return jsonify({'success': True, 'message': '消息已发送'})


@app.route('/api/agent_create_task', methods=['POST'])
def agent_create_task():
    """Agent智能创建任务"""
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({'success': False, 'error': '消息不能为空'}), 400
    
    try:
        # 获取可用音色列表（支持 wav 和 mp3）
        timbre_dir = Path('Timbre')
        available_timbres = []
        if timbre_dir.exists():
            wav_files = [f.stem for f in timbre_dir.glob('*.wav')]
            mp3_files = [f.stem for f in timbre_dir.glob('*.mp3')]
            WAV_files = [f.stem for f in timbre_dir.glob('*.WAV')]  # 大写扩展名
            available_timbres = wav_files + mp3_files + WAV_files
        
        # 使用LLM提取任务信息
        from tools.kimi_api import KimiAPI
        
        api = KimiAPI()
        
        # 构建音色列表（带描述）
        timbre_descriptions = {
            "御姐配音": "成熟、性感、有魅力的女性声音，适合都市言情、霸道总裁、职场小说",
            "软糯女孩": "温柔、甜美、可爱的女性声音，适合校园青春、甜宠、治愈系小说",
            "温暖闺蜜": "亲切、温和的女性声音，适合日常、生活、情感类小说",
            "温柔学姐": "知性、温柔的女性声音，适合校园、青春、成长类小说",
            "阅历姐姐": "成熟、有故事感的女性声音，适合都市、情感、人生感悟类小说",
            
            "温润男声": "温和、磁性的男性声音，适合现代言情、都市、温馨类小说",
            "温润青年": "清新、阳光的男性声音，适合校园、青春、励志类小说",
            "沉稳高管": "成熟、稳重的男性声音，适合职场、商战、霸道总裁类小说",
            "播音中年男": "专业、标准的男性声音，适合历史、传记、正剧类小说",
            "电台男主播": "磁性、深情的男性声音，适合情感、悬疑、都市类小说",
            
            "不羁青年": "洒脱、个性的男性声音，适合江湖、武侠、冒险类小说",
            "随性男青": "轻松、自然的男性声音，适合日常、搞笑、轻松类小说",
            "清澈弟弟": "清爽、年轻的男性声音，适合校园、青春、纯爱类小说",
            "南方小哥": "亲切、温和的男性声音，适合生活、温馨、治愈类小说",
            "北京大爷": "幽默、接地气的男性声音，适合市井、生活、搞笑类小说",
            
            "说书人": "传统、有韵味的声音，适合古风、武侠、历史、评书类小说",
            "抖音-读小说": "流行、现代的声音，适合网文、快节奏、爽文类小说"
        }
        
        # 构建音色列表（自动检测扩展名）
        timbre_list = []
        timbre_files_map = {}  # 存储音色名到完整文件名的映射
        
        for audio_file in timbre_dir.glob('*'):
            if audio_file.suffix.lower() in ['.wav', '.mp3']:
                name = audio_file.stem
                desc = timbre_descriptions.get(name, "通用音色")
                timbre_list.append(f"- {audio_file.name}: {desc}")
                timbre_files_map[name] = audio_file.name
        
        timbre_list_str = "\n".join(timbre_list) if timbre_list else "- 无可用音色"
        
        extract_prompt = f"""从用户消息中提取视频生成任务信息，并智能选择最合适的音色。

用户消息：
{message}

可用音色列表：
{timbre_list_str}

请提取以下信息：
1. 项目标题（简短，3-8个字，如果用户没提供则根据内容生成）
2. 小说内容（完整文本）
3. 音色选择（根据小说内容的风格、主角性别、故事类型，从音色列表中选择最合适的一个）
   - 如果用户明确指定了音色，使用用户指定的
   - 否则根据内容智能选择：
     * 女性主角/都市言情 → 御姐配音、软糯女孩、温柔学姐等
     * 男性主角/都市职场 → 沉稳高管、温润男声、电台男主播等
     * 古风/武侠/历史 → 说书人、播音中年男等
     * 轻松搞笑 → 北京大爷、随性男青等
   - **必须返回完整文件名**（包括扩展名，如"御姐配音.wav"或"温润男声.mp3"）
   - 从上面的音色列表中选择，不要自己编造

**重要**：返回的JSON中，所有字符串值必须正确转义特殊字符（引号、换行符等）。

以JSON格式返回：
{{
    "title": "项目标题",
    "content": "小说内容（注意转义引号和换行符）",
    "timbre": "完整音色文件名（必须从列表中选择，包含扩展名）"
}}

只返回JSON，不要有其他解释。"""
        
        messages = [{"role": "user", "content": extract_prompt}]
        response = api.chat(messages, temperature=0.3)
        
        if not response:
            return jsonify({'success': False, 'error': 'LLM提取失败'}), 500
        
        # 解析JSON
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        try:
            task_info = json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            # JSON解析失败，可能是因为内容中有特殊字符
            # 尝试使用更宽松的解析或直接从原始消息提取
            print(f"⚠️ JSON解析失败: {e}")
            print(f"原始响应: {json_str[:200]}...")
            
            # 回退方案：直接使用用户消息作为内容
            task_info = {
                "title": "视频生成任务",
                "content": message,
                "timbre": None
            }
        
        # 创建任务
        project_name = task_info['title']
        novel_text = task_info['content']
        timbre = task_info.get('timbre')
        
        # 处理音色
        if not timbre or timbre == "默认" or timbre == "null" or timbre == "None":
            # LLM没有选择音色，使用随机回退
            import random
            timbre_dir = Path('Timbre')
            if timbre_dir.exists():
                # 支持所有音频格式
                timbre_files = []
                for ext in ['*.wav', '*.mp3', '*.WAV', '*.MP3']:
                    timbre_files.extend([f.name for f in timbre_dir.glob(ext)])
                
                if timbre_files:
                    timbre = random.choice(timbre_files)
                    print(f"🎲 LLM未选择音色，随机选择: {timbre}")
                else:
                    timbre = None
            else:
                timbre = None
        else:
            print(f"🎤 LLM智能选择音色: {timbre}")
        
        # 创建任务
        task_id = f"task_{int(time.time())}"
        task = Task(task_id, project_name, novel_text, timbre, mode='agent', quality_target=0.8)
        
        # 保存任务元数据
        project_dir = Path('projects') / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            'task_id': task_id,
            'project_name': project_name,
            'novel_text': novel_text,
            'timbre': timbre,
            'mode': 'agent',
            'quality_target': 0.8,
            'created_time': datetime.now().isoformat(),
            'status': 'pending',
            'agent_messages': [],
            'thinking_log': []
        }
        
        metadata_file = project_dir / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 元数据已保存: {metadata_file}")
        
        # 加入队列
        task_queue.put(task)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'project_name': project_name,
            'message': f'任务创建成功：{project_name}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/agent_messages/<task_id>')
def get_agent_messages(task_id):
    """获取Agent对话消息（合并持久化与内存）"""
    msgs = []
    # 1) 从项目metadata读取持久化的 agent_messages
    try:
        projects_dir = Path('projects')
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    metadata_file = project_dir / 'metadata.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        if metadata.get('task_id') == task_id and 'agent_messages' in metadata:
                            # 标准化字段
                            for m in metadata['agent_messages']:
                                role = m.get('role') if isinstance(m, dict) else 'assistant'
                                text = m.get('message') if isinstance(m, dict) else str(m)
                                ts = m.get('timestamp') if isinstance(m, dict) else None
                                msgs.append({'role': role or 'assistant', 'message': text or '', 'timestamp': ts})
                            break
    except Exception:
        pass

    # 2) 合并内存中的临时用户消息
    try:
        mem_msgs = user_messages.get(task_id, [])
        for m in mem_msgs:
            msgs.append({'role': 'user', 'message': m.get('message',''), 'timestamp': m.get('timestamp')})
    except Exception:
        pass

    # 3) 如果当前任务在运行且有thinking_log，把最近的思考/回复也映射为assistant消息（尽力而为）
    try:
        with task_lock:
            if current_task and current_task.task_id == task_id and current_task.thinking_log:
                for entry in current_task.thinking_log[-50:]:
                    if isinstance(entry, dict):
                        text = entry.get('content') or entry.get('text') or json.dumps(entry, ensure_ascii=False)
                    else:
                        text = str(entry)
                    msgs.append({'role': 'assistant', 'message': text, 'timestamp': None})
    except Exception:
        pass

    # 去重（按相同role+message+timestamp判断）并保持顺序
    unique = []
    seen = set()
    for m in msgs:
        key = (m.get('role'), m.get('message'), m.get('timestamp'))
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)
    return jsonify(unique)


@app.route('/api/project_content/<project_name>')
def get_project_content(project_name):
    """获取项目生成的所有内容"""
    project_dir = Path('projects') / project_name
    
    if not project_dir.exists():
        return jsonify({})
    
    content = {}
    
    # 音频
    audio_file = project_dir / 'Audio' / 'audio.mp3'
    if audio_file.exists():
        content['audio'] = True
        
        # 字幕数量
        subtitle_file = project_dir / 'Audio' / 'Subtitles.json'
        if subtitle_file.exists():
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitles = json.load(f)
                content['subtitle_count'] = len(subtitles.get('subtitles', []))
    
    # 提示词
    prompts_file = project_dir / 'Prompts.json'
    if prompts_file.exists():
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
            scene_prompts = prompts_data.get('scene_prompts', [])
            content['prompts'] = [p.get('prompt', '') for p in scene_prompts]
    
    # 图像
    imgs_dir = project_dir / 'Imgs'
    if imgs_dir.exists():
        image_files = sorted(imgs_dir.glob('scene_*.png'))
        content['images'] = [
            {'index': int(f.stem.split('_')[1]), 'path': f'projects/{project_name}/Imgs/{f.name}'}
            for f in image_files
        ]
    
    # 视频
    videos_dir = project_dir / 'Videos'
    if videos_dir.exists():
        video_files = list(videos_dir.glob('*.mp4'))
        if video_files:
            content['video'] = True
    
    return jsonify(content)


@app.route('/api/audio/<project_name>')
def get_audio(project_name):
    """获取音频文件"""
    audio_file = Path('projects') / project_name / 'Audio' / 'audio.mp3'
    
    if not audio_file.exists():
        return jsonify({'error': '音频不存在'}), 404
    
    return send_file(audio_file, mimetype='audio/mpeg')


@app.route('/api/image/<project_name>/<int:scene_index>')
def get_image(project_name, scene_index):
    """获取分镜图片"""
    img_file = Path('projects') / project_name / 'Imgs' / f'scene_{scene_index:04d}.png'
    
    if not img_file.exists():
        return jsonify({'error': '图片不存在'}), 404
    
    return send_file(img_file, mimetype='image/png')


@app.route('/api/update_prompt/<project_name>/<int:scene_index>', methods=['POST'])
def update_prompt(project_name, scene_index):
    """更新单个场景的提示词并重新生成"""
    try:
        data = request.get_json()
        new_prompt = data.get('prompt', '').strip()
        
        if not new_prompt:
            return jsonify({'error': '提示词不能为空'}), 400
        
        # 读取提示词文件
        prompts_file = Path('projects') / project_name / 'Prompts.json'
        if not prompts_file.exists():
            return jsonify({'error': '提示词文件不存在'}), 404
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        # 更新对应场景的提示词
        updated = False
        for scene in prompts_data.get('scene_prompts', []):
            if scene['index'] == scene_index:
                scene['prompt'] = new_prompt
                updated = True
                break
        
        if not updated:
            return jsonify({'error': '找不到对应的场景'}), 404
        
        # 保存更新后的提示词
        with open(prompts_file, 'w', encoding='utf-8') as f:
            json.dump(prompts_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 提示词已更新: scene_{scene_index:04d}")
        
        # 调用重新生成API
        return regenerate_scene(project_name, scene_index)
        
    except Exception as e:
        print(f"❌ 更新提示词失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/regenerate_scene/<project_name>/<int:scene_index>', methods=['POST'])
def regenerate_scene(project_name, scene_index):
    """重新生成单个分镜"""
    try:
        print(f"\n重新生成场景 {scene_index}...")
        
        # 读取提示词
        prompts_file = Path('projects') / project_name / 'Prompts.json'
        if not prompts_file.exists():
            return jsonify({'error': '提示词文件不存在'}), 404
            
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
        
        print(f"提示词: {scene_prompt[:100]}...")
        
        # 直接调用图片生成（简化版）
        # 注意：这会阻塞请求，但单张图片生成较快
        project_dir = Path('projects') / project_name
        imgs_dir = project_dir / 'Imgs'
        imgs_dir.mkdir(exist_ok=True)
        
        # 调用 main.py 中的图片生成逻辑
        # 为了避免重新加载模型，我们直接导入并使用
        import sys
        import torch
        from pathlib import Path as P
        
        # 添加项目根目录到路径
        if str(P(__file__).parent) not in sys.path:
            sys.path.insert(0, str(P(__file__).parent))
        
        # 导入图片生成函数（假设在main.py中）
        # 由于main.py中的代码比较复杂，这里简化处理
        # 直接返回成功，实际生成由前端的"重新生成全部"来完成
        
        print(f"✓ 场景 {scene_index} 提示词已更新，请点击'重新生成全部图像'来应用更改")
        
        return jsonify({
            'success': True,
            'message': f'场景 {scene_index} 的提示词已更新。请点击"重新生成全部图像"按钮来应用更改。',
            'note': '单张图片重新生成功能需要加载SDXL模型，建议批量重新生成以提高效率。'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regenerate_single_image/<project_name>/<int:scene_index>', methods=['POST'])
def regenerate_single_image(project_name, scene_index):
    """重新生成单张图片（使用共享模型池）"""
    try:
        print(f"\n🎨 重新生成单张图片: scene_{scene_index:04d}")
        
        # 添加到任务队列
        task_data = {
            'type': 'regenerate_single',
            'project_name': project_name,
            'scene_index': scene_index,
            'timestamp': time.time()
        }
        
        # 使用全局队列处理（避免重复加载模型）
        task_queue.put(task_data)
        
        return jsonify({
            'success': True,
            'message': f'场景 {scene_index} 正在重新生成...'
        })
        
    except Exception as e:
        print(f"❌ 单张图片重新生成失败: {e}")
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


# 废弃：Agent模式不支持继续任务，请重新生成
# @app.route('/api/continue_project/<project_name>', methods=['POST'])
# def continue_project(project_name):
#     """继续未完成的项目 - 已废弃"""
#     return jsonify({'error': 'Agent模式不支持继续任务，请重新生成项目'}), 400


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
