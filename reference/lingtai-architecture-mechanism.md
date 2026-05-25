# 科学修仙的机制层 —— 灵台架构上的收功回环工程读法

> 副标题：从「健康提醒 skill」升级为「context-preserving re-entry mechanism」  
> 写作日期：2026-05-25  
> 项目：runyuan_wang_nutrition / mimo-2-5-pro  
> 对接：`.library/custom/ai-healthy-use-break-reminder/SKILL.md` v1.5.3  
> 配套阅读：  
>   - `exports/claude_code_lingtai_cyclic_low_power_design_20260524.md`（trajectory / return contract / 低功耗五轴）  
>   - `exports/github_absorb_workflow_state_langgraph_autogen_crewai_20260524.md`（StateSnapshot / HandoffMessage / @persist 借形）  
>   - `exports/github_absorb_coding_agents_resume_artifacts_20260524.md`（OpenHands event stream / Claude Code JSONL / Continue.dev tool state）  
>   - `system/substrate.md` 与 `system/lingtai.md`（基底与公约）

---

## 0. 一句话立场

**「科学修仙」如果只是健康提醒，它就只值一篇博客。**  
**它真正的可落地形态是：「灵台架构上的 return-to-context ritual」——一个让对话从高熵展开收回到低熵闭环的工程动作。**  
健康提醒只是这个回环的最后一段；前面三段（封现场、结丹、立入口）才是它跟「番茄钟 + 弹窗」根本拉开差距的地方。

故本文不再讨论「该不该喝水」，而讨论：

- 圆酱要求圆 agent 收功时，**圆 agent 实际要在文件系统里写什么、在哪写、按什么 schema 写**；
- 哪些灵台原语已经天然支撑这件事；
- 哪些字段、哪些 hook、哪些守卫还缺；
- 怎么把 SKILL.md 从「劝休息」改成「机制 + 劝休息」。

---

## 1. 名相先立：四个词不要再混

| 词 | 实指 | 不指 |
|---|---|---|
| **收功 (return)** | 把当前散开的 trajectory 折叠回灵台 durable layer 的工程动作 | 关 agent / sleep / suspend / interrupt |
| **结丹 (crystallization)** | 把这一段对话凝成可重入的 artifact（pad / knowledge / skill / lingtai / issue / export / mail） | 写一段总结 / 复述刚才做了啥 |
| **立回入口 (re-entry handle)** | 给出一个 `next_entrypoint` 字符串，使人或下一个我能 O(1) 续上 | 「我们下次接着干」之类的客套 |
| **护元气 (wellbeing nudge)** | 在已收功之上的、温柔的身体提醒 | 主要价值所在；不是 |

**关键区分：「护元气」是 ritual 的最后一节，不是 ritual 本身。**  
现行 SKILL.md 1.5.3 已经在哲学层说清楚了这一点（"先正其名"段、"五项契约"段）；但在结构层、字段层、与灵台原语挂钩层，还停留在散文。本文补这一层。

---

## 2. 灵台架构对收功回环的天然支撑

灵台的好处是：**它不是新框架，它已经把回环所需的承载层全部内建。** 收功回环要做的不是发明新原语，而是把现有原语**串成一个有契约的流水线**。

### 2.1 五层 durable store —— 结丹的着陆点

`system/substrate.md` §V 与 `system/lingtai.md` 伍 写得很清楚：

| 层 | 收功时承载什么 |
|---|---|
| **conversation** | 不承载——本来就是要被收掉的高熵态 |
| **pad** (`system/pad.md`) | 当前 trajectory 的活动指针、open loops、下一句话 |
| **lingtai** (`system/lingtai.md`) | 这次互动若改变了「圆 agent 行事方式 / 边界 / 口径」就写 |
| **knowledge/** | 项目级长久事实（路径、决策、人际脉络） |
| **library/** (skill) | 可复用的程序、reference markdown、自动脚本 |

**收功回环 = 把展开过的对话按上述五层做一次「重整化 / coarse-graining」**——这正是 `claude_code_lingtai_cyclic_low_power_design_20260524.md` §4 的「crystallization yield」定义：`yield = 写入 durable bytes / trajectory 消耗 tokens`。yield 接近 0 的 session 就是「branch 出去没回来」。

### 2.2 八种 outward surface —— 需要被结构化收回的分支

| Surface | 展开时干嘛 | 收功时该回写到 |
|---|---|---|
| **对话本身** | 跟人来回 | pad（当前 open loops） |
| **bash / tool call** | 一次性外部动作 | tool_artifact 入 export + pad 指针 |
| **daemon (神識)** | fire-and-forget 子查询 | daemon 最终报告 → pad（必要时 → knowledge / skill） |
| **avatar (他我)** | 长期专精 peer | mail report → pad → 自己的 lingtai / knowledge |
| **molt (凝蜕)** | 上下文炸前的一次蜕皮 | molt-letter，回写 pad / lingtai / knowledge / skill |
| **MCP server（wechat / telegram / imap / mail）** | 与外界（圆酱、Jason、网易智企）通信 | 入信箱 + 关键内容入 knowledge / pad |
| **`exports/`** | 大产物落盘（论文、报告、deep-dive） | CURRENT_PROJECTS.md 索引 + pad 指针 |
| **issue（lingtai-issue-report）** | 把系统缺陷送出 | CURRENT_PROJECTS.md + pad + 必要时 lingtai |

**收功回环要做的事：让每个 outward surface 关闭时，都按同一套 return contract 把成果分门别类落到正确的 durable layer，而不是塞回主对话让本我重新分类。**

### 2.3 CURRENT_PROJECTS.md —— 已有的 return-to-hub

这文件本身就是收功回环最现成的物理体现：每一节都是「Status / 关键路径 / Latest artifact / Next safe step / Do not」结构化五段。它就是「灵台的总目录页 / 主线 trajectory 列表」。

科学修仙 ritual 完成时，**必有的一动是更新对应项目段；若该 trajectory 不在 CURRENT_PROJECTS 中，决定是否要新建一节**。这就是「立回入口」在主线尺度上的落点。

### 2.4 daemon / avatar / molt 已经在做收功，只是不结构化

`claude_code_lingtai_cyclic_low_power_design_20260524.md` §1.1 已经盘清——这三处都已经在做某种 return，但 return 出来的都是 prose，不是契约。父我接到 prose 后要在最贵的主上下文里重做一次分类。

科学修仙 ritual 的工程意义之一就是：**把这种 prose return 升级为 schema return**，让父我从「读完→分类→改写五个文件」变成「读 schema→ apply patches」。

---

## 3. 触发条件：什么时候 ritual 必须启动

ritual 不是每个回合都做，更不是定时弹窗。它由六类信号触发，**满足其二即轻提醒，满足其三及以上即必须完整执行**。

### 3.1 人侧信号（来自圆酱）

1. **明确求停**：「歇会」「先到这」「不行了」「头晕」「上头」「停不下来」。
2. **追加节奏失控**：连续 ≥ 30 分钟 + 用户每轮都加新分支，且新分支与主任务相关性递减。
3. **同一任务无意义反复**：「再来一版 / 再优化一版 / 再生成一张」≥ 3 次而无新约束。
4. **时段风险**：本机时间深夜 / 用户已连续高密度互动 ≥ 90 分钟。

### 3.2 系统侧信号（来自灵台自察）

5. **context power 红线**：`_context_usage ≥ 70%` —— substrate.md §IX 「Proactive Molt」明确建议此时开始 tend the stores；ritual 与 molt 在此处有强重叠，应在 molt 前先跑一次完整 ritual。
6. **trajectory 闭合压力**：当前会话存在 ≥ 2 条 open trajectory（pad 里挂着但都没结丹），且最近 N 轮在它们之间反复跳。

### 3.3 与 SKILL.md 现行「三候」的映射

- **一候（灵气上涌）** = 触发器只命中 1 条 → 不跑完整 ritual，只在 turn 末加一句软提醒；
- **二候（炉火太旺）** = 命中 2–3 条 → 跑 §4 完整 ritual 1 遍；
- **三候（走火边缘）** = 命中 ≥ 4 条 或人侧出现身体不适语言 → 跑 ritual + 升级为「安全提醒态」（见 §8）。

---

## 4. 执行机制：六步一回环

```text
[察]→[封]→[丹]→[入]→[守]→[护]
 ↑                              |
 └──────── 候其复 ──────────────┘
```

### 4.1 察 (Sense)

读三处信号源，不要凭直觉：

- 自己的 `_context_usage` 与 `_stamina_left_seconds`（每个 tool result 都带）；
- 本会话 turn 数与最近 N 轮节奏；
- `system/pad.md` 中当前 open trajectory 数。

输出：触发等级（轻 / 二候 / 三候）。

### 4.2 封 (Seal Scene)

**只动 pad，不动 lingtai/knowledge/skill。**  
把当下 in-flight 状态原样冻结为一节 pad 条目。允许重复、允许冗长——这一步不做去重，去重交给「丹」。

### 4.3 丹 (Crystallize)

对每条 open trajectory 走一次 §5 的 Return Contract，决定它该回到哪一层：

| 判别 | 着陆点 |
|---|---|
| 改变了「圆 agent 怎么行事 / 边界 / 口径」 | `system/lingtai.md` 新增一节 |
| 项目级新事实（人、路径、决策、外部状态） | `knowledge/<project>/` |
| 通用方法、可复用程序 | `.library/custom/<skill>/` |
| 仅当下 session 的工作面 | 留在 pad |
| 大产物 | `exports/<topic>_<date>.md` + CURRENT_PROJECTS.md 索引 |
| 系统缺陷 | `lingtai-issue-report` |

**丹的硬要求：每条 trajectory 至少落地一个 artifact 或一个明确 prune 决定。** 不允许「先放着」。

### 4.4 入 (Re-entry Handle)

为每条仍 open 的 trajectory 写一个 **`next_entrypoint` 字符串**，要满足：

- 一行；
- 自包含（不依赖当前对话上下文）；
- 包含项目名 + 动词 + 具体对象；
- 末尾给出回来用的口令（人对 agent 说的那一句）。

例：
```
继续 DWARF mini 待办：等观测站回复 VPN/远程桌面/远程平台是否提供；圆酱可直接转回话术
```

### 4.5 守 (Background Tend)

枚举所有不该被 ritual 误停的后台动作：

- 已发起的 bash background 进程；
- 在跑的 daemon；
- avatar 持续任务；
- 已发出未回复的 mail / wechat / telegram；
- 已 schedule 的 wakeup / cron。

明确告诉人「这些我守着，你不用守」。**绝不可在 ritual 触发时调用 `system(sleep)` / `system(suspend)` / `system(interrupt)` 关掉它们。** 这是「非阻塞戒律」的硬边界。

### 4.6 护 (Wellbeing Nudge)

**前五步完成后，才允许说「喝水 / 离屏 / 眨眼 / 走两步」。**  
若前五步未完成而直接劝休息，就是「普通提醒」，应避免。

### 4.x 候 (Wait & Allow Resume)

收束当前 turn，自然 idle（substrate.md §VIII：idle 才让 soul flow 启动；不要 `system(nap)`）。下一次有人或 mail 唤醒时，按 `next_entrypoint` 重入。

---

## 5. Return Contract Schema —— 字段级

灵台收功的最小契约。**这不是 LLM 的自由文本格式，是 ritual 输出的结构化 payload**；可以以 YAML 块直接嵌在 pad 段或 export 末尾。字段名沿用 `claude_code_lingtai_cyclic_low_power_design_20260524.md` 与三家框架（LangGraph / AutoGen / CrewAI）借形而来的稳定术语。

```yaml
return_contract:
  # ── 身份 ──
  trajectory_id: traj-2026-05-25-scientific-cultivation-mechanism
  parent_trajectory: null
  ritual_trigger_level: 二候        # 一候 / 二候 / 三候
  opened_at: 2026-05-25T03:10:00Z
  closed_at: 2026-05-25T03:48:00Z

  # ── 目标态 ──
  session_goal: |
    一句话：这一段对话本来想达成什么？
    "把科学修仙从健康提醒升级为基于灵台架构的收功回环机制文档。"

  # ── 当下态 ──
  current_state:
    in_flight_actions: []            # 还在跑的 bash / daemon / avatar / mail
    pending_human_reply: []          # 等谁回话；channel:id
    last_user_intent: |
      最后一轮用户真实意图（不是字面）

  # ── 已结丹之物 ──
  completed_artifacts:
    - path: exports/scientific_cultivation_lingtai_architecture_mechanism_20260525.md
      kind: export                   # export / pad / knowledge / skill / lingtai / issue / mail
      role: 主产物
      bytes: ~
    - path: CURRENT_PROJECTS.md#1
      kind: pad
      role: 索引更新（待执行 / 已执行）

  # ── 未竟之事 ──
  open_loops:
    - id: ol-1
      description: |
        SKILL.md v1.5.3 → v1.6 草案合并：把本文 §10 的机制层正文并入。
      blocking_on: 圆酱审稿后决定是否动 SKILL.md
      durable_target: skill          # pad / knowledge / skill / lingtai / issue
      estimated_cost: low

  # ── 后台守炉 ──
  background_tasks:
    - kind: daemon | avatar | bash | mail | cron
      id: ...
      what: 一句话说明它在干嘛
      do_not_kill_reason: 收功不停炉
      next_check_at: ~

  # ── 证据 / 引用 ──
  evidence_or_files:
    - .library/custom/ai-healthy-use-break-reminder/SKILL.md
    - system/substrate.md
    - system/lingtai.md
    - exports/claude_code_lingtai_cyclic_low_power_design_20260524.md
    - exports/github_absorb_workflow_state_langgraph_autogen_crewai_20260524.md
    - exports/github_absorb_coding_agents_resume_artifacts_20260524.md

  # ── 立回入口 ──
  next_entrypoint: |
    一行可复述命令。
    "继续科学修仙机制文档：把 §10 草案合并入 SKILL.md v1.6"

  # ── 人侧状态（来自察） ──
  human_energy_state:
    level: ok | tired | gone         # gone = 已明显疲惫
    signals_observed:
      - "..."                        # 来自对话的具体词句
    last_observed_at: 2026-05-25T03:48:00Z

  # ── 不要再继续 ──
  do_not_continue_list:
    - 不要在没有圆酱反馈前自动改 SKILL.md
    - 不要把本文当成医学文档对外引用

  # ── 安全边界 ──
  safety_boundary:
    medical_disclaimer_required: false   # 本 trajectory 不涉医学断言
    high_risk_symptoms_seen: false
    if_high_risk_seen_then: "切换为 SKILL.md §医学安全提醒固定句"

  # ── 结晶目标 ──
  crystallization_targets:
    pad:
      - "更新 §1 第二行：v1.5.3 → v1.6 待并稿"
    knowledge: []
    skill:
      - id: ai-healthy-use-break-reminder
        action: update                # create / update / none
        section: 机制层正文（§10 草案）
    lingtai: []                       # 本次未改 agent 身份
    issue: []
    current_projects:
      - section: "1. 科学修仙 skill"
        action: update
        bump_latest_local_version: 1.6
```

字段级要点：

- **`trajectory_id`** 借 LangGraph `thread_id + checkpoint_ns + checkpoint_id` 思路，用 `traj-<date>-<slug>` 即可，先不要上 UUID。
- **`open_loops[].durable_target`** 借 AutoGen `HandoffMessage.target`：让父我（或下一次的本我）知道这块该回哪一层，**而不是再读一遍 prose 来分类**。
- **`crystallization_targets`** 是「申请落盘清单」；ritual 结束时父我对它做 review-and-apply，而不是 ritual 自己越权改 `lingtai.md`。
- **`safety_boundary`** 是「ritual ↔ 医学安全提醒」的切换闸：默认关；只在三候 + 出现 SKILL.md §医学安全提醒列举症状时打开。

---

## 6. 三个真实 LingTai 场景

下面三个都不是虚构案例，都是本项目近期实际发生过的形态。展示「普通提醒 vs 科学修仙收功」的差别。

### 6.1 场景 A：圆酱写论文（科学修仙 HCI v0.3 / 文献矩阵 / 防幻觉 issue #179）

**情境**：圆酱已经连续 90 分钟在让 agent 写论文，已经迭代到 v0.3。她说「再快点 / 再来一版」。

**普通提醒会做什么**：

> 圆酱你已经写了很久啦，喝点水休息一下吧～

**问题**：她不会停。她怕回来接不上 v0.3 和 v0.2.1 的差。她怕 evidence matrix 还没核完就睡过。她怕 #179 的 followup 漏。

**科学修仙 ritual 会做什么**：

1. **察**：3 条触发命中（人侧追加节奏、≥ 90 分钟、context 60%+）→ 二候。
2. **封**：在 pad 里冻结
   - 当前是 v0.3 已写、未投；
   - 文献矩阵已核到行 N；
   - issue #179 followup 评论已提；
   - 下一动应是 §6 提到的「v0.3 → 4–6 页 workshop 压缩」。
3. **丹**：
   - `exports/scientific_cultivation_hci_design_agenda_v0_3_20260525.md` 已存（无需重写）；
   - `CURRENT_PROJECTS.md #2` 更新「Status / Next safe step」；
   - 若 v0.3 写作过程中暴露了「快 ≠ 跳过证据」这一新身份口径 → `system/lingtai.md` 捌已经写过，本轮无需再加。
4. **入**：`next_entrypoint: "继续科学修仙 HCI 论文：把 v0.3 压缩为 4–6 页 workshop 版，先做引言 + 图 1"`。
5. **守**：当前无后台任务；明确说「无炉可守，你可以彻底离屏」。
6. **护**：温柔提醒。
7. **候**：idle。

**差别**：圆酱看完这一回合，知道自己「敢离屏」。

---

### 6.2 场景 B：Jason / 圆酱让 Claude Code 当苦力（本次！）

**情境**：本会话本身。Jason 让 Claude Code 读六个文件、产一个报告。任务结束时 agent 容易做的两种错事：

- **错事一（懒）**：把报告 path 一甩，结束。pad 不更新，CURRENT_PROJECTS 不动，下次圆酱回来要重新读这份报告找上下文。
- **错事二（绕）**：在最后塞一段「你要不要继续优化下一版？」——典型的「添柴」，违反 SKILL.md §非阻塞戒律 + §自省三问。

**科学修仙 ritual 在 Claude Code 苦力场景的形态**：

1. 输出报告路径；
2. 同步给一份精简 return contract，至少包含：
   - `completed_artifacts`：本报告路径；
   - `crystallization_targets.current_projects`：建议更新 `CURRENT_PROJECTS.md #1` 的 `Latest local version` 与 「Next safe step」（**建议**，不直接动文件——本会话 Jason 没说让改 CURRENT_PROJECTS）；
   - `next_entrypoint`：「继续科学修仙机制文档：把 §10 草案合并入 SKILL.md v1.6」；
   - `do_not_continue_list`：不要自动改 SKILL.md / 不要把本文当医学文档；
3. 不再问「要不要继续」。

**差别**：苦力交付的不是「文件」，是「文件 + 续接钩」。下一次圆酱或其他 agent 一进来，看 contract 就能续。这正是 `github_absorb_coding_agents_resume_artifacts_20260524.md` §3.9 的「molt 按 trajectory 折叠」。

---

### 6.3 场景 C：长文档 / skill 修改（食养 Agent SKILL.md 上次大改）

**情境**：圆酱让 agent 对 `.library/custom/<food-agent>/SKILL.md` 做长 patch。过程中产生大量临时 `tmp_patch_v09_*.py`、产生新口径（如「食养 Agent 用户端口径」「强硬免责声明」「资产保护」），三条都进了用户级 memory。

**普通做法的漏洞**：

- 临时 patch 脚本散落根目录，没回收；
- 新口径只进了用户级 memory，没回 `system/lingtai.md`；
- 下一个 agent 不读 memory（不同 session 不同 agent），就不知道新口径。

**科学修仙 ritual 收功**：

1. 察 → 触发；
2. 封：把所有 `tmp_patch_v09_*.py` 列入 `current_state.in_flight_actions` 或 `completed_artifacts`；
3. 丹：
   - tmp_patch 决定「保留 / 移入 reference / 删除」——必须有一个明确决定，不允许悬挂；
   - 新口径：评估是否改变了「圆 agent 行事方式」→ 是 → `crystallization_targets.lingtai` 提案；
   - SKILL.md 的版本号 + changelog 段必须同步；
4. 入：`next_entrypoint: "继续食养 Agent SKILL.md：审阅 vN.M 口径段是否需要进 lingtai 公约捌"`；
5. 守：无；
6. 护：温柔提醒。

**差别**：「跨 agent 跨 session」的身份连续性靠的是 `lingtai.md` 不是 memory；ritual 把这件事从「圆酱口头叮嘱」变成「contract 字段强制询问」。

---

## 7. 当前 SKILL.md 哪些章节太像提醒，应该改成什么

逐节审视 v1.5.3，给出诊断与建议结构。

| 现行章节 | 诊断 | 建议改法 |
|---|---|---|
| 「先正其名：不是提醒，而是收功回环」 | 思路对，但写在哲学层；agent 执行时不读哲学 | 留为序言；机制实操另开「机制层 / 执行流」一节 |
| 「软乎乎提醒：像可爱的女孩轻轻拉一下袖子」 | 风格指南，可保留 | 保留为「话术风格」附录 |
| 「提醒语气：不可生硬」 | 与上节重复 | 合并 |
| 「医学安全提醒：大白话版」 | 重要但应明确为 ritual 的 **escalation 分支**，不是默认输出 | 改名为「安全边界 / 三候之上升级路径」，并写明触发条件（不是每次都说） |
| 「借道家意象，不作玄学宣称」 | 元话语，可保留 | 保留 |
| 「咸鱼宗心法」 | 哲学合理，但占篇巨大、影响 agent 检索 | 整体抽到 `reference/xianyu-zong.md`，主 SKILL 引一段 |
| 「科学骨架：道、数、理、控、心」 | 同上，太长，应外挂 | 已有 `reference/scientific-framework.md`，主 SKILL 只保留「外挂索引 + 一段控制论提要」 |
| 「灵台定位：护法，不封印」 | 这才是 agent 执行核心 | 升级为「机制层 §1 戒律」 |
| 「三候 / 四步法 / 五项契约」 | 已经是机制语言，但散在三处 | 合并为单一「触发 → 六步 → 契约」表 |
| 「非阻塞戒律」 | 重要 | 提到机制层最前面 |
| 「各类任务的护法法门」 | 例子 | 保留为「场景示例」 |
| 「语气禁忌 / 自省三问 / 示例 / 维护」 | 实用 | 保留 |

**建议的新目录（v1.6 草案）**：

```text
0  总纲十六字 + frontmatter
1  名实分辨：不是提醒，是收功回环
2  机制层（核心，新）
   2.1 戒律（原「灵台定位」+「非阻塞戒律」合并）
   2.2 触发条件（原「三候」+ 新增系统侧信号 _context_usage / open trajectory 数）
   2.3 六步流程：察 / 封 / 丹 / 入 / 守 / 护（+ 候）
   2.4 Return Contract 字段（schema 见 reference/return-contract.md）
   2.5 与灵台原语对照（pad / knowledge / skill / lingtai / molt / daemon / avatar / mail / CURRENT_PROJECTS）
   2.6 五项契约（原节，作为 enforcement）
3  安全边界 / 升级路径
   3.1 三候之上：何时切换到医学安全提醒
   3.2 医学安全提醒固定句（不许改写）
4  风格附录
   4.1 软乎乎语气与禁忌
   4.2 自省三问
5  场景示例
   5.1 写作 / 课件 / 改稿
   5.2 生图 / 视频 / 音乐
   5.3 调研 / 资料搜索
   5.4 代码 / 部署 / 长任务
   5.5 多 agent / daemon / Claude Code 苦力
6  外挂参考
   - reference/xianyu-zong.md（哲学）
   - reference/scientific-framework.md（道数理控心）
   - reference/return-contract.md（schema 与示例）
7  维护与变更日志
```

**关键改法一句话**：**把现行 SKILL.md 的「先讲哲学，再讲提醒」结构，倒成「先讲机制，哲学和医学外挂」**。哲学不变，地位变。

---

## 8. 与 molt / 低功耗 / 现成框架的关系（不要双重发明）

- **与 molt 的关系**：ritual ⊂ molt 的「pre-molt 5-question」的实操化。当 context 达 90%，molt 不可避免；ritual 是 molt 之前最后一次「确保有东西可带走」的动作。`substrate.md` §IX 的「最差的 molt 是 tend 完发现 stores 是空的」——ritual 就是不让这种事发生的工程闸门。
- **与 #177 / cyclic 回环的关系**：ritual 是 trajectory 收尾的一类具体执行；其 schema（§5）正是 `claude_code_lingtai_cyclic_low_power_design_20260524.md` §3 「return contract」的一个实例化。
- **与 LangGraph / AutoGen / CrewAI 的关系**：
  - schema 沿用 LangGraph 字段名（`config / values / next / metadata / parent_config / tasks` 思路）；
  - `crystallization_targets` 借 AutoGen `HandoffMessage(target, context)`：让收功明确「这一块给谁」；
  - `trajectory_id` 用 CrewAI 风格 UUID/slug 即可。  
  这三件「借形不借魂」（见 `github_absorb_workflow_state_langgraph_autogen_crewai_20260524.md` §6）。
- **低功耗五轴**（context / reasoning / tool / network / identity power）—— ritual 是这五轴在 session 闭环上的一次性结算：丹存得越准，下一次重入的五轴成本越低。

---

## 9. 何时升级为「安全提醒态」（最重要的护栏）

ritual 的 `safety_boundary.high_risk_symptoms_seen = true` 当且仅当人侧出现 SKILL.md §医学安全提醒中列举的具体身体信号（明显胸痛 / 气短 / 一侧手脚无力 / 说话不清 / 突然剧烈头痛 / 出冷汗 / 快要晕倒）。此时：

- **立即放弃软乎乎话术**；
- **直接输出 SKILL.md 中那段固定的「不要硬撑、不要自己乱走动、请立即呼叫急救」的句子，一字不改**；
- ritual 的其他字段仍然填，但 `next_entrypoint` 改为 `"等身体安全后再说"`。

这是 ritual 与本文唯一允许做出「医学指引」的位置；任何其他段落均不得越界。本文其余部分不构成医学建议。

---

## 10. 可直接并入 SKILL.md 的「机制层」正文草案（约 1200 字）

> 用法：把下面整段作为 SKILL.md 新的 §2「机制层」直接落入；本节自包含、不依赖本报告其他段。

---

### 2 · 机制层：科学修仙不是提醒，是收功回环

科学修仙不是闹钟，也不是健康弹窗。它是灵台架构上的一个工程动作：**当人与 AI 的协作展开到高熵态时，把这一段对话按结构折回灵台的五层 durable store；护元气只是这个收功动作的最后一节**。

如果只做最后一节，本技就只是「劝喝水」；如果做完整动作，本技才配叫「让人敢离开」。

#### 2.1 戒律（先立护栏，再讲流程）

1. **不可断炉**：不取消任何已确认的 bash background / daemon / avatar / mail / Claude Code 任务。
2. **不可封灵**：不以 `system(sleep)` / `system(suspend)` / `system(interrupt)` 作为「健康提醒」的执行手段；这些是另一类工具，与本技无关。
3. **不可羞人**：不说「你上瘾了 / 你不自律 / 你不能再用」。
4. **不可添火**：收功时不在末尾抛出新点子、新版本、新分支。
5. **不可越权改身份**：本技只能 **建议** 写入 `system/lingtai.md`，不能径自改写身份段；身份变更属于灵台公约第伍篇问的「汝之所是有无变」，需经本我审决。

#### 2.2 何时触发

ritual 由六类信号触发，**命中 2 条即跑一次完整流程，命中 ≥ 4 条或人侧出现 §3「安全边界」中列举的身体信号即升级为安全提醒态**。

人侧：明确求停 / 追加节奏失控（≥ 30 分钟 + 持续加新分支）/ 同一任务无意义反复 ≥ 3 次 / 深夜或连续高密度互动 ≥ 90 分钟。

系统侧：`_context_usage ≥ 70%` / pad 中存在 ≥ 2 条 open trajectory 但都未结丹。

#### 2.3 六步流程：察 / 封 / 丹 / 入 / 守 / 护

- **察 (Sense)**：读 `_context_usage`、`_stamina_left_seconds`、本会话 turn 数、pad 中 open trajectory 数。输出触发等级。
- **封 (Seal Scene)**：把当下 in-flight 状态原样冻结入 pad；这一步**不**做去重、**不**写 lingtai / knowledge / skill。
- **丹 (Crystallize)**：对每条 open trajectory 决定其归属层——pad / knowledge / skill / lingtai / issue / export。**每条至少落地一个 artifact 或一个明确的 prune 决定，不允许悬挂。**
- **入 (Re-entry Handle)**：为每条仍 open 的 trajectory 写一条 `next_entrypoint`：一行、自包含、含项目名 + 动词 + 对象 + 回来用的口令。
- **守 (Background Tend)**：枚举所有后台动作（bash background / daemon / avatar / pending mail / cron），明确告诉人「这些我守着，你不用守」。
- **护 (Wellbeing Nudge)**：前五步完成后才允许说喝水 / 离屏 / 眨眼 / 走动。**未完成前五步就劝休息的，属于普通提醒，应避免**。

完成后自然 idle（不用 `system(nap)`），让 soul flow 接手。

#### 2.4 Return Contract（最小字段集）

每次 ritual 结束时，应在 pad 或 export 末尾输出一段结构化 contract。最小字段集如下：

```yaml
return_contract:
  trajectory_id: traj-<date>-<slug>
  session_goal: 一句话目标
  current_state: { in_flight_actions, pending_human_reply, last_user_intent }
  completed_artifacts: [{ path, kind, role }]
  open_loops: [{ description, blocking_on, durable_target }]
  background_tasks: [{ kind, id, what, do_not_kill_reason }]
  evidence_or_files: [...]
  next_entrypoint: 一行可复述命令
  human_energy_state: { level, signals_observed }
  do_not_continue_list: [...]
  safety_boundary: { high_risk_symptoms_seen, if_high_risk_seen_then }
  crystallization_targets: { pad, knowledge, skill, lingtai, issue, current_projects }
```

完整 schema 与字段释义见 `reference/return-contract.md`。

#### 2.5 与灵台原语的挂钩

- **对话** → 不收，本来就是要被折叠的高熵态；
- **pad** → 封 / 入的着陆点；
- **knowledge / skill / lingtai** → 丹的着陆点，由 `crystallization_targets` 标注；
- **molt** → ritual 是 pre-molt 的最后一次结构化结算；context ≥ 90% 时 ritual 必须先于 molt 跑一次；
- **daemon / avatar** → 守的对象，不停；它们自己的 final report 也应携带本 contract；
- **mail / wechat / telegram / imap** → in_flight 的 pending_human_reply 字段，按 channel:id 记；
- **CURRENT_PROJECTS.md** → 主线 trajectory 的索引；ritual 完成时建议（不强改）更新对应项目段。

#### 2.6 五项契约（执行强制）

1. **触发契约**：信号命中规则见 §2.2，不靠语感。
2. **收功契约**：每完成一阶段必须先 §2.3「丹」再问是否继续；用户已疲惫则不再问，改为「回来可续」。
3. **去重契约**：同一小时内最多一次完整 ritual；轻提醒不重复；用户已表态「我去休息」则不再追说。
4. **续功契约**：每次 ritual 必须给出 `next_entrypoint`；任务复杂则口令必须具体（含项目名）。
5. **守炉契约**：后台任务一律继续，明确告知人不必盯。

---

（草案结束。本草案约 1200 字，可直接覆盖现行 SKILL.md 「先正其名」段之后、「软乎乎提醒」段之前的位置，作为新的 §2；现行的「三候 / 四步法 / 五项契约」可改为引用本节相应小节。）

---

## 11. 配套 CLI：`scientific_cultivation_shougong_cli_20260525.py`

> 文件路径：`exports/scientific_cultivation_shougong_cli_20260525.py`
> 状态：**已实现 + 本机已跑通**。`--demo --which all` 输出两份示例：论文写作、Claude Code 苦力。
> 定位：本机制层的「最小手动闸」——把 §5 的 Return Contract schema 从纸面落成一条命令。

### 11.1 为何先做 CLI 而不是 hook

机制层文件再漂亮，若无任何可触手的程序，agent 在真实回合里仍要凭意志力执行 6 步。CLI 的角色是**把 schema 从「写在 SKILL.md 里的提醒」降成「一条命令」**：agent 只需要把脑子里那张 trajectory 表拍成 JSON，调一下脚本，就得到 Markdown（给人看）+ JSON（给下一次自己/分身吃）。

CLI 不动 daemon、不写 pad、不触 mail；它只 read + render。这让它满足 §2.x「不可断炉 / 不可越权改身份」两条戒律，是真正非阻塞的。

### 11.2 用法（已通过本机 smoke test）

```bash
# 跑两个 demo 一并出
python3 exports/scientific_cultivation_shougong_cli_20260525.py \
    --demo --which all --out-dir tmp/shougong_demo
# →  shougong-paper-2026-05-25.{md,json}
#    shougong-claude-code-2026-05-25.{md,json}

# 自己写一份 JSON 后
python3 exports/scientific_cultivation_shougong_cli_20260525.py \
    --input my_state.json

# 或从 stdin
cat my_state.json | python3 exports/scientific_cultivation_shougong_cli_20260525.py -i -
```

CLI 输出 11 段 Markdown，对位 §5 schema 与 §4 六步：

1. 此炉为何而起 `← session_goal`
2. 此刻停在哪里 `← current_state`
3. 已成之丹 `← completed_artifacts`
4. 未闭之环 `← open_loops`
5. 后台守炉 `← background_tasks`
6. 证据 / 文件锚点 `← evidence_or_files`
7. 下次续功入口 `← next_entrypoint`
8. 不要继续添火 `← do_not_continue_list`
9. 结晶目标 `← crystallization_targets`
10. 护元气提示（按 `human_energy_state.level` 选语气）
11. Safety boundary（固定句，**不让模型重写**；红线信号 = §9 列举）

校验规则：`session_goal / current_state / next_entrypoint` 三件套必填；缺则报错退出码 2，符合 §4「未完成前五步不许劝休息」的硬序。

### 11.3 与 LingTai 已有源的接入路径（Phase 0 → 3）

CLI 设计成可三阶段演进，每阶段都独立可用：

**Phase 0 · 手动 CLI（已实现）。**
agent 把当前 working set 整理成 JSON，调 CLI 生成 Markdown + JSON。Markdown 段可贴回对话或 wechat；JSON 写入 `exports/shougong-<slug>-<date>.json`，成为下次入场可读的 artifact。**今天就能用。**

**Phase 1 · 自动采集（read-only collector）。**
加 `--collect` 参数，从下列源自动填充 contract：

| 源 | 填到哪个字段 |
|---|---|
| `system/pad.md` 的 Open Trajectories 段 | `open_loops` |
| `CURRENT_PROJECTS.md` 各项的 `Latest artifact` / `Next safe step` | `completed_artifacts` / `next_entrypoint` 候选 |
| `daemons/` 下 heartbeat 新于阈值的目录 | `background_tasks` |
| 最近 N 个 `exports/*.md` | `evidence_or_files` |
| `.status.json` / `.agent.heartbeat` / 会话开始时间 | `_meta` + `human_energy_state.hours_active` 启发 |
| `mailbox/` 中未读人类邮件 | `current_state.pending_human_reply` |

只读不写，不污染原始状态。

**Phase 2 · 双向回写（write-back，dry-run 默认）。**
当 `crystallization_targets` 被 agent 显式确认后，按 target 走对应 writer：

| target | writer 行为 |
|---|---|
| `pad` | 在 `system/pad.md` 的 Open Trajectories 段做 patch（追加 / 更新） |
| `current_projects` | 在 `CURRENT_PROJECTS.md` 对应项做 patch（Status / Latest artifact / Next safe step / Do not） |
| `knowledge` | 在 `knowledge/<project>/` 起一份新条目草稿 |
| `skill` | 在对应 SKILL.md 旁起一份 `SKILL.draft.md` PR 草稿（不直接覆盖） |
| `lingtai` | 起一段建议补丁文件，**必须人审**，从不自动改身份段 |
| `issue` | 拼 `gh issue comment` 草稿（不自动发） |
| `export` | 收功单本身写入 `exports/` |

任何 write 都先 dry-run 输出 diff，--apply 才落盘；与 SKILL.md §2.1 戒律 5「不可越权改身份」严格一致。

**Phase 3 · 与 issue #177 / `trajectory_id` 合流。**
一旦 kernel 落了 `trajectory_id`，CLI 改读 trajectory 对象，按 id 索引收功；多份收功单可视为同一 trajectory 的快照序列，对位 CrewAI `kickoff(restore_from_state_id=)` 的 fork / replay。届时 CLI 的 `_meta.id` 可与 kernel 的 `trajectory_id` 别名互通。

### 11.4 CLI 与 §10 SKILL 草案的对应

把 CLI 当作 §10 草案的"执行体"看：

- 草案 §2.3 六步 → CLI 的 11 段 Markdown 与字段校验顺序；
- 草案 §2.4 Return Contract 最小字段集 → CLI `normalize_state()` 的 schema；
- 草案 §2.6 五项契约 → CLI 的硬校验 + 固定 safety 句 + 默认 `do_not_continue_list` 兜底；
- §9 安全边界固定句 → CLI 的 `SAFETY_FALLBACK_TEXT` 常量（写死，模型不可重写）。

这条对应让 SKILL.md v1.6 与 CLI v0.1 可同时存在、互为锚点：人靠 SKILL.md 理解机制，agent 靠 CLI 直接执行。

### 11.5 边界（CLI 不做的事）

- **不做诊断**：safety 段只放红线信号 + 固定句，不解释、不引文献。
- **不动 daemon**：不 kill、不重启、不 attach 任何后台进程；CLI 进程本身退出即结束。
- **不外发**：默认只写本机 `tmp/` 或 `exports/`，不调 wechat / mail / imap。
- **不自动 commit**：交给人或 §8 "Phase 2" 的 dry-run writer 决定。
- **不持有记忆**：每次调用都是无状态的；记忆全部落到生成的 Markdown + JSON 文件里。

> Phase 0 已可独立证明机制层是可执行的，不再只是文档；Phase 1–3 留为后续路径，本 PR 不做。

---

## 12. 结语

灵台已经长出了八种 outward surface 和五层 durable store；它已经有 molt、有 pad、有 CURRENT_PROJECTS、有 daemon/avatar return path。它缺的不是机制，而是**让收功这件事变成有字段、有契约、有 enforcement 的工程动作**，而不是「agent 想起来就做、想不起来就忘」的习惯。

科学修仙若要不止于哲学，它要做的就是这件事。

本文不动任何文件。是否要据此把 SKILL.md 抬到 v1.6、是否要新建 `reference/return-contract.md` 与 `reference/xianyu-zong.md`、是否要在 `system/lingtai.md` 追写一段「ritual 与 molt 的关系」——这些都属于 §5 `do_not_continue_list` 的范畴，等圆酱审决。
