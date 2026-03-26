# Sprite Sheet Specification

## Grid Layout

- **13 rows × 8 columns**
- **Frame size**: 276×274 px (or square, consistent)
- **Background**: Pure magenta #FF00FF
- **Total image**: ~2208 × 3562 px (at 276×274 per frame)
- **Output resolution**: 4K+ recommended for quality

## Row Definitions

| Row | State | Description | Loop? | Trigger |
|-----|-------|-------------|-------|---------|
| 0 | idle | Sitting relaxed, slight breathing, occasional blink | Yes | Default state |
| 1 | walking | Walking forward, full body visible | Yes | Moving on screen |
| 2 | looking_around | Head turning left/right, alert ears, curious | Yes | Taking screenshot / observing |
| 3 | sleeping | Curled up, eyes closed, zzz | Yes | Idle > 5min or late night |
| 4 | exercising | Stretching, jumping, moving actively | No | Health reminder |
| 5 | working | At keyboard/laptop, focused | Yes | When owner is working |
| 6 | playful | Playing with toy/yarn, batting paw | No | Fun interaction |
| 7 | happy | Bright eyes, tail up, content expression | No | Positive interaction |
| 8 | celebrate | Jumping with joy, confetti/sparkles | No | Achievement / milestone |
| 9 | sad | Droopy ears, looking down, subdued | Yes | Low hearts / ignored |
| 10 | sick | Lying flat, tired eyes, unwell | Yes | Hearts = 0 |
| 11 | panic | Wide eyes, fur standing, startled | No | Mouse moves quickly |
| 12 | dragging | Being held/carried, dangling | Yes | Being dragged by user |

## Generation Prompt

Copy and customize this prompt for AI image generation:

```
请生成一张精灵图（sprite sheet）

硬性要求：
- PNG 或 JPG 均可（推荐 PNG 以减少压缩噪点）
- 背景色必须是且只能是纯品红（magenta）#ff00ff：不要渐变/阴影/纹理/噪点/压缩噪点；不要出现第二种背景色像素；应用会自动把背景抠成透明
- 角色不要自带任何"背景/场景/地面/墙面/光斑/烟雾"等元素；除角色本身外，所有区域必须是纯品红背景（#ff00ff）
- 请避免在角色/道具/阴影中使用背景色（#ff00ff 或非常接近的品红色），否则会被一起抠掉
- 角色表面不要出现品红色反光/品红色轮廓光/品红色光晕（避免被误抠）
- 分成 8 列 × 13 行的网格，每一格必须是正方形帧（每帧宽高相等！）
- 每一帧与相邻帧必须紧挨着：不要留白/间隔/内边距/外边距；不要画网格线或分隔线（不要有任何缝隙！）
- 整体长宽比约为 8:13（≈0.615）
- 推荐输出 4K 级别的高分辨率图片（如 4096×6656，每帧 512×512），程序会等比例缩放到最终尺寸 1024×1664（每帧 128×128）
- 请确保图像质量高：角色细节清晰、边缘锐利、无模糊/锯齿/压缩伪影
- 同一行表示同一个动画；从左到右是连续帧，循环播放
- Idle（第1行）需要有呼吸和眨眼的动作，不要画成完全静止不动的帧
- Sleeping（第4行）只画闭眼呼吸的帧，不要画打哈欠的帧（因为循环播放时不停打哈欠会很突兀）
- 同一个动画（同一行）相邻两帧之间的变化必须非常连贯：不要跳帧、不要突然大幅位移/大幅姿态变化/大幅表情变化、不要突然变焦或改变视角
- 角色在每一帧中的位置尽量一致（建议以画布中心对齐），不要裁切到边缘

行含义（从上到下）：
- 第1行：Idle — 坐着放松，轻微呼吸起伏，偶尔眨眼
- 第2行：Walking — 走路，四肢交替迈步
- 第3行：Looking Around — 坐着左右张望，耳朵竖起，好奇表情
- 第4行：Sleeping — 蜷缩成团，闭眼，轻微呼吸，可以有小 zzz
- 第5行：Exercising — 伸懒腰、轻跳、活跃的肢体动作
- 第6行：Working — 坐在小键盘/笔记本前，专注表情
- 第7行：Playful — 拨弄毛线球/玩具，俏皮的爪子动作（当主人在看视频/玩游戏等放松时触发）
- 第8行：Happy — 眼睛明亮，尾巴翘起，开心表情，可以有小爱心
- 第9行：Celebrate — 开心跳跃，周围有小星星/彩花
- 第10行：Sad — 耳朵耷拉，低头，神情低落
- 第11行：Sick — 侧躺，半闭眼，虚弱无力的样子
- 第12行：Panic — 瞪大眼睛，毛炸起来，受惊表情
- 第13行：Dragging — 被拎着后颈皮提起来，四肢悬空，略带不满表情

角色设定：[在这里填你的角色描述，比如：狸花猫，参考我的照片]
风格：可爱、干净、有真实照片的感觉，统一光照与配色，背景保持纯品红色（方便抠图）
输出：只输出这张 sprite sheet（png/jpg）
```

## After Generation

Process the sprite sheet with:
```bash
python3 scripts/process-spritesheet.py input.png public/sprites/[name].png --cols 8 --frame-size 128
```

Then update `src/sprite.js` STATES to match the new rows.
