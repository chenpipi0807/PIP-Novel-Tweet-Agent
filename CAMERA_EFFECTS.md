# 视频运镜效果说明

## 支持的运镜效果（Ken Burns）

系统会为每个分镜随机选择以下运镜效果之一：

### 1. 缩放效果

- **zoom_in** (放大)
  - 从1.0倍缓慢放大到1.2倍
  - 适合：强调重点、营造紧张感

- **zoom_out** (缩小)
  - 从1.2倍缓慢缩小到1.0倍
  - 适合：展现全景、舒缓节奏

### 2. 平移效果

- **pan_right** (右移)
  - 从左向右平移
  - 适合：展现场景、引导视线

- **pan_left** (左移)
  - 从右向左平移
  - 适合：回溯、反向叙事

- **pan_up** (上移)
  - 从下向上平移
  - 适合：仰视、升华情绪

- **pan_down** (下移)
  - 从上向下平移
  - 适合：俯视、压抑氛围

### 3. 组合效果

- **zoom_in_up** (放大+上移)
  - 放大同时向上移动
  - 适合：英雄登场、情绪高涨

- **zoom_out_down** (缩小+下移)
  - 缩小同时向下移动
  - 适合：失落、沉重情绪

## 字幕效果

- **位置**: 底部居中
- **字体**: 微软雅黑 40号
- **颜色**: 白色文字
- **描边**: 3像素黑色描边
- **边距**: 距离底部50像素

## 技术实现

使用ffmpeg的`zoompan`和`drawtext`滤镜：

```bash
# zoompan: Ken Burns运镜
zoompan=z='min(zoom+0.0015,1.2)':x='...':y='...':d=frames:s=1024x1024:fps=24

# drawtext: 字幕
drawtext=text='字幕内容':fontfile='msyh.ttc':fontsize=40:fontcolor=white:borderw=3
```

## 参考案例

抖音小说推文常见运镜：
1. 对话场景：缓慢放大（zoom_in）
2. 环境描述：左右平移（pan_left/right）
3. 情绪转折：放大+上移（zoom_in_up）
4. 悬念铺垫：缓慢缩小（zoom_out）

## 自定义运镜

修改 `tools/video_composer_enhanced.py` 中的 `CAMERA_EFFECTS` 列表即可添加新效果。

参数说明：
- `scale_start/end`: 起始/结束缩放比例
- `x_start/end`: 起始/结束X轴偏移（像素）
- `y_start/end`: 起始/结束Y轴偏移（像素）
