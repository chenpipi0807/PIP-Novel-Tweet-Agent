"""
启动Web服务
"""
import sys
from pathlib import Path

# 检查依赖
try:
    import flask
except ImportError:
    print("❌ Flask未安装")
    print("请运行: pip install flask")
    sys.exit(1)

# 检查ffmpeg
from tools.check_ffmpeg import check_ffmpeg
if not check_ffmpeg():
    print("\n⚠ ffmpeg未安装，视频合成功能将无法使用")
    print("运行以下命令安装: python tools/install_ffmpeg.py")
    print("\n是否继续启动Web服务? (y/n): ", end='')
    
    choice = input().strip().lower()
    if choice != 'y':
        sys.exit(0)

print("\n" + "=" * 70)
print("启动短剧AI生成系统 Web服务")
print("=" * 70)
print("\n访问地址: http://localhost:5000")
print("按 Ctrl+C 停止服务\n")

# 启动Flask应用
import threading, sys, asyncio

def _thread_excepthook(args):
    # 忽略 ReactPy/AnyIO 在连接关闭时抛出的 CancelledError 噪声
    if isinstance(args.exc_value, asyncio.CancelledError):
        return
    # 其它异常仍按默认方式输出
    sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)

threading.excepthook = _thread_excepthook

from app import app
# 生产模式运行，关闭 debug 与自动重载
app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False, threaded=True)
