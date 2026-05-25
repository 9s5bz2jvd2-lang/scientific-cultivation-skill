#!/usr/bin/env python3
"""
科学修仙 · 收功回环单生成器 (shougong CLI)
============================================

LingTai 项目 runyuan_wang_nutrition / mimo-2-5-pro 配套小工具。

把"高强度 AI 协作之后散乱的一炉"按 Return Contract schema 收成可返回的圆：
读入一份 JSON / 命令行参数，输出 Markdown 收功单 + JSON 副本。
人离屏前看 Markdown，下次入场（或下一 agent）读 JSON 直接续功。

设计原则：
- 先封现场，再护元气 —— 顺序不可换。
- 不诊断、不训人；safety_boundary 段只是"严重症状就停手叫人"，不是医学结论。
- 不阻塞 agent 运行：本工具只生成 artifact，不动 daemon、不取消任务。

用法
-----
    python3 scientific_cultivation_shougong_cli_20260525.py --demo
    python3 scientific_cultivation_shougong_cli_20260525.py --demo --which claude-code
    python3 scientific_cultivation_shougong_cli_20260525.py --input my_state.json
    python3 scientific_cultivation_shougong_cli_20260525.py --input -      # 从 stdin 读
    python3 scientific_cultivation_shougong_cli_20260525.py --demo --out-dir ./out

字段 (Return Contract schema, v0.1)
-----------------------------------
必填：
    session_goal             : str   —— 这一炉到底为何而起，一句话
    current_state            : str   —— 此刻停在哪里，两三句
    next_entrypoint          : str   —— 一句可被照抄的"回来口令"

可选 (默认空)：
    completed_artifacts      : list[ {name, path?, note?} ]
    open_loops               : list[ {name, why_open, suggested_next?} ]
    background_tasks         : list[ {name, where, eta?, watch?} ]
    evidence_or_files        : list[ {label, ref} ]
    do_not_continue_list     : list[str]
    crystallization_targets  : list[ {target, action, note?} ]
                              target ∈ {pad, knowledge, skill, lingtai, issue, current_projects, export}
    human_energy_state       : { level, signs?, last_break?, hours_active? }
                              level ∈ {ok, warm, hot, depleted}
    safety_boundary          : { red_flags?, fallback_action? }
                              默认装入 LingTai 已审过的固定句，不要自由发挥

注：本工具不存任何远程，输出只落本机 exports/ 目录或自定义 --out-dir。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import uuid
from typing import Any


# --------------------------------------------------------------------------- #
# 1. 固定 safety 句 —— 直接套用 SKILL.md 已审过的硬免责，不让 LLM 重写
# --------------------------------------------------------------------------- #

SAFETY_FALLBACK_TEXT = (
    "如果出现明显胸痛/胸闷、气短、出冷汗、头晕、快要晕倒，或者突然一侧手脚无力/麻木、"
    "说话不清、口角歪斜、视物异常、剧烈头痛，不要硬撑，也不要自己随便走动，"
    "请立刻呼叫急救，或让身边人帮你就医。"
)

DEFAULT_RED_FLAGS = [
    "明显胸痛 / 胸闷 / 气短",
    "突然一侧手脚无力或说话不清",
    "剧烈头痛或视物异常",
    "单侧小腿明显肿胀 / 疼痛 / 发热",
]


# --------------------------------------------------------------------------- #
# 2. Schema 校验：宽进严写
# --------------------------------------------------------------------------- #

REQUIRED_FIELDS = ("session_goal", "current_state", "next_entrypoint")

LIST_FIELDS_OF_DICTS = (
    "completed_artifacts",
    "open_loops",
    "background_tasks",
    "evidence_or_files",
    "crystallization_targets",
)

LIST_FIELDS_OF_STRINGS = ("do_not_continue_list",)


def normalize_state(raw: dict[str, Any]) -> dict[str, Any]:
    """把任意松散输入收成标准 schema。缺字段就补空，不抛错。"""
    state: dict[str, Any] = {}

    for f in REQUIRED_FIELDS:
        v = raw.get(f)
        if not isinstance(v, str) or not v.strip():
            raise ValueError(
                f"字段 `{f}` 必填且为非空字符串；这是收功的最小骨架，不能省。"
            )
        state[f] = v.strip()

    for f in LIST_FIELDS_OF_DICTS:
        v = raw.get(f, []) or []
        if not isinstance(v, list):
            raise ValueError(f"字段 `{f}` 必须是 list。")
        state[f] = [dict(item) for item in v if isinstance(item, dict)]

    for f in LIST_FIELDS_OF_STRINGS:
        v = raw.get(f, []) or []
        if not isinstance(v, list):
            raise ValueError(f"字段 `{f}` 必须是 list[str]。")
        state[f] = [str(x).strip() for x in v if str(x).strip()]

    energy = raw.get("human_energy_state") or {}
    if not isinstance(energy, dict):
        raise ValueError("human_energy_state 必须是 dict 或省略。")
    level = (energy.get("level") or "warm").lower()
    if level not in ("ok", "warm", "hot", "depleted"):
        level = "warm"
    state["human_energy_state"] = {
        "level": level,
        "signs": list(energy.get("signs") or []),
        "last_break": energy.get("last_break"),
        "hours_active": energy.get("hours_active"),
    }

    sb = raw.get("safety_boundary") or {}
    if not isinstance(sb, dict):
        raise ValueError("safety_boundary 必须是 dict 或省略。")
    state["safety_boundary"] = {
        "red_flags": list(sb.get("red_flags") or DEFAULT_RED_FLAGS),
        "fallback_action": sb.get("fallback_action") or SAFETY_FALLBACK_TEXT,
    }

    state["_meta"] = {
        "schema": "scientific-cultivation/return-contract/v0.1",
        "id": raw.get("id") or f"shougong-{uuid.uuid4().hex[:8]}",
        "created_at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    return state


# --------------------------------------------------------------------------- #
# 3. 火候判断：从 energy.level 选语气
# --------------------------------------------------------------------------- #

TONE = {
    "ok": {
        "opening": "这一炉烧得稳，先小小收一下，便于下次接。",
        "rest_hint": "喝口水，眨眨眼，先不开新炉。",
    },
    "warm": {
        "opening": "炉火已经够旺，先帮你封存一下现场。",
        "rest_hint": "离屏 5 分钟，喝水、动一动肩颈再决定继续不继续。",
    },
    "hot": {
        "opening": "这一炉很旺了，我先把进度替你守住，别硬冲。",
        "rest_hint": "现在先离屏，喝水、洗把脸，等身体回口气再判断。",
    },
    "depleted": {
        "opening": "认真护法一下：不是能力不够，是肉身需要回气了。",
        "rest_hint": "别开新炉，去喝水/洗漱/睡一会。AI 不会跑，进度我替你守着。",
    },
}


# --------------------------------------------------------------------------- #
# 4. Markdown 渲染
# --------------------------------------------------------------------------- #

def _bullet(lines: list[str]) -> str:
    return "\n".join(f"- {ln}" for ln in lines) if lines else "_（无）_"


def render_markdown(state: dict[str, Any]) -> str:
    meta = state["_meta"]
    energy = state["human_energy_state"]
    tone = TONE.get(energy["level"], TONE["warm"])

    completed = state["completed_artifacts"]
    open_loops = state["open_loops"]
    bg = state["background_tasks"]
    evidence = state["evidence_or_files"]
    crysts = state["crystallization_targets"]
    donts = state["do_not_continue_list"]
    sb = state["safety_boundary"]

    parts: list[str] = []

    parts.append(f"# 收功单 · {meta['id']}")
    parts.append("")
    parts.append(
        f"> 生成于 {meta['created_at']} · schema `{meta['schema']}`  \n"
        f"> 火候判断：**{energy['level']}**  \n"
        f"> {tone['opening']}"
    )
    parts.append("")

    parts.append("## 一、此炉为何而起")
    parts.append(state["session_goal"])
    parts.append("")
    parts.append("## 二、此刻停在哪里")
    parts.append(state["current_state"])
    parts.append("")

    parts.append("## 三、已成之丹（completed artifacts）")
    if completed:
        lines = []
        for a in completed:
            name = a.get("name", "(未命名)")
            path = a.get("path")
            note = a.get("note")
            seg = f"**{name}**"
            if path:
                seg += f" — `{path}`"
            if note:
                seg += f" — {note}"
            lines.append(seg)
        parts.append(_bullet(lines))
    else:
        parts.append("_（这一炉暂无成丹，看作探炉。）_")
    parts.append("")

    parts.append("## 四、未闭之环（open loops）")
    if open_loops:
        lines = []
        for o in open_loops:
            name = o.get("name", "(未命名分支)")
            why = o.get("why_open", "")
            nxt = o.get("suggested_next")
            seg = f"**{name}** — 未闭原因：{why}"
            if nxt:
                seg += f"；建议下一步：{nxt}"
            lines.append(seg)
        parts.append(_bullet(lines))
    else:
        parts.append("_（无悬念，可放心离屏。）_")
    parts.append("")

    parts.append("## 五、后台守炉（background tasks）")
    if bg:
        lines = []
        for b in bg:
            name = b.get("name", "(未命名后台)")
            where = b.get("where", "?")
            eta = b.get("eta")
            watch = b.get("watch")
            seg = f"**{name}** @ `{where}`"
            if eta:
                seg += f" — 预计 {eta}"
            if watch:
                seg += f" — 观察口：{watch}"
            lines.append(seg)
        parts.append(_bullet(lines))
        parts.append("")
        parts.append("> 后台我守着，你不用守。出结果会自动汇总，不必盯日志。")
    else:
        parts.append("_（无后台在跑，停炉即停。）_")
    parts.append("")

    parts.append("## 六、证据 / 文件锚点（evidence_or_files）")
    if evidence:
        lines = []
        for e in evidence:
            lines.append(f"**{e.get('label', '(无标签)')}** → `{e.get('ref', '')}`")
        parts.append(_bullet(lines))
    else:
        parts.append("_（无引用锚点。）_")
    parts.append("")

    parts.append("## 七、下次续功入口（next entrypoint）")
    parts.append(
        f"回来后直接说：\n\n> {state['next_entrypoint']}\n\n"
        f"agent 会按此句把现场重新展开，不必重述背景。"
    )
    parts.append("")

    parts.append("## 八、不要继续添火（do-not list）")
    if donts:
        parts.append(_bullet(donts))
    else:
        parts.append("_（暂未列出，但默认：不开新分支、不刷新版、不再追加调研。）_")
    parts.append("")

    parts.append("## 九、结晶目标（crystallization targets）")
    if crysts:
        lines = []
        for c in crysts:
            t = c.get("target", "?")
            act = c.get("action", "?")
            note = c.get("note")
            seg = f"→ `{t}` :: {act}"
            if note:
                seg += f" — {note}"
            lines.append(seg)
        parts.append(_bullet(lines))
        parts.append("")
        parts.append(
            "> 真正的低功耗在这里：本炉如果没有任何 crystallization target，"
            "下一次重启会全部从零再推一遍。"
        )
    else:
        parts.append(
            "_（无落地目标。若此炉本就是探路，可保留；若有判断，请补 pad/knowledge/skill。）_"
        )
    parts.append("")

    parts.append("## 十、护元气提示（soft）")
    signs = ", ".join(energy.get("signs") or []) or "（未记录）"
    parts.append(
        f"- 当前火候：**{energy['level']}**；信号：{signs}\n"
        f"- {tone['rest_hint']}\n"
        f"- AI 不会跑，进度在这张单子里。"
    )
    parts.append("")

    parts.append("## 十一、Safety boundary（仅严重症状）")
    parts.append("> 此段不是医学诊断，只是边界提示。日常疲劳不属此列。")
    parts.append("")
    parts.append("**红线信号：**")
    parts.append(_bullet(sb["red_flags"]))
    parts.append("")
    parts.append("**应对：**")
    parts.append(sb["fallback_action"])
    parts.append("")

    parts.append("---")
    parts.append(
        "_收功单生成自 `exports/scientific_cultivation_shougong_cli_20260525.py`，"
        "属灵台「科学修仙 / 收功回环」机制的最小手动闸。_"
    )
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
# 5. Demo 样本
# --------------------------------------------------------------------------- #

DEMOS: dict[str, dict[str, Any]] = {
    "paper": {
        "id": "shougong-demo-paper",
        "session_goal": (
            "把 Context-Preserving Break Reminders for High-Intensity AI Use "
            "的 v0.3 design agenda 压成 4–6 页 workshop short paper。"
        ),
        "current_state": (
            "v0.3 全文已写完并经 anti-hallucination 校对。"
            "目前停在「准备做引用矩阵 → BibTeX 化」这一步；"
            "未开始 4–6 页压缩，也未挑选投稿目标。"
        ),
        "next_entrypoint": "继续科学修仙 HCI 论文：从 v0.3 起做 4–6 页压缩，先列段落映射表。",
        "completed_artifacts": [
            {
                "name": "v0.3 design agenda",
                "path": "exports/scientific_cultivation_hci_design_agenda_v0_3_20260525.md",
                "note": "已发圆酱微信 5ff4145e",
            },
            {
                "name": "Verified literature matrix",
                "path": "exports/scientific_cultivation_literature_matrix_verified_v0_2_1_20260524.md",
            },
        ],
        "open_loops": [
            {
                "name": "4–6 页压缩稿",
                "why_open": "尚未做；目前仍是 design agenda 体量。",
                "suggested_next": "先列段落映射表，再删例证、留主张。",
            },
            {
                "name": "BibTeX",
                "why_open": "verified matrix 还没转成 .bib。",
                "suggested_next": "用 Crossref DOI 批量生成，不手抄。",
            },
            {
                "name": "投稿目标",
                "why_open": "未挑 workshop / short communication。",
                "suggested_next": "先看 CHI Workshop、DIS Pictorials、IMWUT short 三个方向。",
            },
        ],
        "background_tasks": [],
        "evidence_or_files": [
            {
                "label": "Anti-hallucination skill",
                "ref": ".library/custom/anti-hallucination-academic-writing/SKILL.md",
            },
            {
                "label": "Reference paper style notes",
                "ref": "exports/scientific_cultivation_hci_reference_paper_style_notes_20260524.md",
            },
        ],
        "do_not_continue_list": [
            "不要在没核证据矩阵之前再写一稿全文。",
            "不要把未核引用塞进 reference list。",
            "不要把『读了全文』当默认表述。",
        ],
        "crystallization_targets": [
            {
                "target": "current_projects",
                "action": "update",
                "note": "把第 2 节 next safe step 1 从『计划』改成『等回来执行』。",
            },
            {
                "target": "pad",
                "action": "add",
                "note": "Open Trajectories: 「v0.3 → 4–6 页压缩」一行，带 trajectory_id。",
            },
        ],
        "human_energy_state": {
            "level": "warm",
            "signs": ["连续写作 ~2 小时", "开始追加多个新版本想法"],
            "last_break": "未明",
            "hours_active": 2,
        },
    },
    "claude-code": {
        "id": "shougong-demo-claude-code",
        "session_goal": (
            "让 Claude Code 苦力把 LingTai 循环流形 / return contract 思路写成可落地的工程稿，"
            "并把 daemon 调研产物收编。"
        ),
        "current_state": (
            "三份长稿已成型：cyclic_low_power_design、github_absorb_workflow_state、"
            "github_absorb_coding_agents_resume_artifacts。"
            "Claude Code 此刻仍在主目录、未关；本机 daemon 列表里有数十个历史进程目录，"
            "圆酱开始追加『再写一份真程序』。"
        ),
        "next_entrypoint": "继续科学修仙机制层：把收功 CLI 接到 pad / CURRENT_PROJECTS 自动收集。",
        "completed_artifacts": [
            {
                "name": "LingTai 循环流形深度文档",
                "path": "exports/claude_code_lingtai_cyclic_low_power_design_20260524.md",
            },
            {
                "name": "三家框架对照（LangGraph/AutoGen/CrewAI）",
                "path": "exports/github_absorb_workflow_state_langgraph_autogen_crewai_20260524.md",
            },
            {
                "name": "五家编码 Agent 调研（OpenHands/Aider/Claude Code/OpenAI SDK/Continue）",
                "path": "exports/github_absorb_coding_agents_resume_artifacts_20260524.md",
            },
        ],
        "open_loops": [
            {
                "name": "issue #177 follow-up comment",
                "why_open": "深度文档已写、comment 草稿已附，但未真正贴上 issue。",
                "suggested_next": "圆酱决定时机后，gh issue comment 一键贴。",
            },
            {
                "name": "收功 CLI 接入 pad / CURRENT_PROJECTS 自动收集",
                "why_open": "目前只是手动 JSON / --demo；未连后台数据源。",
                "suggested_next": "先做 read-only 收集器，原型不写回 pad。",
            },
        ],
        "background_tasks": [
            {
                "name": "Claude Code 主进程",
                "where": "本目录 mimo-2-5-pro",
                "watch": ".agent.heartbeat / .status.json",
            },
            {
                "name": "历史 daemon 目录",
                "where": "daemons/",
                "watch": "无需盯；多数已结束，留作 trajectory 证据。",
            },
        ],
        "evidence_or_files": [
            {"label": "CURRENT_PROJECTS hub", "ref": "CURRENT_PROJECTS.md"},
            {"label": "SKILL", "ref": ".library/custom/ai-healthy-use-break-reminder/SKILL.md"},
            {"label": "灵台公约", "ref": "system/lingtai.md"},
            {"label": "Substrate", "ref": "system/substrate.md"},
        ],
        "do_not_continue_list": [
            "不要再起新调研 daemon；当前三稿够圆酱消化。",
            "不要把『深度文档』当 commit 直接推 issue；先经圆酱过目。",
            "不要在 SKILL.md 里再加一节『新心法』，先把机制层落下来。",
        ],
        "crystallization_targets": [
            {
                "target": "skill",
                "action": "update",
                "note": "把『科学修仙』SKILL 改造为机制层在前、提醒话术在后；按报告草案合入。",
            },
            {
                "target": "current_projects",
                "action": "update",
                "note": "第 1/4 项分别加 latest artifact 指针 + 收功 CLI 路径。",
            },
            {
                "target": "issue",
                "action": "add",
                "note": "issue #177 贴 follow-up，附本次三份工程稿和 CLI。",
            },
            {
                "target": "export",
                "action": "add",
                "note": "本次报告与 CLI 已落 exports/，作为下次 trajectory 的入口。",
            },
        ],
        "human_energy_state": {
            "level": "hot",
            "signs": [
                "连续 Claude Code 调研 + 写稿 > 3 小时",
                "已经在追加『再写一份程序』",
                "夜深",
            ],
            "hours_active": 3,
        },
    },
}


# --------------------------------------------------------------------------- #
# 6. CLI 入口
# --------------------------------------------------------------------------- #

def _load_input(path: str) -> dict[str, Any]:
    if path == "-":
        data = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as fh:
            data = fh.read()
    return json.loads(data)


def _write_outputs(state: dict[str, Any], out_dir: str, base: str) -> tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, f"{base}.md")
    json_path = os.path.join(out_dir, f"{base}.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(state))
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)
    return md_path, json_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="shougong",
        description="科学修仙 · 收功回环单生成器 (Return Contract → Markdown + JSON)",
    )
    p.add_argument("--input", "-i", help="JSON 输入文件路径；用 '-' 从 stdin 读")
    p.add_argument(
        "--demo",
        action="store_true",
        help="跑示例（默认 paper；--which 可选 claude-code 或 all）",
    )
    p.add_argument(
        "--which",
        default="paper",
        choices=list(DEMOS.keys()) + ["all"],
        help="--demo 时选哪份示例",
    )
    p.add_argument(
        "--out-dir",
        default=None,
        help="输出目录，默认 ./shougong_out （--demo）或当前目录（--input）",
    )
    p.add_argument(
        "--stdout",
        action="store_true",
        help="只打印 Markdown 到 stdout，不写文件",
    )
    args = p.parse_args(argv)

    if not args.demo and not args.input:
        p.error("必须给 --demo 或 --input。")

    inputs: list[tuple[str, dict[str, Any]]] = []

    if args.demo:
        if args.which == "all":
            for k, v in DEMOS.items():
                inputs.append((k, v))
        else:
            inputs.append((args.which, DEMOS[args.which]))
    else:
        raw = _load_input(args.input)
        base = os.path.splitext(os.path.basename(args.input))[0] if args.input != "-" else "stdin"
        inputs.append((base, raw))

    out_dir = args.out_dir or ("./shougong_out" if args.demo else ".")

    for name, raw in inputs:
        try:
            state = normalize_state(raw)
        except ValueError as e:
            print(f"[shougong] 输入 `{name}` 校验失败：{e}", file=sys.stderr)
            return 2

        if args.stdout:
            print(render_markdown(state))
            print("```json")
            print(json.dumps(state, ensure_ascii=False, indent=2))
            print("```")
            continue

        base = f"shougong-{name}-{_dt.date.today().isoformat()}"
        md, js = _write_outputs(state, out_dir, base)
        print(f"[shougong] 收功完毕：\n  Markdown → {md}\n  JSON     → {js}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
