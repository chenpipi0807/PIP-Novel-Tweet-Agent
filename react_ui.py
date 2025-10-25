from __future__ import annotations
import json
import asyncio
from urllib.parse import urlencode, urljoin
from reactpy import component, html, hooks
from reactpy.backend.flask import use_request
import httpx


def _qs(params: dict) -> str:
    q = urlencode({k: v for k, v in params.items() if v is not None})
    return f"?{q}" if q else ""


async def api_get_json(req, path: str):
    base = req.host_url.rstrip("/")
    url = urljoin(base + "/", path.lstrip("/"))
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        if resp.status_code >= 400:
            raise RuntimeError(f"GET {path} failed: {resp.status_code}")
        return resp.json()


async def api_post_json(req, path: str, data: dict):
    base = req.host_url.rstrip("/")
    url = urljoin(base + "/", path.lstrip("/"))
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json=data)
        res_json = resp.json()
        if resp.status_code >= 400:
            err = res_json.get("error") if isinstance(res_json, dict) else res_json
            raise RuntimeError(err or f"POST {path} failed: {resp.status_code}")
        return res_json


async def api_delete(req, path: str):
    base = req.host_url.rstrip("/")
    url = urljoin(base + "/", path.lstrip("/"))
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.delete(url)
        res_json = resp.json() if resp.content else {"success": resp.status_code < 400}
        if resp.status_code >= 400:
            err = res_json.get("error") if isinstance(res_json, dict) else res_json
            raise RuntimeError(err or f"DELETE {path} failed: {resp.status_code}")
        return res_json


@component
def IndexPage():
    req = use_request()
    timbres, set_timbres = hooks.use_state([])
    project_name, set_project_name = hooks.use_state("")
    novel_text, set_novel_text = hooks.use_state("")
    timbre, set_timbre = hooks.use_state("")
    alert, set_alert = hooks.use_state("")
    auto_generate, set_auto_generate = hooks.use_state(True)
    created_task_id, set_created_task_id = hooks.use_state("")

    def clean_project_name(text: str) -> str:
        if not text:
            return ""
        import re, time
        # 保留中文、字母、数字和下划线，去掉其他符号
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
        if len(cleaned) < 2:
            cleaned = f"novel_{str(int(time.time()))[-6:]}"
        return cleaned

    def generate_project_name(text: str) -> str:
        if not text or len(text) < 5:
            return ""
        name = clean_project_name(text[:10])
        return name

    @hooks.use_effect
    async def _load_timbres():
        try:
            data = await api_get_json(req, "/api/timbres")
            set_timbres(data)
        except Exception:
            set_timbres([])
        return

    def on_text_input(value: str):
        set_novel_text(value)
        if auto_generate and value and len(value) >= 5:
            set_project_name(generate_project_name(value))

    async def on_submit(event):
        print("[前端] 用户点击：创建任务按钮")
        set_alert("")
        set_created_task_id("")
        try:
            pn = clean_project_name(project_name) or generate_project_name(novel_text)
            print(f"[前端] 创建任务 - 项目名: {pn}, 音色: {timbre or '随机'}, 文本长度: {len(novel_text)}")
            payload = {
                "project_name": pn,
                "novel_text": novel_text,
                "timbre": timbre,
                "mode": "workflow",
            }
            res = await api_post_json(req, "/api/create_task", payload)
            print(f"[前端] 任务创建成功 - task_id: {res.get('task_id', '')}")
            set_alert(f"✓ {res.get('message','创建成功')}")
            set_created_task_id(res.get("task_id") or "")
        except Exception as e:
            print(f"[前端] 任务创建失败: {str(e)}")
            set_alert(f"❌ {str(e)}")

    # 简化的统计
    sentences = len([s for s in novel_text.split("。") if s.strip()])
    minutes = (sentences * 4 + 59) // 60 if sentences else 0

    return html.div({"class": "content"},
        html.h2({"style": {"marginBottom": "16px"}}, "传统模式 - 创建任务"),
        alert and html.div({"class": "alert"}, alert),
        (created_task_id and html.div({"style": {"margin": "8px 0", "display": "flex", "gap": "12px"}},
            html.a({"href": "/react?view=tasks", "class": "btn"}, "查看任务管理"),
            html.a({"href": f"/react?view=project&name={(clean_project_name(project_name) or generate_project_name(novel_text))}", "class": "btn"}, "查看项目详情")
        )) or None,
        html.div({"class": "form-group"},
            html.label({"for": "project_name"}, "项目名称 *"),
            html.input({
                "id": "project_name",
                "value": project_name,
                "on_input": lambda e: (set_project_name(e["target"]["value"]), set_auto_generate(False)),
                "placeholder": "自动生成或手动输入",
            }),
            html.small({}, "只能包含字母、数字、下划线（系统会自动从小说标题生成）"),
        ),
        html.div({"class": "form-group"},
            html.label({"for": "timbre"}, "选择音色"),
            html.select({
                "id": "timbre",
                "value": timbre,
                "on_change": lambda e: set_timbre(e["target"]["value"]),
            },
                html.option({"value": ""}, "🎲 随机音色"),
                [html.option({"value": t}, t) for t in timbres]
            ),
        ),
        
        html.div({"class": "form-group"},
            html.label({"for": "novel_text"}, "小说文本 *"),
            html.textarea({
                "id": "novel_text", "value": novel_text,
                "on_input": lambda e: on_text_input(e["target"]["value"]),
                "placeholder": "输入小说内容...\n\n建议200字以内，系统会自动分句生成分镜。",
            }),
            html.small({},
                html.span({}, [
                    html.span({}, ["字数: ", html.span({"style": {"color": "#6366f1"}}, str(len(novel_text)))]),
                    " ",
                    html.span({}, ["预计分镜: ", html.span({"style": {"color": "#6366f1"}}, str(sentences)), "个"]),
                    " ",
                    html.span({}, ["预计时长: ", html.span({"style": {"color": "#6366f1"}}, str(minutes)), "分钟"]),
                ])
            ),
        ),
        html.button({"class": "btn", "type": "button", "on_click": on_submit}, "🚀 创建任务"),
    )


@component
def TasksPage():
    req = use_request()
    items, set_items = hooks.use_state([])
    status_filter, set_status_filter = hooks.use_state('all')
    page, set_page = hooks.use_state(1)
    page_size = 10

    @hooks.use_effect
    async def _poll():
        cancelled = False

        async def load_once():
            try:
                data = await api_get_json(req, "/api/tasks")
                set_items(data)
            except Exception:
                pass

        async def loop():
            while not cancelled:
                await load_once()
                await asyncio.sleep(5)

        task = asyncio.create_task(loop())

        def cleanup():
            nonlocal cancelled
            cancelled = True
            try:
                task.cancel()
            except Exception:
                pass
        return cleanup

    def badge(status: str):
        color_map = {
            "pending": "#f59e0b",
            "running": "#3b82f6",
            "completed": "#22c55e",
            "failed": "#ef4444"
        }
        bg = color_map.get(status, "#9ca3af")
        return html.span({"class": "badge", "style": {"background": bg}}, status)

    def progress_bar(pct: int):
        width = max(0, min(100, int(pct or 0)))
        return html.div({"class": "progress"},
            html.div({"class": "progress-inner", "style": {"width": f"{width}%"}}, f"{width}%")
        )

    def mode_badge(mode: str):
        if mode == 'agent':
            return html.span({"class": "badge", "style": {"background": "#8b5cf6"}}, "Agent")
        return html.span({"class": "badge", "style": {"background": "#374151"}}, "传统")

    def row_view(t: dict):
        tid = t.get('task_id', '') or t.get('project_name','')
        pname = t.get('project_name','')
        mode = t.get('mode','')
        status = t.get('status','')
        paused = bool(t.get('paused'))

        async def on_queue_remove(event):
            print(f"[前端] 用户点击：移除队列 - task_id: {tid}")
            await api_post_json(req, f"/api/queue/remove/{tid}", {})
            print(f"[前端] 队列移除完成 - task_id: {tid}")
            await _refresh(req, set_items)

        async def on_queue_top(event):
            print(f"[前端] 用户点击：队列置顶 - task_id: {tid}")
            await api_post_json(req, f"/api/queue/top/{tid}", {})
            print(f"[前端] 队列置顶完成 - task_id: {tid}")
            await _refresh(req, set_items)

        async def on_pause(event):
            print(f"[前端] 用户点击：暂停任务 - task_id: {tid}")
            await api_post_json(req, f"/api/task/pause/{tid}", {})
            print(f"[前端] 任务暂停完成 - task_id: {tid}")
            await _refresh(req, set_items)

        async def on_resume(event):
            print(f"[前端] 用户点击：继续任务 - task_id: {tid}")
            await api_post_json(req, f"/api/task/resume/{tid}", {})
            print(f"[前端] 任务继续完成 - task_id: {tid}")
            await _refresh(req, set_items)

        async def on_delete_project(event):
            # 注意：后端会阻止删除正在运行的项目
            print(f"[前端] 用户点击：删除项目 - project_name: {pname}")
            await api_delete(req, f"/api/project_delete/{pname}")
            print(f"[前端] 项目删除完成 - project_name: {pname}")
            await _refresh(req, set_items)

        async def on_regen_video(event):
            print(f"[前端] 用户点击：重新合成视频 - project_name: {pname}")
            await api_post_json(req, f"/api/regenerate_video/{pname}", {})
            print(f"[前端] 视频重新合成完成 - project_name: {pname}")
            await _refresh(req, set_items)

        async def on_regen_images(event):
            print(f"[前端] 用户点击：重新生成图像 - project_name: {pname}")
            await api_post_json(req, f"/api/regenerate_images/{pname}", {})
            print(f"[前端] 图像重新生成完成 - project_name: {pname}")
            await _refresh(req, set_items)

        def action_btn(label, on_click=None, href=None, variant="normal"):
            """操作按钮 - 简洁版"""
            colors = {
                "primary": {"bg": "#5865f2", "hover": "#4752c4"},
                "success": {"bg": "#3ba55d", "hover": "#2d7d46"},
                "danger": {"bg": "#ed4245", "hover": "#c03537"},
                "normal": {"bg": "#4e5058", "hover": "#6d6f78"}
            }
            color = colors.get(variant, colors["normal"])
            
            btn_style = {
                "padding": "4px 12px",
                "fontSize": "12px",
                "backgroundColor": color["bg"],
                "color": "#fff",
                "border": "none",
                "borderRadius": "4px",
                "cursor": "pointer",
                "whiteSpace": "nowrap",
                "textDecoration": "none",
                "display": "inline-block"
            }
            
            if href:
                return html.a({"href": href, "style": btn_style}, label)
            return html.button({"type": "button", "on_click": on_click, "style": btn_style}, label)

        def ops_cell():
            """操作列 - 根据状态显示不同按钮"""
            buttons = []
            
            # 排队中
            if status == 'pending':
                buttons.append(action_btn("置顶", on_queue_top, variant="primary"))
                buttons.append(action_btn("移除", on_queue_remove, variant="danger"))
                if mode == 'agent':
                    buttons.append(action_btn("工作台", href=f"/react?view=agent{_qs({'task_id': tid})}"))
            
            # 进行中
            elif status == 'running':
                if paused:
                    buttons.append(action_btn("继续", on_resume, variant="success"))
                else:
                    buttons.append(action_btn("暂停", on_pause, variant="normal"))
                buttons.append(action_btn("置顶", on_queue_top, variant="primary"))
                if mode == 'agent':
                    buttons.append(action_btn("工作台", href=f"/react?view=agent{_qs({'task_id': tid})}"))
            
            # 已完成
            elif status == 'completed':
                buttons.append(action_btn("查看", href=f"/react?view=project&name={pname}", variant="primary"))
                buttons.append(action_btn("重新生成", on_regen_video, variant="normal"))
                buttons.append(action_btn("删除", on_delete_project, variant="danger"))
            
            # 失败
            elif status == 'failed':
                buttons.append(action_btn("重试", on_regen_video, variant="success"))
                buttons.append(action_btn("查看", href=f"/react?view=project&name={pname}"))
                buttons.append(action_btn("删除", on_delete_project, variant="danger"))
            
            # 其他状态
            else:
                buttons.append(action_btn("查看", href=f"/react?view=project&name={pname}"))
                buttons.append(action_btn("删除", on_delete_project, variant="danger"))
            
            return html.div({"style": {"display": "flex", "gap": "6px", "flexWrap": "wrap"}}, buttons)
        return html.tr({"id": f"row-{tid}"},
            html.td({"id": f"name-{tid}"}, html.a({"href": f"/react?view=project&name={pname}"}, pname)),
            html.td({"id": f"mode-{tid}"}, mode_badge(mode)),
            html.td({}, html.span({"id": f"status-{tid}", "class": "badge"}, t.get('status',''))),
            html.td({}, html.div({"class": "progress"}, html.div({"id": f"prog-{tid}", "class": "progress-inner", "style": {"width": f"{int(t.get('progress',0))}%"}}, f"{int(t.get('progress',0))}%"))),
            html.td({"id": f"step-{tid}"}, t.get('current_step','')),
            html.td({"id": f"start-{tid}"}, (t.get('start_time') or '') or ''),
            html.td({"id": f"end-{tid}"}, (t.get('end_time') or '') or ''),
            html.td({}, ops_cell()),
        )

    async def do_refresh(event):
        print("[前端] 用户点击：刷新任务列表")
        await _refresh(req, set_items)
        print("[前端] 任务列表刷新完成")

    # filtering and pagination
    def apply_filter(items_list):
        if status_filter == 'all':
            return items_list
        mapping = {'pending': 'pending', 'running': 'running', 'completed': 'completed'}
        return [t for t in items_list if (t.get('status') or '') == mapping.get(status_filter, '')]

    filtered = apply_filter(items)
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page_clamped = max(1, min(page, total_pages))
    start = (page_clamped - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    def set_filter(val):
        print(f"[前端] 用户点击：筛选任务 - filter: {val}")
        set_status_filter(val)
        set_page(1)

    return html.div({"class": "content"},
        html.h2({}, "任务列表 (ReactPy)"),
        html.div({"style": {"display": "flex", "gap": "12px", "margin": "12px 0", "alignItems": "center"}},
            html.div({"class": "nav", "style": {"padding": "0", "background": "transparent", "border": "none"}},
                html.a({"href": "#", "class": "" if status_filter!='all' else "active", "on_click": lambda e: set_filter('all')}, "全部"),
                html.a({"href": "#", "class": "" if status_filter!='pending' else "active", "on_click": lambda e: set_filter('pending')}, "排队中"),
                html.a({"href": "#", "class": "" if status_filter!='running' else "active", "on_click": lambda e: set_filter('running')}, "进行中"),
                html.a({"href": "#", "class": "" if status_filter!='completed' else "active", "on_click": lambda e: set_filter('completed')}, "已完成"),
            ),
            html.div({"style": {"flex": 1}}),
            html.button({"class": "btn", "type": "button", "on_click": do_refresh}, "刷新")
        ),
        html.table({"class": "table", "style": {"tableLayout": "fixed", "width": "100%"}},
            html.colgroup({},
                html.col({"style": {"width": "14%"}}),  # 项目名
                html.col({"style": {"width": "7%"}}),   # 类型
                html.col({"style": {"width": "8%"}}),   # 状态
                html.col({"style": {"width": "10%"}}),  # 进度
                html.col({"style": {"width": "11%"}}),  # 当前步骤
                html.col({"style": {"width": "12%"}}),  # 开始时间
                html.col({"style": {"width": "12%"}}),  # 结束时间
                html.col({"style": {"width": "26%"}}),  # 操作（大幅加宽，容纳多个按钮）
            ),
            html.thead({},
                html.tr({},
                    html.th({}, "项目名"),
                    html.th({}, "类型"),
                    html.th({}, "状态"),
                    html.th({}, "进度"),
                    html.th({}, "当前步骤"),
                    html.th({}, "开始时间"),
                    html.th({}, "结束时间"),
                    html.th({}, "操作"),
                )
            ),
            html.tbody({}, [row_view(t) for t in page_items])
        ),
        html.div({"style": {"display": "flex", "justifyContent": "flex-end", "gap": "8px", "marginTop": "12px"}},
            html.span({}, f"第 {page_clamped}/{total_pages} 页，共 {total} 条"),
            html.button({"class": "btn", "type": "button", "on_click": lambda e: (print("[前端] 用户点击：任务列表上一页"), set_page(max(1, page_clamped-1)))}, "上一页"),
            html.button({"class": "btn", "type": "button", "on_click": lambda e: (print("[前端] 用户点击：任务列表下一页"), set_page(min(total_pages, page_clamped+1)))}, "下一页"),
        )
    )


async def _refresh(req, set_items):
    try:
        data = await api_get_json(req, "/api/tasks")
        set_items(data)
    except Exception:
        pass


@component
def AgentWorkspacePage():
    req = use_request()
    from urllib.parse import parse_qs, urlparse
    qs = parse_qs(urlparse(req.full_path).query)
    initial_task_id = (qs.get("task_id") or [""])[0]

    # states
    tip, set_tip = hooks.use_state("")
    project_name, set_project_name = hooks.use_state("")
    task, set_task = hooks.use_state({})
    content, set_content = hooks.use_state({})
    messages, set_messages = hooks.use_state([])
    typing, set_typing = hooks.use_state(False)
    last_assistant_ts, set_last_assistant_ts = hooks.use_state("")
    tasks_list, set_tasks_list = hooks.use_state([])
    sel_task_id, set_sel_task_id = hooks.use_state(initial_task_id)

    # 用于清空输入框的计数器
    clear_counter, set_clear_counter = hooks.use_state(0)
    
    def handle_keydown(event):
        """处理键盘事件：Enter发送，Shift+Enter换行"""
        if event["key"] == "Enter" and not event.get("shiftKey", False):
            # 异步调用 send_message
            import asyncio
            asyncio.create_task(send_message(event))
    
    async def send_message(event):
        try:
            # 从事件对象读取输入框的值
            current_msg = event.get("target", {}).get("value", "").strip()
            if not current_msg:
                set_tip("❗ 请输入消息")
                return
            if not sel_task_id:
                # 无任务时，使用当前输入创建一个Agent任务
                if not current_msg:
                    set_tip("❗ 请输入消息后再创建任务")
                    return
                print(f"[前端] 用户点击：发送消息/创建Agent任务 - 消息: {current_msg[:50]}...")
                # 乐观回显
                now = {"role": "user", "message": current_msg, "timestamp": ""}
                set_messages((messages or []) + [now])
                res = await api_post_json(req, "/api/agent_create_task", {"message": current_msg})
                if res.get("success"):
                    new_tid = res.get("task_id") or ""
                    print(f"[前端] Agent任务创建成功 - task_id: {new_tid}, project_name: {res.get('project_name', '')}")
                    set_sel_task_id(new_tid)
                    set_tip(f"✓ 已创建任务：{res.get('project_name','')}，并发送首条消息")
                    set_clear_counter(clear_counter + 1)  # 触发清空
                    set_typing(True)
                else:
                    print(f"[前端] Agent任务创建失败: {res.get('error', '未知错误')}")
                    set_tip(res.get("error") or "创建任务失败")
                return
            # 已有任务，直接发送
            print(f"[前端] 用户点击：发送消息 - task_id: {sel_task_id}, 消息: {current_msg[:50]}...")
            set_messages((messages or []) + [{"role": "user", "message": current_msg, "timestamp": ""}])
            await api_post_json(req, f"/api/agent_message/{sel_task_id}", {"message": current_msg})
            print(f"[前端] 消息发送成功 - task_id: {sel_task_id}")
            set_tip("✓ 已发送")
            set_clear_counter(clear_counter + 1)  # 触发清空
            set_typing(True)
        except Exception as e:
            print(f"[前端] 消息发送失败: {str(e)}")
            set_tip(f"❌ {str(e)}")

    @hooks.use_effect
    async def _poll_all():
        cancelled = False

        async def load_tasks():
            try:
                data = await api_get_json(req, "/api/tasks")
                # Only update if task count or task IDs/status changed
                should_update = len(data) != len(tasks_list)
                if not should_update:
                    # Compare task IDs and statuses
                    data_keys = {(t.get('task_id'), t.get('status')) for t in data}
                    old_keys = {(t.get('task_id'), t.get('status')) for t in tasks_list}
                    should_update = data_keys != old_keys
                
                if should_update:
                    set_tasks_list(data)
                
                # 若未选择任务，自动选一个最近的agent任务（running优先，否则pending）
                nonlocal sel_task_id
                if not sel_task_id:
                    run = next((t for t in data if t.get('mode')=='agent' and t.get('status')=='running'), None)
                    pend = next((t for t in data if t.get('mode')=='agent' and t.get('status')=='pending'), None)
                    if run:
                        set_sel_task_id(run.get('task_id') or '')
                    elif pend:
                        set_sel_task_id(pend.get('task_id') or '')
            except Exception:
                pass

        async def resolve_task_and_project():
            if not sel_task_id:
                return
            try:
                data = await api_get_json(req, "/api/tasks")
                for t in data:
                    if t.get("task_id") == sel_task_id:
                        set_task(t)
                        set_project_name(t.get("project_name") or "")
                        break
            except Exception:
                pass

        async def load_messages():
            if not sel_task_id:
                return
            try:
                data = await api_get_json(req, f"/api/agent_messages/{sel_task_id}")
                # Only update if message count or last message changed
                data_len = len(data)
                msg_len = len(messages)
                should_update = data_len != msg_len
                if not should_update and data_len > 0 and msg_len > 0:
                    # Compare last message content (ignore timestamp)
                    last_new = data[-1]
                    last_old = messages[-1]
                    if (last_new.get('role') != last_old.get('role') or 
                        last_new.get('message') != last_old.get('message')):
                        should_update = True
                
                if should_update:
                    set_messages(data)
                
                # 检测是否收到新的 assistant 回复，用于关闭“正在思考”
                try:
                    last_assist = next((m for m in reversed(data) if (m.get('role')=='assistant' and (m.get('message') or '').strip())), None)
                except Exception:
                    last_assist = None
                if last_assist:
                    ts = str(last_assist.get('timestamp') or '')
                    if ts and ts != (last_assistant_ts or ''):
                        set_last_assistant_ts(ts)
                        set_typing(False)
            except Exception:
                pass

        async def load_content():
            if not project_name:
                return
            try:
                c = await api_get_json(req, f"/api/project_content/{project_name}")
                # Only update if key fields changed
                new_data = c or {}
                should_update = False
                
                # Compare key fields that matter for display
                if len(new_data) != len(content):
                    should_update = True
                else:
                    # Check if key content fields changed
                    for key in ['novel_text', 'script', 'status', 'progress']:
                        if new_data.get(key) != content.get(key):
                            should_update = True
                            break
                
                if should_update:
                    set_content(new_data)
            except Exception:
                pass

        await load_tasks()
        await resolve_task_and_project()

        async def loop():
            while not cancelled:
                await load_tasks()
                await resolve_task_and_project()
                await load_messages()
                await load_content()
                await asyncio.sleep(5)

        t = asyncio.create_task(loop())

        def cleanup():
            nonlocal cancelled
            cancelled = True
            try:
                t.cancel()
            except Exception:
                pass
        return cleanup

    # helpers
    def progress_card():
        prog = int(task.get('progress', 0) or 0)
        step = task.get('current_step', '') or ''
        return html.div({"class": "card"},
            html.h4({}, "任务进度"),
            html.div({"class": "progress"}, html.div({"id": "agent-prog", "data-project": project_name or "", "class": "progress-inner", "style": {"width": f"{prog}%"}}, f"{prog}%")),
            html.div({"style": {"marginTop": "8px"}},
                html.div({"id": "agent-step", "data-project": project_name or ""}, step)
            )
        )

    def quality_card():
        score = task.get('quality_score')
        return html.div({"class": "card"},
            html.h4({}, "质量评分"),
            html.div({}, str(score) if score is not None else "无")
        )

    def tools_card():
        tools = task.get('tools') or {}
        task_status = task.get('status') or ''
        end_time = task.get('end_time') or ''
        current_step = task.get('current_step') or ''
        def row(key, title):
            info = tools.get(key) or {}
            status = info.get('status') or 'idle'
            retries = info.get('retries', 0)
            last = info.get('last_update', '')
            # 当任务已完成但没有工具状态或全部idle时，显示为已完成
            if task_status == 'completed' and (not tools or status == 'idle'):
                status = 'done'
                last = end_time or last
            # 当任务进行中且当前步骤匹配工具时，显示执行中
            if task_status == 'running' and (current_step.find(key) != -1):
                status = 'running'
            # 状态徽标class将在SSE里同步设置，这里也初始设置
            def status_cls(s):
                return 'badge-running' if s=='running' else ('badge-done' if s=='done' else ('badge-error' if s=='error' else 'badge-idle'))
            def status_text(s):
                return '执行中' if s=='running' else ('已完成' if s=='done' else ('出错' if s=='error' else '待机'))
            return html.div({"style": {"display": "flex", "justifyContent": "space-between", "alignItems": "center", "padding": "8px 6px", "borderBottom": "1px solid #2d3548"}},
                html.div({"class": "nowrap"}, title),
                html.span({"id": f"tool-{key}-status", "class": f"badge {status_cls(status)}"}, status_text(status))
            )
        return html.div({"class": "card"},
            html.h4({}, "工具状态"),
            row('generate_audio',   '生成音频'),
            row('generate_prompts','生成提示词'),
            row('generate_images', '生成图像'),
            row('generate_video',  '合成视频')
        )

    def previews_card():
        imgs_all = content.get('images') or []
        # 分页：每页12张
        thumbs_per_page = 12
        img_page, set_img_page = hooks.use_state(1)

        total = len(imgs_all)
        total_pages = max(1, (total + thumbs_per_page - 1) // thumbs_per_page)
        page = max(1, min(img_page, total_pages))
        start = (page - 1) * thumbs_per_page
        end = start + thumbs_per_page
        imgs = imgs_all[start:end]

        items = []
        for img in imgs:
            items.append(
                html.div({"class": "card", "style": {"padding": "6px"}},
                    html.div({"class": "mono", "style": {"fontSize": "12px"}}, f"scene_{img.get('index',0):04d}"),
                    html.img({"src": f"/api/image/{project_name}/{int(img.get('index',0))}", "style": {"width": "100%", "borderRadius": "6px", "marginTop": "4px"}})
                )
            )
        return html.div({"class": "card"},
            html.h4({}, "生成内容预览"),
            html.div({"class": "grid", "style": {"gridTemplateColumns": "repeat(3, 1fr)", "gap": "8px"}}, items),
            html.div({"style": {"display": "flex", "justifyContent": "flex-end", "gap": "8px", "marginTop": "8px"}},
                html.span({}, f"第 {page}/{total_pages} 页，共 {total} 张"),
                html.button({"class": "btn", "type": "button", "on_click": lambda e: (print("[前端] 用户点击：预览图片上一页"), set_img_page(max(1, page-1)))}, "上一页"),
                html.button({"class": "btn", "type": "button", "on_click": lambda e: (print("[前端] 用户点击：预览图片下一页"), set_img_page(min(total_pages, page+1)))}, "下一页")
            )
        )

    def video_card():
        has_video = bool(content.get('video'))
        vts, set_vts = hooks.use_state(0)
        base = f"/api/video/{project_name}"
        src = has_video and f"{base}?v={vts}" or ""
        async def on_refresh(e):
            set_vts(vts + 1)
        return html.div({"class": "card"},
            html.div({"style": {"display": "flex", "justifyContent": "space-between", "alignItems": "center"}},
                html.h4({}, "视频预览"),
                has_video and html.button({"class": "btn", "type": "button", "on_click": lambda e: (print(f"[前端] 用户点击：刷新视频 - project_name: {project_name}"), on_refresh(e))}, "刷新视频") or None
            ),
            has_video and html.video({"id": "project-video", "data-project": project_name or "", "data-src-base": base, "src": src, "controls": True, "style": {"width": "100%", "borderRadius": "8px"}}) or html.div({"class": "mono", "style": {"color": "#9ca3af"}}, "暂无视频，完成后会自动出现")
        )

    def chat_item(m):
        ts = m.get('timestamp', '')
        text = m.get('message', '')
        role = m.get('role', 'user')
        bubble_cls = "chat-bubble-left" if role == 'assistant' else "chat-bubble-right"
        return html.li({"class": bubble_cls},
            html.div({"class": "chat-meta"}, role, " · ", str(ts)),
            html.div({"class": "chat-text"}, text)
        )

    # 左侧任务搜索过滤
    task_query, set_task_query = hooks.use_state("")

    def filtered_tasks():
        q = (task_query or "").strip().lower()
        items = [t for t in tasks_list if t.get('mode')=='agent']
        if not q:
            return items
        def match(t):
            name = (t.get('project_name','') or '').lower()
            return q in name
        return [t for t in items if match(t)]

    return html.div({"class": "content"},
        html.div({"class": "grid", "style": {"gridTemplateColumns": "260px 3fr 1fr", "alignItems": "start", "gap": "20px"}},
            # left: task list
            html.div({"class": "card leftbar"},
                html.h4({}, "任务列表"),
                html.input({"placeholder": "搜索任务...", "class": "chat-textbox", "value": task_query, "on_input": lambda e: set_task_query(e["target"]["value"]), "style": {"marginBottom": "8px"}}),
                html.div({"class": "task-list"},
                    [
                        html.div({
                            "class": f"task-item {'active' if (t.get('task_id')==sel_task_id) else ''}",
                            "on_click": (lambda e, tid=t.get('task_id',''), pname=t.get('project_name',''): (
                                print(f"[前端] 用户点击：选择任务 - task_id: {tid}, project_name: {pname}"), 
                                set_sel_task_id(tid)
                            ))
                        },
                            html.div({"style": {"display": "flex", "alignItems": "center", "gap": "8px"}},
                                html.span({"class": f"dot {t.get('status','')}"}),
                                html.span({"style": {"flex": "1"}}, t.get('project_name',''))
                            )
                        ) for t in filtered_tasks()
                    ]
                )
            ),
            # middle: chat panel
            html.div({"class": "card", "style": {"display": "flex", "flexDirection": "column", "minHeight": "70vh"}},
                html.div({"class": "chat-header"},
                    html.h3({}, "Agent 智能对话"),
                    (project_name and html.span({"class": "badge"}, project_name)) or None
                ),
                html.ul({"id": "agent-messages", "data-task": sel_task_id or "", "data-sse": "off", "class": "chat-list", "style": {"flex": 1}}, [*([chat_item(m) for m in messages]), (typing and html.li({"class": "tl-step"}, "正在思考…")) or None]),
                html.div({"class": "chat-input", "key": "chat-input-container"},
                    html.textarea({
                        "id": "chat-input-box", 
                        "key": f"chat-input-box-{clear_counter}", 
                        "placeholder": "输入消息，Enter 发送，Shift+Enter 换行...", 
                        "class": "chat-textbox",
                        "on_key_press": handle_keydown
                    })
                ),
                tip and html.div({"class": "alert", "style": {"marginTop": "8px"}}, tip)
            ),
            # right: sidebar
            html.div({"class": "sidebar"},
                progress_card(),
                tools_card(),
                quality_card(),
                video_card(),
                previews_card()
            )
        )
    )


@component
def Navbar(active: str):
    def link(href: str, text: str, key: str):
        cls = "active" if active == key else ""
        return html.a({"href": href, "class": cls}, text)
    return html.div({},
        html.div({"class": "header"},
            html.div({"class": "header-left"},
                html.h1({}, "🎬PIP 小说推文"),
                html.p({}, "从小说到视频，一键生成")
            )
        ),
        html.div({"class": "nav"},
            link("/react?view=agent", "🤖 Agent工作台", "agent"),
            link("/react?view=index", "传统模式", "index"),
            link("/react?view=tasks", "任务管理", "tasks")
        )
    )


@component
def App():
    req = use_request()
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(req.full_path)
    qs = parse_qs(parsed.query)
    view = (qs.get('view') or [''])[0]
    name = (qs.get('name') or [''])[0]
    if not view:
        p = req.path or ''
        if p.startswith('/react/tasks'):
            view = 'tasks'
        elif p.startswith('/react/agent'):
            view = 'agent'
        elif p.startswith('/react/projects'):
            view = 'projects'
        elif p.startswith('/react/project'):
            view = 'project'
        elif p.startswith('/react/edit'):
            view = 'edit'
        else:
            view = 'index'

    page = IndexPage
    if view == 'tasks':
        page = TasksPage
    elif view == 'agent':
        page = AgentWorkspacePage
    elif view == 'project':
        page = ProjectDetailPage
    elif view == 'projects':
        page = ProjectsPage
    elif view == 'edit':
        page = EditPage
    active = {
        'agent': 'agent',
        'index': 'index',
        'tasks': 'tasks',
    }.get(view, 'agent')

    # inline base.html styles for reuse
    base_styles = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft YaHei', sans-serif; background: #0f1419; min-height: 100vh; margin: 0; color: #e8eaed; }
        .container { width: 100%; max-width: 100%; margin: 0; background: #1a1f2e; min-height: 100vh; }
        .header { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 18px 60px; display: flex; justify-content: space-between; align-items: center; }
        .header-left h1 { font-size: 1.6em; margin: 0 0 4px 0; font-weight: 600; }
        .header-left p { margin: 0; opacity: 0.9; font-size: 0.95em; }
        .nav { background: #242938; padding: 0 60px; display: flex; gap: 0; border-bottom: 1px solid #2d3548; }
        .nav a { color: #9ca3af; text-decoration: none; padding: 18px 28px; transition: all 0.3s; font-weight: 500; border-bottom: 3px solid transparent; font-size: 0.95em; }
        .nav a:hover { color: #fff; background: rgba(99, 102, 241, 0.1); }
        .nav a.active { color: #6366f1; border-bottom-color: #6366f1; background: rgba(99, 102, 241, 0.05); }
        .content { padding: 40px 60px; }
        .btn { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; border: none; padding: 10px 18px; border-radius: 8px; cursor: pointer; font-size: 0.92em; font-weight: 600; transition: all 0.25s; box-shadow: 0 3px 10px rgba(99, 102, 241, 0.25); }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(99, 102, 241, 0.32); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .form-group { margin-bottom: 24px; }
        .form-group label { display: block; margin-bottom: 10px; font-weight: 500; color: #e8eaed; font-size: 0.95em; }
        .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 14px 16px; background: #242938; border: 2px solid #2d3548; border-radius: 10px; font-size: 1em; color: #e8eaed; transition: all 0.3s; }
        .form-group input:focus, .form-group textarea:focus, .form-group select:focus { outline: none; border-color: #6366f1; background: #2a3042; }
        .form-group textarea { resize: vertical; min-height: 200px; font-family: inherit; line-height: 1.6; }
        .alert { padding: 16px 20px; border-radius: 10px; margin-bottom: 24px; border-left: 4px solid; }
        .table { width: 100%; border-collapse: collapse; background: #1b2130; border-radius: 10px; overflow: hidden; }
        .table th, .table td { padding: 12px 16px; border-bottom: 1px solid #2d3548; text-align: left; font-size: 0.95em; }
        .table th { background: #202638; color: #cbd5e1; font-weight: 600; }
        .table tr:hover { background: rgba(99, 102, 241, 0.06); }
        .badge { display: inline-block; color: #fff; padding: 4px 10px; border-radius: 999px; font-size: 0.85em; font-weight: 600; }
        .progress { background: #0f172a; border: 1px solid #2d3548; border-radius: 8px; height: 20px; width: 220px; overflow: hidden; }
        .progress-inner { background: linear-gradient(90deg, #22c55e, #16a34a); height: 100%; text-align: center; font-size: 0.85em; color: #e8eaed; line-height: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .card { background: #1b2130; border: 1px solid #2d3548; border-radius: 10px; padding: 16px; }
        .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; }
        /* Agent chat styles */
        .chat-header { display:flex; justify-content: space-between; align-items:center; padding-bottom:8px; border-bottom:1px solid #2d3548; margin-bottom:12px; }
        .chat-list { list-style:none; padding:0; margin:0; max-height: 62vh; overflow:auto; display:flex; flex-direction:column; gap:10px; }
        .chat-bubble-left, .chat-bubble-right { background:#0f172a; border:1px solid #2d3548; padding:10px 12px; border-radius:10px; max-width: 92%; }
        .chat-bubble-left { align-self:flex-start; background:#121827; }
        .chat-bubble-right { align-self:flex-end; background:#1f2937; }
        .chat-meta { font-size: 12px; color:#9ca3af; margin-bottom:4px; }
        .chat-text { white-space: pre-wrap; line-height:1.6; }
        .chat-input { display:flex; gap:8px; margin-top:12px; }
        .chat-textbox { flex:1; padding:12px 14px; background:#242938; border:1px solid #2d3548; border-radius:10px; color:#e8eaed; }
        .sidebar > .card { margin-bottom: 16px; }
        /* 左侧任务栏 */
        .leftbar .task-item { display:flex; align-items:center; justify-content:space-between; padding:8px 10px; border-radius:8px; border:1px solid #2d3548; background:#0f172a; cursor:pointer; transition:all 0.2s; position:relative; }
        .leftbar .task-item.active { border-color:#6366f1; background:#1f2540; box-shadow:0 0 0 1px rgba(99,102,241,0.5) inset; }
        .leftbar .task-item.active::before { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; background:#6366f1; border-radius:8px 0 0 8px; }
        .leftbar .task-list { display:flex; flex-direction:column; gap:8px; max-height: 72vh; overflow:auto; }
        .dot { width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:6px; }
        .dot.pending{ background:#f59e0b; } .dot.running{ background:#3b82f6; } .dot.completed{ background:#22c55e; } .dot.failed{ background:#ef4444; }
        /* 时间线卡片 */
        .tl-step, .tl-tool { background:#0f172a; border:1px dashed #2d3548; padding:8px 10px; border-radius:8px; color:#cbd5e1; font-size:13px; }
        .tl-tool.running{ border-color:#f59e0b; } .tl-tool.done{ border-color:#22c55e; } .tl-tool.error{ border-color:#ef4444; }
        /* 回到底部按钮 */
        .scroll-bottom { position:absolute; right:16px; bottom:86px; background:#2a3042; border:1px solid #2d3548; color:#e5e7eb; border-radius:999px; padding:6px 12px; font-size:12px; display:none; cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.3); }
        .scroll-bottom:hover{ background:#333a52; }
        .table-compact { width: 100%; border-collapse: collapse; font-size: 13px; }
        .table-compact th, .table-compact td { padding: 6px 8px; border-bottom: 1px solid #2d3548; text-align: left; }
        .table-compact th { color: #9ca3af; font-weight: 600; }
        .nowrap { white-space: nowrap; }
        /* 工具状态 徽标色 */
        .badge-running { background:#f59e0b; }
        .badge-done    { background:#16a34a; }
        .badge-error   { background:#dc2626; }
        .badge-idle    { background:#6b7280; }
    """

    sse_script = """
    (function(){
      try {
        const es = new EventSource('/events');
        es.onmessage = function(e){
          try{
            const ev = JSON.parse(e.data);
            if(ev && ev.type === 'task_update' && ev.task){
              const t = ev.task;
              const tid = t.task_id || t.project_name || '';
              // Tasks table updates
              const statusEl = document.getElementById('status-' + tid);
              if(statusEl){ statusEl.textContent = t.status || ''; }
              const progEl = document.getElementById('prog-' + tid);
              if(progEl && t.progress != null){ progEl.style.width = (parseInt(t.progress)||0)+'%'; progEl.textContent = (parseInt(t.progress)||0)+'%'; }
              const stepEl = document.getElementById('step-' + tid);
              if(stepEl && t.current_step){ stepEl.textContent = t.current_step; }
              // Agent page widgets
              const ap = document.getElementById('agent-prog');
              if(ap && ap.dataset && (ap.dataset.project||'') === (t.project_name||'')){
                ap.style.width = (parseInt(t.progress)||0)+'%'; ap.textContent = (parseInt(t.progress)||0)+'%';
                const as = document.getElementById('agent-step'); if(as){ as.textContent = t.current_step || ''; }
                // 时间线：步骤变化插入卡片
                const list = document.getElementById('agent-messages');
                if(list && list.dataset && list.dataset.task === tid){
                  if(t.current_step && list.dataset.lastStep !== t.current_step){
                    const li = document.createElement('li');
                    li.className = 'tl-step';
                    const ts = new Date().toLocaleTimeString();
                    li.textContent = '📌 步骤更新：' + t.current_step + ' · ' + ts;
                    list.appendChild(li);
                    list.dataset.lastStep = t.current_step;
                    try{ list.scrollTop = list.scrollHeight; }catch(_){}
                  }
                }
              const aStep = document.getElementById('agent-step');
              if(aStep && aStep.dataset.project === (t.project_name||'')){
                 aStep.textContent = t.current_step || '';
              }
              // Project detail video smooth reload
              const v = document.getElementById('project-video');
              if(v && v.dataset.project === (t.project_name||'')){
                 try{
                   const t0 = v.currentTime || 0; const wasPaused = v.paused;
                   const src = v.getAttribute('data-src-base') || v.currentSrc || v.src;
                   const base = src.split('?')[0];
                   const newSrc = base + '?v=' + Date.now();
                   v.src = newSrc; v.setAttribute('data-src-base', base);
                   v.onloadedmetadata = function(){ try{ v.currentTime = t0; if(!wasPaused) v.play(); }catch(_){} };
                 }catch(_){}
              }
            }
            // 为避免与轮询渲染重复，这里默认不通过SSE追加agent_message。
            // 若需要开启，将#agent-messages设置 data-sse="on" 即可。
            if(ev && ev.type === 'agent_message'){
              const list = document.getElementById('agent-messages');
              if(!(list && list.dataset && list.dataset.sse === 'on')){ return; }
              if(list && list.dataset.task && ev.task_id === list.dataset.task){
                 const li = document.createElement('li');
                 const role = ev.role || 'user';
                 li.className = role === 'assistant' ? 'chat-bubble-left' : 'chat-bubble-right';
                 const meta = document.createElement('div');
                 meta.className = 'chat-meta';
                 const ts = ev.timestamp ? new Date(ev.timestamp * 1000).toLocaleTimeString() : '';
                 meta.textContent = (role || '') + (ts? ' · ' + ts : '');
                 const text = document.createElement('div');
                 text.className = 'chat-text';
                 text.textContent = ev.message || '';
                 li.appendChild(meta);
                 li.appendChild(text);
                 list.appendChild(li);
                 try{ list.scrollTop = list.scrollHeight; }catch(_){}
              }
            }
            if(ev && ev.type === 'tool_update'){
              const list = document.getElementById('agent-messages');
              const taskId = ev.task_id;
              // 仅当当前聊天所选任务一致时才更新侧栏
              if(list && list.dataset && list.dataset.task === taskId){
                 const name = ev.tool; const info = ev.info || {};
                 const statusEl = document.getElementById(`tool-${name}-status`);
                 const retryEl = document.getElementById(`tool-${name}-retries`);
                 const timeEl = document.getElementById(`tool-${name}-time`);
                 if(statusEl){
                    const s = (info.status||'idle');
                    statusEl.textContent = statusTextCN(s);
                    statusEl.className = `badge ${statusClass(s)}`;
                 }
                 if(retryEl){ retryEl.textContent = String(info.retries||0); }
                 if(timeEl){ timeEl.textContent = fmtTime(info.last_update||''); }
                 // 时间线：工具事件
                 const li = document.createElement('li');
                 const s = (info.status||'idle');
                 li.className = `tl-tool ${s}`;
                 const cname = toolNameCN(name);
                 const ts = fmtTime(info.last_update||'');
                 li.textContent = `🛠️ 工具：${cname} → ${statusTextCN(s)} ${ts?('· '+ts):''}`;
                 list.appendChild(li);
                 try{ list.scrollTop = list.scrollHeight; }catch(_){}
              }
            }
          }catch(err){ console.warn('SSE parse error', err); }
        };
        es.onerror = function(){ /* silently ignore to keep connection */ };
        // 滚动到底部提示逻辑
        try{
          const list = document.getElementById('agent-messages');
          const btn = document.getElementById('scroll-to-bottom');
          if(list && btn){
            const nearBottom = () => (list.scrollHeight - list.scrollTop - list.clientHeight) < 40;
            const updateBtn = () => { btn.style.display = nearBottom()? 'none':'inline-block'; };
            list.addEventListener('scroll', updateBtn);
            updateBtn();
            btn.addEventListener('click', () => { try{ list.scrollTop = list.scrollHeight; updateBtn(); }catch(_){} });
          }
        }catch(_){}
        
        function statusClass(s){
          switch(s){
            case 'running': return 'badge-running';
            case 'done': return 'badge-done';
            case 'error': return 'badge-error';
            default: return 'badge-idle';
          }
        }
        function statusTextCN(s){
          switch(s){
            case 'running': return '执行中';
            case 'done': return '已完成';
            case 'error': return '出错';
            case 'idle': default: return '待机';
          }
        }
        function toolNameCN(k){
          switch(k){
            case 'generate_audio': return '生成音频';
            case 'generate_prompts': return '生成提示词';
            case 'generate_images': return '生成图像';
            case 'generate_video': return '合成视频';
            default: return k;
          }
        }
        function pad(n){ return n<10?('0'+n):(''+n); }
        function fmtTime(s){
          if(!s) return '';
          try{
            const d = new Date(s);
            if(isNaN(d.getTime())) return s;
            return d.getFullYear()+ '-' + pad(d.getMonth()+1) + '-' + pad(d.getDate()) + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
          }catch(_){ return s; }
        }
      } catch(err){ console.warn('SSE init error', err); }
    })();
    """

    return html.div({"class": "container"},
        html.style({}, base_styles),
        Navbar(active),
        page(),
        html.script({}, sse_script)
    )


@component
def ProjectDetailPage():
    req = use_request()
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(req.full_path)
    qs = parse_qs(parsed.query)
    project_name = (qs.get('name') or [''])[0]
    data, set_data = hooks.use_state({})
    edit_scene, set_edit_scene = hooks.use_state(None)  # 当前编辑的场景
    edit_prompt, set_edit_prompt = hooks.use_state("")  # 编辑中的提示词

    @hooks.use_effect
    async def _load():
        try:
            content = await api_get_json(req, f"/api/project_content/{project_name}")
            set_data(content or {})
        except Exception:
            set_data({})
        return

    async def on_refresh(event):
        print(f"[前端] 用户点击：刷新项目详情 - project_name: {project_name}")
        try:
            content = await api_get_json(req, f"/api/project_content/{project_name}")
            set_data(content or {})
            print(f"[前端] 项目详情刷新完成 - project_name: {project_name}")
        except Exception as e:
            print(f"[前端] 项目详情刷新失败: {str(e)}")

    async def on_regen_all(event):
        print(f"[前端] 用户点击：重新生成全部图像 - project_name: {project_name}")
        try:
            await api_post_json(req, f"/api/regenerate_images/{project_name}", {})
            print(f"[前端] 全部图像重新生成完成 - project_name: {project_name}")
            await on_refresh(event)
        except Exception as e:
            print(f"[前端] 全部图像重新生成失败: {str(e)}")

    def on_edit_click(idx: int):
        """点击编辑按钮"""
        # 从prompts中找到对应的提示词
        prompts = data.get('prompts', [])
        if idx > 0 and idx <= len(prompts):
            prompt = prompts[idx - 1]  # index从1开始，数组从0开始
            set_edit_scene(idx)
            set_edit_prompt(prompt)
            print(f"[前端] 打开编辑对话框 - scene: {idx}, prompt: {prompt[:50]}...")
    
    async def on_save_prompt(event):
        """保存编辑的提示词"""
        if edit_scene is None:
            return
        print(f"[前端] 保存提示词 - scene: {edit_scene}")
        try:
            # 调用API保存提示词
            await api_post_json(req, f"/api/update_prompt/{project_name}/{edit_scene}", {
                "prompt": edit_prompt
            })
            print(f"[前端] 提示词保存成功")
            # 关闭对话框
            set_edit_scene(None)
            set_edit_prompt("")
            # 刷新数据
            await on_refresh(event)
        except Exception as e:
            print(f"[前端] 提示词保存失败: {str(e)}")
    
    def on_cancel_edit(event):
        """取消编辑"""
        set_edit_scene(None)
        set_edit_prompt("")
    
    def create_regen_handler(idx: int):
        """创建重新生成处理器"""
        async def handler(event):
            print(f"[前端] 用户点击：重新生成单张图片 - scene: {idx}")
            try:
                await api_post_json(req, f"/api/regenerate_single_image/{project_name}/{idx}", {})
                print(f"[前端] 单张图片重新生成任务已提交 - scene: {idx}")
                print(f"💡 提示：图片正在后台生成，请稍后手动刷新查看")
            except Exception as e:
                print(f"[前端] 单张图片重新生成失败: {str(e)}")
        return handler

    def images_grid(items):
        """图片网格 - 缩略图模式"""
        cards = []
        for img in (items or []):
            idx = int(img.get('index',0))
            # 缩略图卡片
            cards.append(
                html.div({
                    "class": "card",
                    "style": {
                        "padding": "12px",
                        "display": "flex",
                        "flexDirection": "column",
                        "gap": "8px"
                    }
                },
                    # 场景编号
                    html.div({"style": {"fontSize": "13px", "color": "#9ca3af", "fontWeight": "600"}}, 
                        f"scene_{img.get('index',0):04d}"
                    ),
                    # 缩略图（点击查看大图）
                    html.a({
                        "href": f"/static/{img.get('path','')}",
                        "target": "_blank",
                        "style": {"display": "block", "position": "relative", "overflow": "hidden", "borderRadius": "6px", "background": "#0f172a"}
                    },
                        html.img({
                            "src": f"/static/{img.get('path','')}",
                            "style": {
                                "width": "100%",
                                "height": "160px",
                                "objectFit": "cover",
                                "display": "block",
                                "cursor": "pointer",
                                "transition": "transform 0.2s"
                            },
                            "onmouseover": "this.style.transform='scale(1.05)'",
                            "onmouseout": "this.style.transform='scale(1)'"
                        })
                    ),
                    # 操作按钮
                    html.div({"style": {"display": "flex", "gap": "6px"}},
                        html.button({
                            "class": "btn",
                            "type": "button",
                            "on_click": lambda e, i=idx: on_edit_click(i),
                            "style": {
                                "flex": "1",
                                "padding": "6px 10px",
                                "fontSize": "12px",
                                "background": "#5865f2",
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer"
                            }
                        }, "编辑"),
                        html.button({
                            "class": "btn",
                            "type": "button",
                            "on_click": create_regen_handler(idx),
                            "style": {
                                "flex": "1",
                                "padding": "6px 10px",
                                "fontSize": "12px",
                                "background": "#3ba55d",
                                "color": "#fff",
                                "border": "none",
                                "borderRadius": "4px",
                                "cursor": "pointer"
                            }
                        }, "重新生成")
                    )
                )
            )
        # 使用更紧凑的网格布局
        return html.div({
            "style": {
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))",
                "gap": "16px",
                "marginTop": "16px"
            }
        }, cards)

    # video src with cache-busting
    vid_src = None
    if data.get('video'):
        vid_src = f"/api/video/{project_name}?v=0"

    return html.div({"class": "content"},
        html.h2({}, f"项目：{project_name}"),
        html.div({"style": {"display": "flex", "gap": "8px", "margin": "8px 0 16px"}},
            html.a({"href": f"/react?view=edit&name={project_name}", "class": "btn"}, "编辑提示词"),
            html.button({"class": "btn", "type": "button", "on_click": on_regen_all}, "重新生成全部图像"),
            html.button({"class": "btn", "type": "button", "on_click": on_refresh}, "刷新")
        ),
        vid_src and html.div({"class": "card"},
            html.h3({}, "视频预览"),
            html.video({
                "id": "project-video",
                "data-project": project_name,
                "data-src-base": f"/api/video/{project_name}",
                "src": vid_src,
                "controls": True,
                "style": {"maxWidth": "500px", "width": "100%", "borderRadius": "8px", "display": "block"}
            })
        ) or None,
        (data.get('images') and html.div({},
            html.h3({}, "分镜图像"),
            images_grid(data.get('images'))
        )) or None,
        # 编辑对话框
        edit_scene is not None and html.div({
            "style": {
                "position": "fixed",
                "top": "0",
                "left": "0",
                "right": "0",
                "bottom": "0",
                "background": "rgba(0,0,0,0.7)",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "zIndex": "1000"
            }
        },
            html.div({
                "class": "card",
                "style": {
                    "width": "90%",
                    "maxWidth": "700px",
                    "maxHeight": "80vh",
                    "overflow": "auto",
                    "padding": "24px"
                }
            },
                html.h3({}, f"编辑场景 {edit_scene} 的提示词"),
                html.div({
                    "style": {
                        "padding": "10px",
                        "background": "#1e293b",
                        "borderRadius": "6px",
                        "fontSize": "13px",
                        "color": "#94a3b8",
                        "marginTop": "8px"
                    }
                }, "💡 提示：保存后需要点击\"重新生成全部图像\"按钮来应用更改"),
                html.textarea({
                    "value": edit_prompt,
                    "on_change": lambda e: set_edit_prompt(e["target"]["value"]),
                    "style": {
                        "width": "100%",
                        "minHeight": "200px",
                        "padding": "12px",
                        "fontSize": "14px",
                        "fontFamily": "monospace",
                        "background": "#0f172a",
                        "color": "#e8eaed",
                        "border": "1px solid #2d3548",
                        "borderRadius": "6px",
                        "resize": "vertical",
                        "marginTop": "12px"
                    }
                }),
                html.div({
                    "style": {
                        "display": "flex",
                        "gap": "12px",
                        "marginTop": "20px",
                        "justifyContent": "flex-end"
                    }
                },
                    html.button({
                        "class": "btn",
                        "type": "button",
                        "on_click": on_cancel_edit,
                        "style": {
                            "background": "#4e5058",
                            "padding": "10px 20px"
                        }
                    }, "取消"),
                    html.button({
                        "class": "btn",
                        "type": "button",
                        "on_click": on_save_prompt,
                        "style": {
                            "background": "#3ba55d",
                            "padding": "10px 20px"
                        }
                    }, "保存")
                )
            )
        ) or None
    )


@component
def ProjectsPage():
    req = use_request()
    rows, set_rows = hooks.use_state([])

    @hooks.use_effect
    async def _load():
        try:
            data = await api_get_json(req, "/api/tasks")
            set_rows(data)
        except Exception:
            set_rows([])
        return

    def row_view(t: dict):
        pname = t.get('project_name','')
        return html.tr({},
            html.td({}, html.a({"href": f"/react?view=project&name={pname}"}, pname)),
            html.td({}, t.get('status','')),
            html.td({}, t.get('progress',0)),
            html.td({}, html.a({"href": f"/react?view=edit&name={pname}", "class": "btn"}, "编辑"))
        )

    return html.div({"class": "content"},
        html.h2({}, "项目列表 (ReactPy)"),
        html.table({"class": "table"},
            html.thead({}, html.tr({}, html.th({}, "项目名"), html.th({}, "状态"), html.th({}, "进度"), html.th({}, "操作"))),
            html.tbody({}, [row_view(t) for t in rows])
        )
    )


@component
def EditPage():
    req = use_request()
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(req.full_path)
    qs = parse_qs(parsed.query)
    project_name = (qs.get('name') or [''])[0]
    text, set_text = hooks.use_state("")
    tip, set_tip = hooks.use_state("")

    @hooks.use_effect
    async def _load():
        try:
            data = await api_get_json(req, f"/api/prompts/{project_name}")
            set_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            set_text(json.dumps({"scene_prompts": []}, ensure_ascii=False, indent=2))
        return

    async def on_save(event):
        print(f"[前端] 用户点击：保存提示词 - project_name: {project_name}")
        try:
            payload = json.loads(text)
            await api_post_json(req, f"/api/prompts/{project_name}", payload)
            print(f"[前端] 提示词保存成功 - project_name: {project_name}")
            set_tip("✓ 已保存")
        except Exception as e:
            print(f"[前端] 提示词保存失败: {str(e)}")
            set_tip(f"❌ {str(e)}")

    return html.div({"class": "content"},
        html.h2({}, f"编辑提示词：{project_name}"),
        tip and html.div({"class": "alert"}, tip) or None,
        html.div({},
            html.textarea({"class": "mono", "style": {"minHeight": "420px", "width": "100%"}, "value": text, "on_input": lambda e: set_text(e["target"]["value"])},),
            html.div({"style": {"marginTop": "12px"}}, html.button({"class": "btn", "type": "button", "on_click": on_save}, "保存"))
        )
    )
