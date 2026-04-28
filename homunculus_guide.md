# Homunculus 使用文档

> Homunculus 是一个 **Claude Code 插件（Plugin）**——通过插件市场安装，内部由一组 skills + hooks + 本地文件系统约定组成。它在本地观察你和 Claude 的协作模式，自动学习行为习惯，沉淀成可复用的偏好与能力，最终能孵化出专属的 agent / skill / command。
>
> 不是云端服务，不是 MCP server，**也不是单独的 skill**。它是一个标准的 Claude Code Plugin，所有数据落在你电脑上。
>
> GitHub 源：[humanplane/homunculus](https://github.com/humanplane/homunculus)

---

## 目录

- [一、它是什么](#一它是什么)
- [二、安装](#二安装)
- [三、目录结构](#三目录结构)
- [四、核心概念：observation → instinct → evolved](#四核心概念observation--instinct--evolved)
- [五、命令参考](#五命令参考)
- [六、典型使用流程](#六典型使用流程)
- [七、最佳实践](#七最佳实践)
- [八、常见问题与坑](#八常见问题与坑)
- [九、跨设备迁移](#九跨设备迁移)

---

## 一、它是什么

Homunculus = "小人儿"，源自炼金术里那个被造出来、慢慢长大的小生命。

它解决的痛点：**Claude 每个会话都是失忆的，你的偏好、踩过的坑、约定的流程，每次都要重讲。**

它的解法：

1. 你正常用 Claude（不需要刻意"教学"）。
2. **插件里的 hooks 自动**捕获每次 prompt 和 tool use，落到本地的 `observations.jsonl`——不靠 Claude 自觉记录。
3. 一个后台 observer 子代理把原始观察提炼成**有名字的 instinct**（行为模式）。
4. 当某类 instinct 攒够、形成簇，可以**进化**成专属的 agent / skill / slash command，落到 `.claude/homunculus/evolved/`。

关键架构：**Plugin = Skills + Hooks + 文件约定**。Skills 提供 `/homunculus:*` 命令；Hooks 把行为数据灌进 observations；文件约定（`.claude/homunculus/`）是状态存储。三者缺一不可——所以必须按插件的方式装，单独 copy skill 不行。

跟 Claude 内置的 auto-memory 的区别：

| 维度 | auto-memory | homunculus |
|---|---|---|
| 形态 | 一组 markdown 备忘 | 分层结构：raw log → instinct → evolved capability |
| 数据采集 | Claude 主动写 | **Hooks 自动捕获每次 prompt + tool use** |
| 提炼 | 不提炼 | observer 子代理周期性提炼成 instinct |
| 终点 | 文本记录 | 可孵化成可调用的 agent / skill / command |
| 范围 | 用户级 | 工作目录级（每个项目可以有自己的小人儿） |
| 共享 | 不易共享 | 支持 export / import |

两者**可以共存**，事实上推荐共存——auto-memory 抓显式偏好，homunculus 抓行为模式 + 进化成能力。

---

## 二、安装

Homunculus 是 Claude Code Plugin。前置：已安装 Claude Code（且版本支持 plugin marketplace）。

### 步骤 1：添加插件市场

在 Claude Code 里运行：

```
/plugin marketplace add humanplane/homunculus
```

把作者的 GitHub 仓库注册成一个本地可见的插件市场。

### 步骤 2：安装插件

```
/plugin install homunculus@humanplane-homunculus
```

会从刚才注册的市场里把 homunculus 拉下来安装。装完插件里携带的 skills 和 hooks 会进入待激活状态。

### 步骤 3：重载插件

```
/reload-plugins
```

**这一步不能省**——hooks 必须经过 reload 才会生效，跳过的话后续 observations 不会被自动采集，homunculus 等于失效。

### 步骤 4：诞生你的 homunculus

进入你想绑定的工作目录（项目根目录最佳），运行：

```
/homunculus:init
```

第一次运行会：

1. 检查 `.claude/homunculus/identity.json` 是否存在。
2. 不存在 → 走"诞生"流程：问你在做什么、你的技术水平偏好（technical / semi-technical / non-technical / chaotic），然后创建文件夹结构和 `identity.json`。
3. 存在 → 走"唤醒"流程，加载历史。

### 步骤 5：（可选）每次会话开始时加载历史

```
/homunculus:session-memory
```

会派 observer 子代理把累积的 observations 提炼成 instincts，并把相关上下文塞进当前会话。建议在新会话开头跑一次。

### 安装后验证

```
/plugin list                # 确认 homunculus 在列
/homunculus:status          # 看身份卡能否读出来
```

如果 `/homunculus:*` 命令找不到，多半是 reload-plugins 没跑或没生效——重启 Claude Code 再试。

---

## 三、目录结构

诞生后，工作目录下会出现：

```
.claude/homunculus/
├── identity.json                   # 身份卡：项目名、级别、journey、统计数
├── observations.jsonl              # 原始观察日志（每行一条 JSON）
├── sessions/                       # 历史会话快照（可选）
├── instincts/
│   ├── personal/                   # observer 从 observations 提炼出的 instinct
│   └── inherited/                  # 通过 import 从别处拿来的 instinct
└── evolved/                        # 进化成型的能力
    ├── agents/ 					# 专职子 Agent（有独立角色和工具配置）
    ├── skills/						# 可复用的能力片段（怎么做某件事）
    └── commands/					# 可触发的具体指令（做什么）
```

### identity.json 字段

```json
{
  "version": "2.0.0",
  "project": {
    "name": "项目名",
    "description": "一句话说明",
    "born": "ISO 时间戳"
  },
  "creator": {
    "level": "technical | semi-technical | non-technical | chaotic"
  },
  "journey": {
    "milestones": [],         // 重要节点
    "sessionCount": 0,
    "lastSession": null
  },
  "homunculus": {
    "evolved": [],            // 已孵化的能力名单
    "awakened": "ISO 时间戳"
  },
  "instincts": {
    "personal": 0,
    "inherited": 0
  },
  "evolution": {
    "ready": []               // 准备进化的 instinct 簇
  },
  "lastAnalysis": null        // 上次 observer 跑的时间
}
```

---

## 四、核心概念：observation → instinct → evolved

三层抽象，从粗到精：

### Observation（观察）

- **是什么**：原始日志条目，存在 `observations.jsonl`，JSONL 格式（每行一个 JSON）。
- **谁写**：**插件里的 hooks 自动写**——每次你提交 prompt、Claude 调用 tool，hook 都会捕获并落一行。这是被动采集，不依赖 Claude 自觉。
- **额外补充**：Claude 也会在察觉到明确约定、纠正、用户偏好时主动追加结构化条目（例如 `type: workflow_rule`），作为 hook 自动采集之外的补充。
- **示例**：

```json
{"ts":"2026-04-27T06:30:55Z","type":"workflow_rule","scope":"internal-web","rule":"git commit 前必须 cd frontend && npm run build","source":"user_explicit"}
{"ts":"2026-04-27T07:12:03Z","type":"preference","scope":"rag","rule":"用户偏好 LangChain 而非 LlamaIndex 做检索","source":"inferred"}
```

### Instinct（本能）

- **是什么**：观察被提炼后形成的命名好的行为模式，单文件一条，存在 `instincts/personal/` 或 `instincts/inherited/`。
- **谁写**：observer 子代理（在 `/homunculus:session-memory` 或 `/homunculus:observer` 时触发）。
- **作用**：下次开会话、干活前，`/homunculus:instinct-apply` 会把相关 instinct 拉出来贴到当前任务上下文。

### Evolved（进化能力）

- **是什么**：当某个 instinct 簇足够稳定且高频，孵化成完整的 agent / skill / command，能被你直接调用。
- **谁写**：`/homunculus:evolve` 触发，由 Claude 设计并写入 `.claude/homunculus/evolved/`。
- **示例**：你反复让 Claude "在提交前跑 build + 检查 dist + 提交" → 进化成一个 `/commit-frontend` slash command。

提炼链路：

```
[你正常工作]
   ↓ Claude 在 observations.jsonl 里记关键点
[observations.jsonl]
   ↓ /homunculus:session-memory 触发 observer
[instincts/personal/*.md]
   ↓ /homunculus:status 提示某簇 ready
[evolution.ready]
   ↓ /homunculus:evolve
[evolved/agents/ | skills/ | commands/]
```

---

## 五、命令参考

| 命令 | 作用 | 何时用 |
|---|---|---|
| `/homunculus:init` | 诞生或唤醒 | 第一次进项目，或换设备后第一次 |
| `/homunculus:session-memory` | 加载历史 + 跑 observer 提炼 | 每次新会话开头建议跑一次 |
| `/homunculus:status` | 看身份、observation 数、instinct 数、是否 ready evolve | 想看进展 / 排查"它学到什么没" |
| `/homunculus:instinct-apply` | 把相关 instinct 贴到当前任务 | 干活前主动调，让 Claude 带着 instinct 干 |
| `/homunculus:evolve` | 把 ready 的 instinct 簇孵化成能力 | status 提示 ready 时 |
| `/homunculus:export` | 导出 instincts 为可分享文件 | 备份 / 分享给同事 / 跨设备 |
| `/homunculus:import` | 导入别人的 instincts 到 inherited/ | 拿到同事的 instinct 包时 |

后台还有一个：

| Agent | 作用 |
|---|---|
| `homunculus:observer` | 后台分析器，读 observations、生成 instincts、检测簇。被 session-memory 自动调用，也可手动触发。 |

---

## 六、典型使用流程

### 场景 A：第一次给项目配 homunculus

```
cd 你的项目根目录
/homunculus:init
# 回答 Claude 的提问：在做什么、技术水平偏好
# 文件结构和 identity.json 自动生成
```

之后正常干活。Claude 会在合适时机往 `observations.jsonl` 记东西。

### 场景 B：日常工作流

```
[新会话开始]
/homunculus:session-memory     # 加载历史 + 提炼
[正常干活，提需求 / 写代码 / 调 bug]
[Claude 带着 instinct 工作]
[会话结束，新观察落到 observations.jsonl]
```

### 场景 C：检查进展

```
/homunculus:status
# 输出示例：
# lowcode-rag. Session 12.
# 8 instincts. Evolution ready: frontend-commit (5 instincts clustered).
```

### 场景 D：让它进化出新能力

```
/homunculus:status
# 看到 "Evolution ready: frontend-commit"

/homunculus:evolve
# Claude 把 frontend-commit 簇里的 5 条 instinct 整合成一个 command/skill
# 落到 .claude/homunculus/evolved/commands/commit-frontend.md
# 之后你可以 /commit-frontend 直接调
```

### 场景 E：手动塞知识进去

如果有些规则你不想等 Claude 自己摸索，可以直接告诉它：

```
"内部系统 git commit 前必须先 cd frontend && npm run build。
原因：dist 是版本化资产，要随源码一起进仓库。"
```

Claude 会立刻把它写进 observations，并在 auto-memory 里也存一份。

---

## 七、最佳实践

### 1. 纠正时多说一句"为什么"

```
❌ "别用 mock"
✅ "别 mock 数据库，上次 mock 测试通过但生产 migration 挂了，必须用真库"
```

带原因的纠正才能沉淀成有判断力的 instinct，不带原因的只是死规矩。

### 2. 周期性 status

每隔 5–10 个会话喊一次 `/homunculus:status`，看它有没有跑偏。跑偏了就让 Claude 删掉错的 instinct。

### 3. 想要"铁律"用 hook，不靠 instinct

Instinct 是"Claude 主动遵守的约定"——不是机器拦截。如果某个规则**绝对不能漏**（比如"任何 git commit 前必须 build"），让 Claude 用 `update-config` skill 在 `settings.json` 里配 PreToolUse hook 拦 `git commit`。Hook 是 harness 强制的，instinct 漏不掉。

### 4. 不要每个项目都建 homunculus

它有维护成本（status / evolve 都要你主动管）。建议给"长期、反复回访、规则多"的项目建——一次性脚本不值得。

### 5. 项目级，不是用户级

`.claude/homunculus/` 在工作目录下，跨项目不共享。要共享得 export → import。

---

## 八、常见问题与坑

### Q1. 我什么都没干，observations.jsonl 没新条目，正常吗？

**不正常**。插件的 hooks 应该每次 prompt / tool use 都自动追加。如果完全没新条目，按这个顺序排查：

1. `/plugin list` 确认 homunculus 装上了。
2. 装了但不工作 → `/reload-plugins` 重载 hooks（这是最常见的原因）。
3. 还不行 → 重启 Claude Code。
4. 仍不行 → 检查工作目录是否真的有 `.claude/homunculus/identity.json`（hook 通常依赖身份卡存在）。

### Q2. observer 没自动跑，instinct 一直是 0

需要手动触发：`/homunculus:session-memory` 或直接调用 observer agent。observer 是按需跑的，不是后台守护进程。

### Q3. 进化出的能力质量不行怎么办

直接进 `.claude/homunculus/evolved/` 编辑或删掉文件。这是普通 markdown / agent 配置，可改可删。

### Q4. 误学了错的东西

`/homunculus:status` 看 instinct 列表 → 找到错的那个 → 直接 `rm .claude/homunculus/instincts/personal/<错的>.md`。或者让 Claude 帮你改。

### Q5. 它会不会偷偷把我的代码发出去？

不会。所有数据本地落盘，homunculus 不联网，不上传。只有你主动 `/homunculus:export` 才会生成可分享文件。

### Q6. 跟 CLAUDE.md / auto-memory 冲突吗？

不冲突，三者职责不同：

- **CLAUDE.md**：项目级人写的硬规则（架构、约定、跑测试命令）。Claude 每次都读。
- **auto-memory**：Claude 跨会话的偏好备忘（用户角色、feedback）。
- **homunculus**：分层、可孵化、可导出的本地能力系统。

冲突时优先级：CLAUDE.md > auto-memory > homunculus instinct > observation。

---

## 九、跨设备迁移

```
[源机器]
/homunculus:export
# 生成 .claude/homunculus/exports/<timestamp>.zip 之类

[拷贝到目标机器]

[目标机器]
cd 对应项目
/homunculus:init        # 先建身份
/homunculus:import <文件>
# instincts 落到 inherited/
```

**注意**：

- `observations.jsonl` 通常不导出（太多噪音）。导出的是已经提炼的 instinct。
- `evolved/` 下的能力可以单独 copy 过来，本质就是文件。
- `identity.json` 不要直接覆盖——每台机器有独立的 journey。
