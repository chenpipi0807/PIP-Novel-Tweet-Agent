import sys

print("检查WeTextProcessing...")
try:
    import WeTextProcessing
    print(f"✓ WeTextProcessing已安装: {WeTextProcessing.__file__}")
except ImportError as e:
    print(f"✗ WeTextProcessing未安装: {e}")

print("\n检查wetext...")
try:
    import wetext
    print(f"✓ wetext已安装: {wetext.__file__}")
except ImportError as e:
    print(f"✗ wetext未安装: {e}")

print("\n检查WeTextProcessing内容...")
try:
    import WeTextProcessing
    print(f"WeTextProcessing模块内容: {dir(WeTextProcessing)}")
except:
    pass
