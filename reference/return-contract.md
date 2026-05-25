# Return Contract / 收功回环单 schema

科学修仙不是普通提醒，而是把一轮高密度 AI 协作收成可返回的结构。`scripts/shougong.py` 使用以下最小 schema 生成 Markdown + JSON 收功单。

## 必填字段

```json
{
  "session_goal": "这一炉为何而起，一句话目标",
  "current_state": "此刻停在哪里，两三句话",
  "next_entrypoint": "回来后可直接照抄的一句话口令"
}
```

## 可选字段

```json
{
  "completed_artifacts": [ {"name": "产物名", "path": "文件路径", "note": "说明"} ],
  "open_loops": [ {"name": "未闭之环", "why_open": "为何未闭", "suggested_next": "下一步"} ],
  "background_tasks": [ {"name": "后台任务", "where": "位置/ID", "eta": "预计", "watch": "如何看守"} ],
  "evidence_or_files": [ {"label": "证据或文件", "ref": "路径/链接/ID"} ],
  "do_not_continue_list": ["现在不要继续添火的事项"],
  "crystallization_targets": [ {"target": "pad|knowledge|skill|lingtai|issue|current_projects|export", "action": "add|update|prune", "note": "说明"} ],
  "human_energy_state": {"level": "ok|warm|hot|depleted", "signs": ["观察到的信号"], "hours_active": 2},
  "safety_boundary": {"red_flags": ["严重症状边界"], "fallback_action": "出现严重症状时的固定应对句"}
}
```

## CLI 用法

```bash
python3 scripts/shougong.py --demo --which all --out-dir tmp/shougong_demo
python3 scripts/shougong.py --input state.json --out-dir tmp/shougong
cat state.json | python3 scripts/shougong.py --input - --stdout
```

输出包括：

- `shougong-<id>.md`：人看的收功单；
- `shougong-<id>.json`：agent / 下次会话可读的结构化副本。

## 固定原则

1. 先封现场，再护元气。
2. CLI 只生成 artifact，不自动停 daemon、不发消息、不改 pad、不提交 git。
3. safety boundary 只处理严重症状边界，不做医学诊断。
4. 下一步接入 LingTai 时，应先做 read-only collector，再做 dry-run write-back，最后再考虑 trajectory_id 合流。
