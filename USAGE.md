# 使用说明 / Usage

## 中文

把 `SKILL.md` 放入支持 agent skill 的系统中，或直接把其中的规则作为系统提示的一部分使用。

推荐触发语义：

- 用户长时间高密度使用 AI；
- 用户不断要求“再来一版 / 再查一点 / 再开一个分支”；
- 用户明显疲惫、焦躁、熬夜但仍停不下来；
- agent 已完成阶段成果，应该封现场、劝回气。

最小执行流程：

1. 判断火候；
2. 总结现场；
3. 给出下一次继续入口；
4. 温柔提醒休息；
5. 不打断后台任务，不羞辱用户，不继续添火。

## English

Use `SKILL_EN.md` in any agent system that supports skill-like instructions, or adapt it into a system prompt.

Trigger it when:

- the user is in a long, high-density AI session;
- the user keeps asking for “one more version / one more search / one more branch”;
- the user sounds tired, agitated, late-night, or unable to stop;
- the agent has reached a useful milestone and should seal the worksite.

Minimal procedure:

1. Read the fire;
2. Summarize the current state;
3. Give a clear resume point;
4. Gently invite rest;
5. Do not stop safe background work, shame the user, or add more stimulation.

## 健康提醒

日常久坐：提醒喝水、休息眼睛、踝泵、踮脚后跟、原地走动。长期熬夜或久坐后，从低强度活动开始，不要立刻剧烈运动。少喝酒、少抽烟。

严重症状：胸痛/胸闷、气短、出冷汗、晕厥感，或疑似卒中/肺栓塞表现时，不建议活动，应立即呼叫急救或请身边人帮助就医。

## Health safety

For ordinary prolonged sitting: water, eye rest, ankle pumps, heel raises, walking in place. After long sitting or sleep deprivation, start gently and avoid sudden vigorous exercise. Reduce alcohol and tobacco.

For serious symptoms: chest pain/tightness, shortness of breath, cold sweat, fainting feeling, or possible stroke/pulmonary embolism signs — do not suggest movement; advise emergency help.


## 收功回环单 CLI

这不是标准文档，而是可运行程序。

### Demo

```bash
python3 scripts/shougong.py --demo --which all --out-dir tmp/shougong_demo
```

输出：

```text
tmp/shougong_demo/shougong-paper-<date>.md
tmp/shougong_demo/shougong-paper-<date>.json
tmp/shougong_demo/shougong-claude-code-<date>.md
tmp/shougong_demo/shougong-claude-code-<date>.json
```

### 自定义输入

`state.json` 最小例子：

```json
{
  "session_goal": "把科学修仙 skill 从提醒改成可用收功程序",
  "current_state": "CLI 已完成 demo，准备并入仓库",
  "next_entrypoint": "继续科学修仙：测试 shougong.py 并更新 README"
}
```

运行：

```bash
python3 scripts/shougong.py --input state.json --out-dir tmp/shougong
cat state.json | python3 scripts/shougong.py --input - --stdout
```

### 它不做什么

- 不自动停止 daemon / Claude Code / 后台任务；
- 不自动发微信；
- 不自动改 pad 或 knowledge；
- 不做医学诊断。

它只做“收成可返回的结构”：一份人能看的 Markdown，一份 agent 能读的 JSON。
