# 老游戏开源重制版「提高渲染分辨率后 UI 不变形」机制调研

调研对象：OpenRA、DevilutionX、OpenXcom、ja2-stracciatella、ScummVM、BuildGDX/NuBuildGDX、DXX-Rebirth、EDuke32，以及 Panzer General 系列相关的 pg-cht（A1 hires canvas）项目。

**方法说明**：本项目为纯 Web 调研、**未修改任何文件**。所有代码结论均来自实际抓取到的源码/文档；本次把 4 个仓库（OpenRA@bleed、devilutionX@master、OpenXcom@master、ja2-stracciatella@master）下载到本地快照后逐行核对，因此行号与代码均为实测。**抓取失败的页面已在该节明确标注**（DXX-Rebirth 的 `gr.h` 超时、EDuke32 官方仓库不在 GitHub、Open General/PG Forever 无公开源码）。

---

## 0. 一句话结论

这些项目**没有一个是靠"把 UI 一起拉伸"来解决的**。主流做法是三条正交的机制：

1. **UI 尺寸常量完全不动**（图集原始像素、面板固定 `Size{640,128}`、按钮固定宽高）；
2. 把「位置」抽出来，变成**屏幕尺寸的算术函数**（锚点表达式 / 标准窗口偏移 / 面板原点）；
3. 缩放只发生在「输出/合成」层，且必须是**整数倍 + 黑边**，或者干脆不缩放只居中（letterbox / pillarbox）。

| 项目 | 位置数据变成什么 | 尺寸怎么保持 | 缩放因子怎么定 | 像素精确怎么保 |
|---|---|---|---|---|
| OpenRA | YAML 里的**算术表达式**（`WINDOW_WIDTH/PARENT_WIDTH - WIDTH - k`） | 宽高是像素常量 | `graphicSettings.UIScale`（默认 1） | `Image2x`/`Image3x` 多倍素材 |
| DevilutionX | **面板原点 + 面板内相对坐标** | `MainPanelSize{640,128}` 常量 | `zoomFactor` 整数倍 | 整数倍最近邻 |
| OpenXcom | **标准窗口偏移 `getDX()/getDY()`** 全局 pass | `ORIGINAL_WIDTH/HEIGHT` 常量 | `SCALE_15X/2X/SCREEN_DIV_3` | 8bpp 原图，non-square 用 `pixelRatioY=1.2` |
| ja2 | **`UILayout` 集中重算 + `STD_SCREEN_X/Y`** | `TEAMPANEL_SLOT_WIDTH` 等常量 | SDL_Renderer `ScalingQuality` + Rust | 整数放大 |
| ScummVM | 不重排 UI，整体缩放并 letterbox | 不动 | Pixel-perfect / Even-pixels 整数倍 | 整数倍；OpenGL 路径可避免软件 scaler 的模糊 |

**没有任何一个项目在代码注释或文档里提出"把固定像素 UI 拉伸填满宽屏"**；唯一的"拉伸"选项（ScummVM 的 *Stretch to window*）是明确标注为不保比例的用户可选最差选项。

---

## 1. OpenRA（C#）

仓库：<https://github.com/OpenRA/OpenRA>（分支 `bleed`）

### 机制：UI 位置 = YAML 里的算术表达式，不是常量

`OpenRA.Game/Widgets/Widget.cs:292-320` 的 `Widget.Initialize(WidgetArgs args)` 是全部布局的总入口：

```csharp
public virtual void Initialize(WidgetArgs args)
{
    // Parse the YAML equations to find the widget bounds
    var parentBounds = (Parent == null)
        ? new WidgetBounds(0, 0, Game.Renderer.Resolution.Width, Game.Renderer.Resolution.Height)
        : Parent.Bounds;

    var substitutions = ...;
    substitutions.Add("WINDOW_WIDTH",  Game.Renderer.Resolution.Width);
    substitutions.Add("WINDOW_HEIGHT", Game.Renderer.Resolution.Height);
    substitutions.Add("PARENT_WIDTH",  parentBounds.Width);
    substitutions.Add("PARENT_HEIGHT", parentBounds.Height);

    var width  = Width?.Evaluate(readOnlySubstitutions)  ?? 0;
    var height = Height?.Evaluate(readOnlySubstitutions) ?? 0;
    substitutions.Add("WIDTH",  width);
    substitutions.Add("HEIGHT", height);

    var x = X?.Evaluate(readOnlySubstitutions) ?? 0;
    var y = Y?.Evaluate(readOnlySubstitutions) ?? 0;
    Bounds = new WidgetBounds(x, y, width, height);
}
```

链接：<https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Widgets/Widget.cs#L292-L320>

要点：
- 每个 widget 的 `X/Y/Width/Height` 是 `IntegerExpression`（可含变量与四则运算），**不是数字**。
- 变量注入顺序很讲究：先 `WINDOW_*` / `PARENT_*` → 求宽度高度 → 再把 `WIDTH` / `HEIGHT` 注入 → 才求 `X` / `Y`。**所以 `X` 可以直接写 `PARENT_WIDTH - WIDTH - 20`，即"锚在父容器右边缘、留 20px 间距"。**
- 根容器没有父级时，用**渲染分辨率**当 parent bounds，即 `Game.Renderer.Resolution` = `Window.EffectiveWindowSize`（`OpenRA.Game/Renderer.cs:387`、`OpenRA.Game/Graphics/PlatformInterfaces.cs:55`）。

### 锚定规则写在数据文件里（真例子，行号实测）

`mods/cnc/chrome/*.yaml` 里到处都是：

```
mods/cnc/chrome/assetbrowser.yaml:3:    X: (WINDOW_WIDTH - WIDTH) / 2        ← 水平居中
mods/cnc/chrome/assetbrowser.yaml:4:    Y: (WINDOW_HEIGHT - HEIGHT) / 2      ← 垂直居中
mods/cnc/chrome/assetbrowser.yaml:108:  X: PARENT_WIDTH - WIDTH - 15         ← 贴父级右边缘
mods/cnc/chrome/assetbrowser.yaml:215:  X: PARENT_WIDTH - WIDTH + 5
mods/cnc/chrome/connection.yaml:3:      X: (WINDOW_WIDTH - WIDTH) / 2
mods/cnc/chrome/connection.yaml:22:     Y: (PARENT_HEIGHT - HEIGHT) / 2
mods/cnc/chrome/dialogs.yaml:           X: WINDOW_WIDTH - WIDTH - 245        ← 贴屏幕右边缘(dialog)
mods/cnc/chrome/ingame.yaml:            Y: WINDOW_HEIGHT - HEIGHT - 5        ← 贴屏幕下边缘
```

链接：
- <https://github.com/OpenRA/OpenRA/blob/bleed/mods/cnc/chrome/assetbrowser.yaml>
- <https://github.com/OpenRA/OpenRA/blob/bleed/mods/cnc/chrome/connection.yaml>
- <https://github.com/OpenRA/OpenRA/blob/bleed/mods/cnc/chrome/dialogs.yaml>
- <https://github.com/OpenRA/OpenRA/blob/bleed/mods/cnc/chrome/ingame.yaml>

**这就是用户要的"贴四边 + 居中"的现成表达法**，而且因为是表达式，在原始分辨率下天然退化回原值（幂等）。

### 图集保持像素精确：按 dpiScale 选 @2x/@3x 素材

`OpenRA.Game/Graphics/ChromeProvider.cs`：

```
:65   static float dpiScale = 1;
:73   dpiScale = Game.Renderer.WindowScale;
:117  if (dpiScale > 2 && !string.IsNullOrEmpty(c.Image3x))
:122  else if (dpiScale > 1 && !string.IsNullOrEmpty(c.Image2x))
:287  public static void SetDPIScale(float scale)
```

链接：<https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Graphics/ChromeProvider.cs#L110-L125>

即：**要放大 UI 时不是拉伸位图，而是换更高分辨率的同名素材（web 的 `@2x` 思路）**。

### UI 缩放的显式开关

`OpenRA.Game/Renderer.cs:124` `public void SetUIScale(float scale)`，`:151` 调 `ChromeProvider.SetDPIScale(newEffective)`；世界坐标换算在 `OpenRA.Game/Graphics/Viewport.cs:331-337` 用 `graphicSettings.UIScale / Zoom`。默认 `UIScale = 1` → UI 就是原始像素。

链接：<https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Renderer.cs#L124> · <https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Graphics/Viewport.cs#L325-L340>

### 地图拿剩余空间
`Viewport` 用整个渲染分辨率当世界视口（`OverrideDefaultHeight` 只是改 `defaultScale`：`Viewport.cs:95-97`）。**"地图吃掉多出来的像素"在 OpenRA 里是默认行为，不需要额外处理。**

---

## 2. DevilutionX（C++）

仓库：<https://github.com/diasurgical/devilutionX>

### 核心文件
`Source/control/control_panel.cpp`（`CalculatePanelAreas()` 在 241-279）、`Source/control/control.hpp`、`Source/utils/display.cpp`。

### 面板定位算法（实测原文）

```cpp
// Source/control/control_panel.cpp
243:  constexpr Size MainPanelSize { 640, 128 };          // ← UI 尺寸写死为常量
245:  MainPanel = {
246:      { (gnScreenWidth - MainPanelSize.width) / 2,     // ← 水平居中
247:        gnScreenHeight - MainPanelSize.height },       // ← 贴下边缘
248:      MainPanelSize
249:  };
261:  if (gnScreenWidth - LeftPanel.size.width - RightPanel.size.width > MainPanel.size.width) {
262:      LeftPanel.position.x = (gnScreenWidth - LeftPanel.size.width - RightPanel.size.width
                              - MainPanel.size.width) / 2;
265:  LeftPanel.position.y = (gnScreenHeight - LeftPanel.size.height - MainPanel.size.height) / 2;
275:  if (gnScreenWidth <= MainPanel.size.width) {
277:      gnViewportHeight -= MainPanel.size.height;       // ← 只在屏幕不够宽时才让底栏吃掉视口高度
278:  }
```

链接：<https://github.com/diasurgical/devilutionX/blob/master/Source/control/control_panel.cpp#L241-L279>

**这是"贴底边 + 居中 + 宽屏时视口恢复满高"三件事一次做完的教科书实现。** 注意 277 行的条件：宽屏时底栏**不再**扣掉视口高度 → 就是用户要的"地图拿到多出来的面积"。

### 面板相对坐标：原版硬编码坐标一个都不用改

`Point GetPanelPosition(UiPanels panel, Point offset = {0,0})`（声明 `Source/control/control.hpp:94`，实现 `control_panel.cpp:332-347` 返回 `GetMainPanel().position + displacement`）。所有绘制都写成：

```cpp
// control_panel.cpp:447
const Point position = mainPanelPosition + Displacement { MainPanelButtonRect[i].position.x,
                                                          MainPanelButtonRect[i].position.y };
// control_panel.cpp:1739
ClxDraw(out, GetPanelPosition(UiPanels::Stash, { 24 + SidePanelSize.width, 327 }), (*pSTextBoxCels)[0]);
```

链接：<https://github.com/diasurgical/devilutionX/blob/master/Source/control/control.hpp#L94> · <https://github.com/diasurgical/devilutionX/blob/master/Source/control/control_panel.cpp#L330-L350>

**所有原版 `{24,327}` 这种硬编码坐标原封不动，只改面板原点。**

### 输出缩放：整数倍 + 逻辑↔物理换算
```cpp
// Source/utils/display.cpp:950
rect->x = rect->x * surface->w / gnScreenWidth;      // ScaleOutputRect: 逻辑坐标 → 物理坐标
// Source/utils/display.cpp:1678
const int screenWidth = GetScreenWidth() / zoomFactor;   // zoomFactor 为整数倍
```
链接：<https://github.com/diasurgical/devilutionX/blob/master/Source/utils/display.cpp>

### "是不是大屏"的判定
`Source/control/control.hpp:88`：`return GetScreenWidth() <= mainPanel.size.width && GetScreenHeight() <= SidePanelSize.height + mainPanel.size.height;`（`Source/control/control_panel.cpp:88` 同族判定 `control_panel.cpp:1608`、`:1851` `if (gnScreenWidth > mainPanel.size.width || IsRedrawEverything())`）。

---

## 3. OpenXcom（C++）

仓库：<https://github.com/OpenXcom/OpenXcom>

### 数据结构：`class Screen`
`src/Engine/Screen.h` 私有成员（实测）：

```cpp
SDL_Surface *_screen;  int _bpp;
int _baseWidth, _baseHeight;                  // 逻辑基分辨率（可配置）
double _scaleX, _scaleY;                      // 输出缩放
int _topBlackBand, _bottomBlackBand, _leftBlackBand, _rightBlackBand;   // letterbox/pillarbox
int _cursorTopBlackBand, _cursorLeftBlackBand;
...
public:
static const int ORIGINAL_WIDTH;  static const int ORIGINAL_HEIGHT;     // 320 / 200
int getDX() const;  int getDY() const;
double getXScale() const;  double getYScale() const;
static void updateScale(int type, int &width, int &height, bool change);
```

### 关键机制 1：「标准窗口偏移」`getDX()/getDY()`
```cpp
// src/Engine/Screen.cpp
105:  _baseWidth  = Options::baseXResolution;      // 逻辑基分辨率是选项
106:  _baseHeight = Options::baseYResolution;
371:  _scaleX = getWidth()  / (double)_baseWidth;  // 输出缩放 = 实际/逻辑
372:  _scaleY = getHeight() / (double)_baseHeight;
596:  int Screen::getDX() const { return (_baseWidth  - ORIGINAL_WIDTH)  / 2; }
605:  int Screen::getDY() const { return (_baseHeight - ORIGINAL_HEIGHT) / 2; }
```
`getDX()/getDY()` 的文档注释原文：**"Gets the Horizontal offset from the mid-point of the screen, in pixels."**

链接：<https://github.com/OpenXcom/OpenXcom/blob/master/src/Engine/Screen.cpp#L592-L608>

### 关键机制 2：一次性全局偏移 pass
```cpp
// src/Engine/State.cpp:379-400
/**
 * centers all the surfaces on the screen.
 */
void State::centerAllSurfaces()
{
    for (std::vector<Surface*>::iterator i = _surfaces.begin(); i != _surfaces.end(); ++i)
    {
        (*i)->setX((*i)->getX() + _game->getScreen()->getDX());
        (*i)->setY((*i)->getY() + _game->getScreen()->getDY());
    }
}

/**
 * drop all the surfaces by half the screen height
 */
void State::lowerAllSurfaces()
{
    for (...)
        (*i)->setY((*i)->getY() + _game->getScreen()->getDY() / 2);
}
```
链接：<https://github.com/OpenXcom/OpenXcom/blob/master/src/Engine/State.cpp#L379-L400>

**每个界面（State）仍然按 320x200 的原坐标摆放所有控件，然后在最后加一个偏移。** 这是最省改动的方案。

### 关键机制 3：基类不定锚，锚点由调用点自己算
`src/Engine/Surface.h`：`class Surface` 只有绝对坐标 `int _x, _y` + `virtual void setX(int)/setY(int)`，**没有任何锚定/对齐 API**。所以右/下/居中全部靠调用点算：

```cpp
src/Geoscape/GeoscapeState.cpp:128:  _bg->setX((_globe->getWidth() - _bg->getWidth()) / 2);   // 居中
src/Interface/Text.cpp:441:          x = getWidth() - 1 - _lineWidth[line];                    // 右对齐
src/Interface/Text.cpp:452:          x = getWidth() - (int)ceil((getWidth() + _font->getSpacing() - _lineWidth[line]) / 2.0);  // 居中
src/Interface/ComboBox.cpp:104:      _arrow->setX(x + getWidth() - BUTTON_WIDTH);              // 贴右
src/Battlescape/BattlescapeState.cpp:678: _cursorPosition.x = Clamp(cursorX, barWidth,
                                          _game->getScreen()->getWidth() - barWidth - ...);    // 贴右(clamp)
src/Geoscape/DogfightState.cpp:321:  graphic->setY(_window->getHeight() - ...->h);           // 贴下
```
链接：<https://github.com/OpenXcom/OpenXcom/blob/master/src/Engine/Surface.h> · <https://github.com/OpenXcom/OpenXcom/blob/master/src/Geoscape/GeoscapeState.cpp#L128>

**注意：这就是"绝对坐标 + 外置锚点计算"的现实形态——用户的项目完全可以照抄这一条，因为它不需要任何布局引擎。**

### 缩放因子怎么选
```cpp
// src/Engine/Screen.cpp:617-639
void Screen::updateScale(int type, int &width, int &height, bool change)
{
    double pixelRatioY = 1.0;
    if (Options::nonSquarePixelRatio) pixelRatioY = 1.2;      // 320x200 像素非正方形校正
    switch (type) {
    case SCALE_15X:  width = Screen::ORIGINAL_WIDTH * 1.5;  height = Screen::ORIGINAL_HEIGHT * 1.5;  break;
    case SCALE_2X:   width = Screen::ORIGINAL_WIDTH * 2;    height = Screen::ORIGINAL_HEIGHT * 2;    break;
    case SCALE_SCREEN_DIV_3: width = Options::displayWidth / 3.0;
                             height = Options::displayHeight / pixelRatioY / 3.0;  break;
    }
}
```
**缩放因子是枚举（1.5x / 2x / 屏幕1/3…），不是连续值；黑边只在 `keepAspectRatio` 时计算**（`Screen.cpp:401`、`:423`，`if (_scaleX > _scaleY && Options::keepAspectRatio)`）。

链接：<https://github.com/OpenXcom/OpenXcom/blob/master/src/Engine/Screen.cpp#L617-L645>

---

## 4. ja2-stracciatella（C++ + Rust）

仓库：<https://github.com/ja2-stracciatella/ja2-stracciatella>

**这是本次调研中机制最"正中靶心"的项目**：它有一个专门的 `UILayout` 类，把"固定尺寸 UI 在变宽屏幕上的位置"集中成一个可重算的布局表。

### `src/game/UILayout.h`（实测）

```cpp
27: #define STD_SCREEN_X                (g_ui.m_stdScreenOffsetX)
28: #define STD_SCREEN_Y                (g_ui.m_stdScreenOffsetY)
39: #define DEFAULT_EXTERN_PANEL_X_POS  (STD_SCREEN_X + 320)
40: #define DEFAULT_EXTERN_PANEL_Y_POS  (STD_SCREEN_Y + 40)
42: #define TEAMPANEL_SLOT_WIDTH        (83)     // width of one slot in the bottom team panel
43: #define TEAMPANEL_BUTTONSBOX_WIDTH  (142)    // width of the container of the buttons on the right of team panel
44: #define TEAMPANEL_HEIGHT            (120)    // height of the bottom bar team panel

79: struct UILayout
…
133:    UILayout(UINT16 screenWidth, UINT16 screenHeight);
135:    /** Set new screen size. Element positions should be recalculated after setting this.
             @see UILayout::recalculatePositions */
136:    void setScreenSize(UINT16 width, UINT16 height);
167: extern UILayout g_ui;
```
`m_stdScreenOffsetX/Y` 的注释为 **"Offset of the standard (640x480) window"**；还有 `isBigScreen()`、`recalculatePositions()`、`getTeamPanelNumSlots()`。

链接：<https://github.com/ja2-stracciatella/ja2-stracciatella/blob/master/src/game/UILayout.h#L27-L167>

### `src/game/UILayout.cc`（实测，核心公式）

```cpp
19:  UILayout g_ui(MIN_INTERFACE_WIDTH, MIN_INTERFACE_HEIGHT);

43:  bool UILayout::isBigScreen() const { ... }

49:  UINT16 UILayout::currentHeight() const      { return fInMapMode ? (STD_SCREEN_Y + m_mapScreenHeight) : m_screenHeight; }
50:  UINT16 UILayout::get_CLOCK_X() const        { return fInMapMode ? (STD_SCREEN_X + 554)
                                                    : m_teamPanelPosition.iX + m_teamPanelSlotsTotalWidth + 56; }
51:  UINT16 UILayout::get_CLOCK_Y() const        { return currentHeight() - 23; }
52:  UINT16 UILayout::get_RADAR_WINDOW_X() const { return fInMapMode ? (STD_SCREEN_X + 543)
                                                    : m_teamPanelPosition.iX + m_teamPanelSlotsTotalWidth + 45; }
53:  UINT16 UILayout::get_RADAR_WINDOW_TM_Y() const    { return currentHeight() - 107; }
54:  UINT16 UILayout::get_INV_INTERFACE_START_Y() const { return m_screenHeight - INV_INTERFACE_HEIGHT; }

57:  void UILayout::recalculatePositions()
59:      m_teamPanelSlotsTotalWidth = getTeamPanelNumSlots() * TEAMPANEL_SLOT_WIDTH;
60:      UINT16 tpXOffset = (m_screenWidth - m_teamPanelSlotsTotalWidth - TEAMPANEL_BUTTONSBOX_WIDTH) / 2;
61:      UINT16 tpYOffset = m_screenHeight - TEAMPANEL_HEIGHT;
63:      m_teamPanelWidth = m_teamPanelSlotsTotalWidth + TEAMPANEL_BUTTONSBOX_WIDTH;
…
115:     m_progress_bar_box.set(STD_SCREEN_X + 5, 2, MIN_INTERFACE_WIDTH - 10, 12);

167: UINT16 UILayout::getTeamPanelNumSlots() const
174:     int numSlots = std::min({(int)gamepolicy(squad_size),
                                (m_screenWidth - TEAMPANEL_BUTTONSBOX_WIDTH) / TEAMPANEL_SLOT_WIDTH, 12});
```

链接：<https://github.com/ja2-stracciatella/ja2-stracciatella/blob/master/src/game/UILayout.cc#L49-L136>

可复用的四点，全部直接对应本项目需求：
1. **`tpYOffset = m_screenHeight - TEAMPANEL_HEIGHT`** = 底栏贴下边缘（尺寸不变）。
2. **`tpXOffset = (m_screenWidth - 底栏总宽) / 2`** = 底栏水平居中。
3. **`get_CLOCK_X()` 这类函数按模式返回不同锚点**：地图模式下贴"标准窗口"（`STD_SCREEN_X + 554`），主界面下贴底栏右端（`m_teamPanelPosition.iX + 面板宽 + 56`）。**同一个控件、两种锚点规则、零尺寸改动。**
4. **元素数量随宽度变、尺寸不变**：`getTeamPanelNumSlots()` 用 `min(班组人数, (屏宽 - 按钮区宽)/槽宽, 12)`。
5. `STD_SCREEN_X/Y` 是"标准 640x480 窗口在宽屏上的偏移"——即 OpenXcom `getDX()/getDY()` 的同构实现。

### 视口
`SCREEN_WIDTH` / `gsVIEWPORT_WINDOW_END_Y` 被用来做 clamp：
```cpp
433:  if (giMenuAnchorX > SCREEN_WIDTH - BUTTON_PANEL_WIDTH)  giMenuAnchorX = SCREEN_WIDTH - BUTTON_PANEL_WIDTH;
437:  if (giMenuAnchorY > gsVIEWPORT_WINDOW_END_Y - BUTTON_PANEL_HEIGHT) giMenuAnchorY = gsVIEWPORT_WINDOW_END_Y - BUTTON_PANEL_HEIGHT;
```

### 缩放交给 SDL_Renderer
`src/sgp/Video.h`：`using VideoScaleQuality = ScalingQuality;`、`void InitializeVideoManager(VideoScaleQuality quality, int32_t targetFPS);`、`extern SDL_Renderer* GameRenderer;`（master 分支已迁移到 **SDL3**）。链接：<https://github.com/ja2-stracciatella/ja2-stracciatella/blob/master/src/sgp/Video.h>

### ★ 有成文的设计讨论（用户想要的那种文档）
Issue #1399 **"Tactical UI layout on wide screens"**（作者 ja2-derek，2021-09-18 开，2021-09-23 由 selaux 关闭，state_reason = completed）正文原文列出三个方案：
- **0. Current UI layout**
- **1. Centered** — "If we align the bottom bar to the center. This is more straight-forward to implement, and is more consistent with the current strategic screen."
- **2. Aligned to corners (JA2'005 style)** — "the bottom bar is split and aligned to the corners. This might be the better-looking one as there are no more useless black space. We may need a better filler texture, though. … The widget is now spread out to the two corners."

链接：<https://github.com/ja2-stracciatella/ja2-stracciatella/issues/1399>

**这是"固定尺寸 UI 在宽屏上该怎么放"最直接的一份成文设计依据**，两种方案（居中 / 拆到两角 + 中间填纹理）都可以直接照搬到用户的底栏与工具栏。

---

## 5. ScummVM

文档：<https://docs.scummvm.org/en/v2.6.1/advanced_topics/understand_graphics.html>

ScummVM 走的是**整体缩放**路线（UI 跟着放大），但它把"倍数选择 / 黑边 / 居中"做成了完整模型，其中"整数倍 + 黑边"的取舍值得照抄为**输出层**策略。

### 管线顺序（文档原文要点）
- SDL Surface 模式：先 scaler，再做 aspect-ratio correction（软件垂直拉伸），最后应用 stretch mode。
- OpenGL 模式：**不跑 scaler**，aspect-ratio correction 与 stretch mode 合成一次，直接从游戏原始分辨率（如 320x200）到最终显示分辨率。文档明确建议："when you want to preserve pixels, you may prefer to use the OpenGL mode… The aspect ratio correction in the SDL Surface mode introduces some irregularities that can be avoided with the OpenGL mode."

### stretch mode 枚举（原义）
| 模式 | 语义 |
|---|---|
| Center | 不缩放，居中 |
| **Pixel-perfect scaling** | 缩放到**能放下的最大整数倍**，余下填黑边。倍率基数是"原始分辨率 × scaler × (可选)aspect correction"（例：320x200 + 2x scaler → 1280x800 或 1920x1200；再开 aspect → 640x480 的倍数） |
| **Even pixels scaling** | 宽高**各自取不同整数倍**（仅 OpenGL 模式）。文档例子：屏幕 1920x1080、游戏 320x200 + aspect correction → **1280x1000**（320×4 / 200×5），即牺牲精确 4:3 换"每个原始像素放大同样的整数倍" |
| Fit to window | 保持比例，可能出现横向或纵向黑边（不会同时出现） |
| Stretch to window | 填满窗口，不保比例 |
| Fit to window (4:3) | 强制 4:3 |

### aspect ratio correction 的代码出处
`graphics/scaler/aspect.cpp` 顶部注释原文：
> "aspect-ratio in games using 320x200 pixel graphics with non-qudratic pixels. Applying this method effectively turns that into 320x240, which provides the correct aspect-ratio on modern displays."

函数签名（实抓）：
```cpp
int stretch200To240Nearest(uint8 *buf, uint32 pitch, int width, int height,
                           int srcX, int srcY, int origSrcY, const Graphics::PixelFormat &format);
```
相关常量：`#define kSuperFastAndUglyAspectMode 0`、`kVeryFastAndGoodAspectMode 1`、`kFastAndVeryGoodAspectMode 2`、`kSlowAndPerfectAspectMode 3`、`#define ASPECT_MODE kVeryFastAndGoodAspectMode`。

链接：<https://github.com/scummvm/scummvm/blob/master/graphics/scaler/aspect.cpp> · 文档源文件 <https://github.com/scummvm/scummvm/blob/master/doc/docportal/advanced_topics/understand_graphics.rst>

**对用户的价值**：这是"游戏逻辑分辨率 ≠ 显示分辨率"时，**唯一被完整文档化**的一套处理（含 aspect 校正、overscan、整数倍、黑边），可以作为补丁的"输出层"规格说明书。

---

## 6. ★ 最贴近的前例：Panzer General 系列的 pg-cht「A1 拉高画布」路线

仓库：<https://github.com/wicanr2/pg-cht>（SSI 5D General 系列的繁中化 + 现代系统适配工程，覆盖 Panzer General 1994 / Allied General 1995 / **Pacific General 1997** / **Panzer General II 1997**）

文档：<https://github.com/wicanr2/pg-cht/blob/main/pacgen/docs/09-a1-hires-canvas-roadmap.md>（标题：**"09 A1 路線圖:拉高內部畫布支援 24×24 CJK"**）

内容要点（原文均标注为"純靜態反組譯"可靠事实）：
- **A1 路线 = 拉高内部画布（640×480 → 更高）**，底图 nearest scale，CJK 用 24×24 画在放大后的画布上。
- **`SetDisplayMode` 是单一控制点**（这是 widescreen/高分辨率补丁的"地基"）：
  ```asm
  0x40cdf8  push 8         ; bpp = 8 (256 色 paletted)
  0x40cdfa  push 0x1e0     ; height = 480
  0x40cdff  push 0x280     ; width  = 640
  0x40ce11  call [eax+0x54]; IDirectDraw::SetDisplayMode(640,480,8)
  ```
  file offset `0x40cdfa`(height) / `0x40cdff`(width) 是唯一呼叫点。
- 解析度/stride 常量可枚举（纯静态扫描计数）：back buffer size `307200`(=640×480) 5 处；`shl reg,7`(=×640) 9 处；`push 640` 2 处；dword `640` 共 30 处；dword `480` 共 27 处 → 结论"**拉高畫布是『有限工程』而非『無源碼下無限大』**"。
- **P0–P5 路线图**：
  | Phase | 目标 |
  |---|---|
  | P0 | `SetDisplayMode` 定位 + 改 mode 是否 crash |
  | P1 | 确认 present 机制（DirectDraw `Blt` vs `Lock+copy`，用 `WINEDEBUG=+ddraw`）+ 让画面放大填满目标解析度 |
  | P2 | 底图 pixel art（SHP.PFP）nearest ×2 |
  | P3 | 字体换 24×24 + Big5 2-byte lookup（绘字管线 VA `0x474000`-`0x47b000`） |
  | **P4** | **座標 / 滑鼠命中區 ×2 映射**（minimap 等 raw widget 单独处理） |
  | P5 | 整合 + 打包 |
- 文档开头有一段**作者自己的状态声明**：先前版本中"present stretch 已用動態 trace 確認、4-word patch 讓畫面放大"的结论**已被全部移除**，因为在 tool 输出不稳定、截图无法可靠判读的 session 期间产生，"未能在乾淨環境定案"。→ **引用此文档时必须注意：它是规划 + 静态侦察，不是已验证实现。**

**方向差异（重要）**：该路线的 UI 是跟着画布一起 ×2 的（UI 会变大），而用户要的是 **UI 保持原始像素、只改位置**。两者可以并存，做法是分两层：
- 地图/底图：走 ×2 nearest（或真实高分辨率素材）；
- UI 层：走 OpenRA/devilutionX 式锚点，画在原始 800x600 逻辑坐标系里。

同仓库其他相关文件：`skills/retro-directdraw-hires-cjk/SKILL.md`（本次抓取**超时未取到内容**）、`pacgen/docs/11-2byte-engine.md`（2-byte CJK 引擎）。

---

## 7. 其他项目（一行一个，仅列实际取到证据的）

- **BuildGDX / NuBuildGDX（BUILD 引擎，Duke3D 系；Java 移植）** — <https://github.com/atsb/NuBuildGDX>：
  `src/ru/m210projects/Build/Engine.java:3423 public void setview(int x1, int y1, int x2, int y2)`、`:1378 setview(0, 0, xdim - 1, ydim - 1)`；文本绘制状态位里有明确注释：`// dastat&256 :align to the left (widescreen support)`、`// dastat&512 :align to the right (widescreen support)`（Engine.java:3465-3466）→ **宽屏下把文本对齐变成"贴左/贴右"两种可选锚点**，是"固定像素文本重新锚定"的最小实现。
- **DXX-Rebirth（Descent）** — <https://github.com/dxx-rebirth/dxx-rebirth>：`common/include/gr.h` 本次抓取**超时未取到**；`common/2d/canvas.cpp` 抓到了文件但未在其中找到锚定/重排证据。**故本项目无法提供可引用机制**（不是"没有"，而是"本次没拿到"）。
- **EDuke32** — `https://github.com/eduke32/eduke32` 返回 **404**（官方源码托管在 <https://voidpoint.io/terminx/eduke32>，本次未抓取 raw 文件）。**无可引用机制**；Build 引擎的宽屏 HUD 证据以上面 NuBuildGDX 为准。
- **Open General（open-general.com，Luis Guzman）与 PG Forever**：**在 GitHub 上找不到开放源码**（Open General 是从零重写 PG2 规格的闭源免费软件，PG Forever 同样闭源），因此**无法提供其 UI 布局代码**。它们只能作为数据格式规格来源，不能作为布局机制的出处。

---

## 8. 可直接套用到我的静态补丁项目的模式

> 前提假设（与任务描述一致）：原版逻辑分辨率 800x600，UI 由位图图集按硬编码像素坐标绘制，地图视口可以变大。下面记 `screenW/screenH` 为新的实际分辨率，`x0/y0/w/h` 为**原版 800x600 坐标**。所有公式在 800x600 下都退化为原值，因此可以**逐元素渐进迁移**、随时对照原版截图验证。

### 模式 1 — 锚点表达式 / 锚点枚举（OpenRA 式，推荐主方案）
不要在 EXE 里到处改数字，而是给每个 UI 元素建一张表：`{id, x0, y0, w, h, anchor}`，`anchor ∈ {左上, 上中, 右上, 左中, 居中, 右中, 左下, 下中, 右下}`，求值：

```
左上: x = x0                     y = y0
上中: x = (screenW - w) / 2      y = y0
右上: x = screenW - (800 - x0 - w)      y = y0
左中: x = x0                     y = (screenH - h) / 2
居中: x = (screenW - w) / 2      y = (screenH - h) / 2
右中: x = screenW - (800 - x0 - w)      y = (screenH - h) / 2
左下: x = x0                     y = screenH - (600 - y0 - h)
下中: x = (screenW - w) / 2      y = screenH - (600 - y0 - h)
右下: x = screenW - (800 - x0 - w)      y = screenH - (600 - y0 - h)
```

这等价于 OpenRA 的 `X: PARENT_WIDTH - WIDTH - 15` / `X: (WINDOW_WIDTH - WIDTH) / 2`（<https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Widgets/Widget.cs#L292-L320>）。**UI 尺寸 w/h 永远是原值 → 天然不变形。**

### 模式 2 — 「标准窗口偏移」单点 pass（OpenXcom / ja2 式，最省事）
定义两个全局量：
```
STD_SCREEN_X = (screenW - 800) / 2;     // 等价 OpenXcom Screen::getDX()
STD_SCREEN_Y = (screenH - 600) / 2;     // 等价 ja2 UILayout::m_stdScreenOffsetX/Y
```
凡是希望**整块居中**的界面（对话框、模态窗，例如"单位装备信息"），**原坐标一个都不改**，只在绘制/命中测试前统一加上 `(STD_SCREEN_X, STD_SCREEN_Y)`。参考 `State::centerAllSurfaces()`（<https://github.com/OpenXcom/OpenXcom/blob/master/src/Engine/State.cpp#L379-L400>）。这是覆盖全部 dialog 的**一行级改动**。

### 模式 3 — 贴边控件用 `screenW/screenH - 常数` 替换绝对坐标（ja2 式）
状态栏、底栏、工具条这类必须贴边的：
```
底栏 y = screenH - 底栏高                       // ja2: tpYOffset = m_screenHeight - TEAMPANEL_HEIGHT
底栏 x = (screenW - 底栏可见总宽) / 2           // ja2: tpXOffset = (m_screenWidth - 槽总宽 - 按钮区宽) / 2
工具条 y = screenH - 工具条高
右侧竖条 x = screenW - 竖条宽
```
**尺寸常量一个都不改**，只把"绝对 x/y"换成"屏幕尺寸的差"。同理可以做 clamp：`x = min(x, screenW - w)`（OpenXcom `BattlescapeState.cpp:678`、ja2 `UILayout.cc:433`）。

### 模式 4 — 面板相对坐标（devilutionX 式，改动量最小的批量方案）
如果不想动上千处绘制调用：只改每个**面板原点**（原为 `(0,0)`），绘制处保持 `panelOrigin + {x0, y0}` 的加法。参考 `GetPanelPosition(UiPanels::Inventory, {24,327})`（<https://github.com/diasurgical/devilutionX/blob/master/Source/control/control_panel.cpp#L330-L350>）。在静态补丁里，这等于"把面板原点全局变量按锚点算出来"，绘制代码二进制不动。

### 模式 5 — 视口 = 全屏减去仍被 UI 占用的部分；宽屏时底栏不再吃高度
devilutionX 只在屏幕**不够宽**时才扣视口高度：
```cpp
if (gnScreenWidth <= MainPanel.size.width) gnViewportHeight -= MainPanel.size.height;
```
（<https://github.com/diasurgical/devilutionX/blob/master/Source/control/control_panel.cpp#L275-L279>）
ja2 则是 `m_VIEWPORT_END_X = m_screenWidth; m_VIEWPORT_END_Y = m_screenHeight - 120`。
**结论：一旦底栏改成贴底且不遮挡，视口高度可直接恢复为全屏高，地图自然拿到多出来的面积。** 这是"地图吃掉额外像素"的实现方式（OpenRA 更彻底：世界视口 = 整个渲染分辨率）。

### 模式 6 — 分层与缩放纪律（综合）
- **逻辑层**：UI 永远画在 800x600 逻辑坐标系里，与屏幕分辨率的唯一联系是一个锚点函数（模式 1/2/3）。
- **输出层**：若要放大画面，只允许**整数倍 + 黑边**（ScummVM Pixel-perfect / Even-pixels、devilutionX `zoomFactor`、ja2 `ScalingQuality`）；OpenXcom 用的是 1.5x/2x 枚举。**绝不做非整数拉伸。**
- **素材层**：要放大 UI 时替换高清同名素材（OpenRA `Image2x`/`Image3x`，`ChromeProvider.cs:117-122`），而不是把原图拉伸。
- **像素完美 vs 拉伸**：ScummVM 文档明确指出软件 scaler 会引入不规则性，保像素应走"从原始分辨率一次变换到目标分辨率"的路径（<https://docs.scummvm.org/en/v2.6.1/advanced_topics/understand_graphics.html>）。

### 若要更激进（保留给未来）：OpenRA 的"UI 缩放开关"
`Renderer.SetUIScale(float)` + `Viewport.cs` 的 `UIScale / Zoom`（<https://github.com/OpenRA/OpenRA/blob/bleed/OpenRA.Game/Renderer.cs#L124>）：把"UI 缩放"做成**显式可配置因子**，默认 1（原始像素），需要时整体放大。用户当前需求是"UI 不变"，所以默认 1 + 模式 1~3 即可；但把接口留出来，未来加"UI 放大"不用重构。

---

## 9. 未能抓取 / 无源码的清单（诚实声明）

| 目标 | 状态 |
|---|---|
| DXX-Rebirth `common/include/gr.h` | 抓取**超时**，未取到；`common/2d/canvas.cpp` 取到但无锚定证据 |
| EDuke32 官方源码 | `github.com/eduke32/eduke32` = **404**；官方为 voidpoint.io 自托管，本次未抓取 raw |
| Open General / PG Forever | **无公开源码**（闭源），无法取得 UI 布局代码 |
| pg-cht `skills/retro-directdraw-hires-cjk/SKILL.md` | 抓取**超时**，未取到；只取到 `pacgen/docs/09-a1-hires-canvas-roadmap.md` |
| OpenRA `OpenRA.Game/Widgets/WidgetUtils.cs`、`OpenRA.Game/Graphics/ChromeMetrics.cs` | 按猜测路径抓取返回 **404**（真实路径为 `OpenRA.Game/Widgets/Widget.cs`、`OpenRA.Game/Graphics/ChromeProvider.cs`） |

本次全部结论均可由上述链接与 `file:line` 复核。
