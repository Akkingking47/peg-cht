# -*- coding: utf-8 -*-
"""PeG030 原生高分辨率重排版 —— 坐标与缩放模型（docs\\80 §2）

设计空间固定为 800x600（引擎编译期布局数据）。目标分辨率 (W, H)。

策略 strategy：
  S2「高度优先」 s = H/600            <- 16:9 玩法模式：UI 盒 = (800s)x(600s)，在 W 内居中
  S1「等比」     s = min(W/800,H/600) <- 4:3 或杂比：整幅等比，可能留黑边

单轴映射（v 是设计空间坐标，T 是该轴目标像素数，D = 800 或 600）：
  center : T/2 + (v - D/2)*s   子界面/面板/控件默认规则（屏幕中心是不动点）
  right  : T - (D - v)*s       右/下锚定元素（到右/下边缘的间距按 s 缩放）
  scale  : v*s                 锚定设计原点的元素（地图像素、图内坐标、滚动偏移）
  stretch: v*T/D               横跨/纵跨整屏的元素（底栏、分隔线、全屏背景）
  fixed  : v                   像素级真值（字体度量、遮罩位宽、结构大小）

取整：round-half-up（floor(v+0.5)）。**相邻共边只要用同一个 mode 就自动一致**
（同一设计坐标必然映射到同一目标像素），因此不会出现 1px 缝被当成黑线。

与 sites.tsv 里 rule 名的对应：
  scale_center        -> center
  anchor_right_scale  -> right （Y 轴用 bottom，等价）
  scale_origin        -> scale
  stretch_h / stretch_w -> stretch
  fixed               -> fixed
"""
from __future__ import annotations

import math

DESIGN_W = 800
DESIGN_H = 600
STRATEGIES = ("S1", "S2")
MODES = ("center", "right", "bottom", "scale", "stretch", "fixed")

#: 六档验证分辨率（docs\\80 §1 A5）
TARGET_RESOLUTIONS = [
    (1024, 768),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
]


def rp(v: float) -> int:
    """round-half-up（负数也按远离 0 的半数进位，保持一致）。"""
    return int(math.floor(v + 0.5))


class Layout:
    """一个目标分辨率下的坐标/尺寸变换器。命中测试与重绘登记必须复用同一个实例。"""

    DW = DESIGN_W
    DH = DESIGN_H

    def __init__(self, W: int, H: int, strategy: str = "S2"):
        W = int(W)
        H = int(H)
        if W <= 0 or H <= 0:
            raise ValueError("分辨率必须是正整数：%r x %r" % (W, H))
        if strategy not in STRATEGIES:
            raise ValueError("未知策略 %r（应为 S1 或 S2）" % (strategy,))
        self.W = W
        self.H = H
        self.strategy = strategy
        self.s = (H / self.DH) if strategy == "S2" else min(W / self.DW, H / self.DH)
        if self.s <= 0:
            raise ValueError("缩放因子非法：%r" % (self.s,))

    # ---------------------------------------------------------------- 单轴
    @staticmethod
    def _norm_mode(mode: str, axis: str) -> str:
        if mode == "bottom":
            return "right" if axis == "y" else mode
        if mode not in MODES:
            raise ValueError("未知 mode %r" % (mode,))
        return mode

    def _axis(self, v: float, mode: str, T: int, D: int) -> int:
        mode = self._norm_mode(mode, "x" if D == self.DW else "y")
        if mode == "fixed":
            return rp(v)
        if mode == "scale":
            return rp(v * self.s)
        if mode == "stretch":
            return rp(v * T / D)
        if mode == "center":
            return rp(T / 2 + (v - D / 2) * self.s)
        if mode == "right":
            return rp(T - (D - v) * self.s)
        raise ValueError(mode)  # pragma: no cover

    def x(self, v: float, mode: str = "center") -> int:
        return self._axis(v, mode, self.W, self.DW)

    def y(self, v: float, mode: str = "center") -> int:
        return self._axis(v, mode, self.H, self.DH)

    # ---------------------------------------------------------------- 矩形
    def rect(self, r, hx: str = "center", hy: str | None = None):
        """设计空间矩形 (x0,y0,x1,y1) -> 目标空间矩形。两端用同一条规则分别变换。"""
        x0, y0, x1, y1 = r
        if hy is None:
            hy = hx
        a, b = self.x(x0, hx), self.x(x1, hx)
        c, d = self.y(y0, hy), self.y(y1, hy)
        return (min(a, b), min(c, d), max(a, b), max(c, d))

    # ---------------------------------------------------------------- 尺寸
    def scaled_len(self, L: float) -> int:
        """长度/宽高按 s 缩放，至少 1 像素（防止控件被抹平）。"""
        return max(1, rp(L * self.s))

    def font_px(self, n: int) -> int:
        """F1 方案：字号不动，只重定位（docs\\80 §5）。P3 再换 F2/F3。"""
        return int(n)

    # ---------------------------------------------------------------- 派生
    def design_box(self):
        """UI 盒：设计空间整幅 (0,0,800,600) 按 center 规则映射后的外框。"""
        return self.rect((0, 0, self.DW, self.DH), "center", "center")

    def ui_scale_pct(self) -> float:
        return self.s * 100.0

    def describe(self) -> str:
        bx0, by0, bx1, by1 = self.design_box()
        return ("%dx%d %s s=%.4f UI盒=%dx%d @(%d,%d) 侧边留白=%d/%d" % (
            self.W, self.H, self.strategy, self.s,
            bx1 - bx0, by1 - by0, bx0, by0, bx0, self.W - bx1))

    # ---------------------------------------------------------------- 自检
    def self_test(self) -> None:
        # 中心不动点
        assert self.x(400, "center") == rp(self.W / 2), "x 中心不是屏幕中心"
        assert self.y(300, "center") == rp(self.H / 2), "y 中心不是屏幕中心"
        # 右/下锚定端点
        assert self.x(800, "right") == self.W
        assert self.y(600, "bottom") == self.H
        # 横跨整屏
        assert self.x(0, "stretch") == 0 and self.x(800, "stretch") == self.W
        assert self.y(0, "stretch") == 0 and self.y(600, "stretch") == self.H
        # 相邻共边一致（不会产生 1px 缝）
        assert self.rect((0, 0, 400, 300))[2] == self.rect((400, 0, 800, 300))[0]
        assert self.rect((0, 0, 400, 300), hy="center")[3] == self.rect((0, 300, 400, 600), hy="center")[1]
        # 单调性
        assert self.x(0) < self.x(400) < self.x(800)
        assert self.y(0) < self.y(300) < self.y(600)
        # 尺寸保底
        assert self.scaled_len(0) == 1
        assert self.rect((400, 300, 400, 300))[2] >= self.rect((400, 300, 400, 300))[0]


def _selftest() -> int:
    """跑 6 档分辨率的固定断言 + 打印实算表。"""
    L = Layout(1920, 1080, "S2")
    L.self_test()
    assert abs(L.s - 1.8) < 1e-9
    assert L.design_box() == (240, 0, 1680, 1080), L.design_box()
    # docs\80 §2 的示例：设计中央、300x200 的面板
    assert L.rect((250, 200, 550, 400)) == (690, 360, 1230, 720), L.rect((250, 200, 550, 400))
    r = L.rect((250, 200, 550, 400))
    assert (r[0] + r[2]) // 2 == L.W // 2 and (r[1] + r[3]) // 2 == L.H // 2, "示例中心未落到屏幕中心"
    assert (r[2] - r[0], r[3] - r[1]) == (L.scaled_len(300), L.scaled_len(200))

    expect_s = {(1024, 768): 1.28, (1280, 720): 1.2, (1366, 768): 1.28,
                (1600, 900): 1.5, (1920, 1080): 1.8, (2560, 1440): 2.4}
    expect_box = {(1024, 768): (0, 0, 1024, 768), (1280, 720): (160, 0, 1120, 720),
                  (1366, 768): (171, 0, 1195, 768), (1600, 900): (200, 0, 1400, 900),
                  (1920, 1080): (240, 0, 1680, 1080), (2560, 1440): (320, 0, 2240, 1440)}
    print("strategy=height-first(S2)  (UI 盒按 s 等比后居中)")
    print("%-11s %-6s %-6s %-26s %s" % ("分辨率", "s", "缩放%", "UI 盒(x0,y0,x1,y1)", "侧边留白"))
    for W, H in TARGET_RESOLUTIONS:
        l2 = Layout(W, H, "S2")
        l2.self_test()
        assert abs(l2.s - expect_s[(W, H)]) < 1e-9, (W, H, l2.s)
        assert l2.design_box() == expect_box[(W, H)], (W, H, l2.design_box())
        print("%-11s %-6.2f %-6.0f %-26s %d/%d" % (
            "%dx%d" % (W, H), l2.s, l2.ui_scale_pct(),
            str(l2.design_box()), l2.design_box()[0], W - l2.design_box()[2]))
        l1 = Layout(W, H, "S1")
        l1.self_test()

    # 与旧方案对比：旧补丁是"右对齐平移 +1120、不缩放"
    print()
    print("对照（1920x1080）：旧补丁 x'=x+1120（不缩放） vs 新模型 x'=960+(x-400)*1.8")
    for x in (0, 336, 400, 701, 799):
        print("  设计 x=%-4d 旧=%-6d 新(center)=%-6d 新(right)=%-6d" % (
            x, x + 1120, L.x(x), L.x(x, "right")))
    print()
    print("SELFTEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
