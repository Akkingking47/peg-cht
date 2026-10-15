# -*- coding: utf-8 -*-
"""把 sd25-pe 的单文件 SKILL.md 按其「生成工作流阶段」切分为 SKILL.md + references/。
内容零丢失，只重排。用法：python _split_sd25.py [--apply]
"""
import os, sys

SK = r"C:\Users\Administrator\.workbuddy\skills"
SRC = os.path.join(SK, "sd25-pe", "SKILL.md")

# (起, 止含, 容器标题 or None)
BLOCKS = {
    "01-positioning-and-principles.md": dict(
        title="定位 · 适用范围 · 不可违反的原则 · 输入状态",
        stage="阶段 0 · 定位",
        chunks=[(45, 120, None)]),   # 25-44（顶层标题 + 触发前的自升级）保留在 SKILL.md
    "02-workflow-input.md": dict(
        title="核心工作流 ① 解析目标 ② 编译长文本 ③ 盘点素材",
        stage="阶段 1 · 输入解析",
        chunks=[(121, 199, None)]),
    "03-workflow-materials-and-task.md": dict(
        title="核心工作流 ④ 素材职责与主体映射 ⑤ 置信度 ⑥ 唯一主任务 ⑦ 任务参数 ⑧ 模板净化",
        stage="阶段 2 · 素材与任务",
        chunks=[(200, 327, None)]),
    "04-templates-and-multi-material.md": dict(
        title="生成模板 · 多素材组织",
        stage="阶段 3 · 模板与素材编排",
        chunks=[(328, 497, None)]),
    "05-longvideo-edit-extend.md": dict(
        title="长视频与时间段 · 视频编辑 · 视频延长",
        stage="阶段 4 · 时长与编辑",
        chunks=[(498, 698, None)]),
    "06-keyframes.md": dict(
        title="关键帧锚点：首帧 / 尾帧 / 多关键帧 / 宫格分镜 / 白模",
        stage="阶段 5 · 关键帧",
        chunks=[(699, 818, None)]),
    "07-emotion-cinematography-sound.md": dict(
        title="情绪、摄影与声音：可观察表现 · 专业摄影 · 台词文字 · 产品流程",
        stage="阶段 6 · 表现层",
        chunks=[(819, 903, None)]),
    "08-output-contract-and-checklist.md": dict(
        title="输出合同 · 最终自检 · 兼容性与运行时说明",
        stage="阶段 7 · 交付",
        chunks=[(904, 996, None)]),
}

NOTE = ("摘自 `sd25-pe`（Seedance 2.5 Prompt Optimizer）。**章节标题沿用原技能**，便于对照。")


def main():
    apply = "--apply" in sys.argv
    src = open(SRC, encoding="utf-8").read().split("\n")
    n = len(src)
    covered = [False] * (n + 1)
    refs = {}
    for fn, cfg in BLOCKS.items():
        parts = [f"# {cfg['title']}", "", f"> {NOTE}", f"> 阶段：**{cfg['stage']}**", "", "---", ""]
        for (a, b, container) in cfg["chunks"]:
            for i in range(a, b + 1):
                covered[i] = True
            body = list(src[a - 1:b])
            if container:
                parts += [container, ""]
            while body and not body[-1].strip():
                body.pop()
            parts += body + ["", "---", ""]
        while parts and not parts[-1].strip():
            parts.pop()
        refs[fn] = "\n".join(parts) + "\n"

    missing = [i for i in range(25, n + 1) if not covered[i]]
    print(f"源文件 {n} 行")
    print("\n各 reference：")
    for fn, c in refs.items():
        print(f"  {fn:44s} {c.count(chr(10)):5d} 行  {len(c.encode('utf-8')):7d} B")
    print(f"\n覆盖校验：未覆盖行 = {missing if missing else '无 ✓'}")

    if not apply:
        print("\n（预览；加 --apply 才写盘）")
        return
    dest = os.path.join(SK, "sd25-pe", "references")
    os.makedirs(dest, exist_ok=True)
    for fn, c in refs.items():
        open(os.path.join(dest, fn), "w", encoding="utf-8", newline="\n").write(c)
    print(f"\n已写 {len(refs)} 个 reference → {dest}")


if __name__ == "__main__":
    main()
