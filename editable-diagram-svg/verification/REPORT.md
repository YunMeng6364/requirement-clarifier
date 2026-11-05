# 新技能创建与验证记录

本记录对应 `2026-11-05` 在 `D:/GitHub/skillhub/技能对比/editable-diagram-svg/` 创建的实际技能包。入口为 [SKILL.md](../SKILL.md)，按同级 `SVG技能融合方案.md` 已确认裁决实现；不是仅有方案或待填骨架。采用 `skill-creator` 的初始化、资源分层与独立前向演练流程。

## 已落地的能力

| 部分 | 实现 |
|---|---|
| 入口与流程 | 中文入口、任意格式适配、八种拓扑、三档细节；内容／布局／精确配色／装饰／回退合为一份提纲，批准后冻结 `acceptance.json` |
| 颜色 | `references/palette.json` 为两份源规范精确色值去重后的 **47 色白名单**；保留纯紫与紫色渐变端点，移除固定职责定色 |
| 视觉资源 | 汇报派的三个模板、17 个矢量图标与两个示例；清理非白名单色值，补齐对象 ID 和模拟验收清单 |
| 静态校验 | `scripts/validate_svg.py` 检查 SVG 结构、内部引用、可编辑文字、可见登记、冻结对象／关系／条件／文字／配色映射及白名单；旧关键词模式明确不能代替完整验收 |
| 几何辅助 | `scripts/svgkit.py` 从冻结清单显式构建；方法失败不部分修改累计部件，换行保留原文字，组容器不自动变成业务节点 |
| 实际渲染 | `scripts/render_svg.cjs` 使用已有 Playwright／浏览器，检查当前输入哈希、文字区域和实际 PNG；不自动安装依赖，不把截图存在等同于目视通过 |
| 最终写入 | `scripts/publish_svg.py` 在静态／渲染／目视证据完整且对应当前输入时原子写入；同字节不重复写，失败保留已有目标；支持受阻草稿和获批精确改色 |
| 交付与异常 | 区分事实／计划／假设／未知；三次同问题失败后采用已批准回退或提具体变更；检查分列四类，记录证据后清理本次预览与临时文件 |

没有加入 HTML、无限画布、主题系统、栅格主交付或外部字体下载。三个原技能目录的 **71 个文件 SHA-256 与创建前逐项一致**。源码来源与色值迁移见 [provenance.md](../references/provenance.md)。本次仅创建仓库内独立技能目录，未执行全局安装、打包、提交、上传或部署。

## 行为验证

| 检查 | 通过 | 失败 | 环境受阻 | 验证范围 |
|---|---:|---:|---:|---|
| `verification/exercise_validator.py` | 60 | 0 | 0 | 合法色值及任意语义选色；非法／近似色与 CSS 绕过；逐对象文字和关系冻结；非节点组容器配色；外部资源与隐藏内容；模拟批准限制；旧模式限制；真实 CLI 与报告写入 |
| `verification/exercise_svgkit.py` | 8 | 0 | 0 | 保留空格和全部文字；卡片／箭头／标题／分组构建失败不修改内存；合法非节点组容器；候选校验、同字节幂等及失败不覆盖 |
| `verification/exercise_render.cjs` | 8 | 0 | 0 | 实际浏览器渲染；旧哈希拒绝；浏览器缺失不冒充旧预览成功；无效区域及几何失败；参数错误 |
| `verification/exercise_publish.py` | 13 | 0 | 1 | 完整原子替换、失败清理、并发更改保护、严格改色、旧证据拒绝、目视缺项拒绝、最终文件名、幂等写入、受阻草稿与失败不得绕过 |

合计 **89 个行为用例通过，1 个环境受阻，0 个失败**。预期拒绝的负例被正确拒绝属于“用例通过”，不代表该非法 SVG 通过验收。发布器的渲染／目视记录夹具为模拟数据，用于验证证据契约；实际渲染与代理目视另见下一节。

`verification/run_checks.py` 最终 **21 项检查通过**，覆盖包内 Markdown 链接、47 色配置和七份完整 SVG 资源清单。其 `not_run` 只表示该静态脚本本身不执行渲染、官方验证或独立演练，整体执行状态以本记录分列结果为准。

本轮 JSON 证据保留在 `D:/GitHub/skillhub/.trellis/tasks/11-05-editable-diagram-svg/`：`validator-negative.json`、`svgkit-tests.json`、`package-checks.json`；渲染／发布行为证据保留为包内 `verification/render-results.json` 和 `verification/publish-results.json`。这些是创建时的验证记录，后续生成不得继承旧通过。

## 七份资源的实际渲染与目视

使用本包的新渲染器逐份渲染，代理实际打开全部完整 PNG；纵向图按可读宽度检查。对应 `render-N.static.json`、`render-N.render.json`、`render-N.visual.json` 位于上述本轮工作记录目录，包含完整 SVG／清单／色板／PNG 哈希。

| N | SVG 资源 | 实际预览尺寸 | 可编辑文字数 | 静态／渲染／目视 |
|---:|---|---|---:|---|
| 0 | `assets/icons.svg` | 1600×1036 | 19 | 通过／通过／通过 |
| 1 | `assets/templates/flow.svg` | 1600×900 | 27 | 通过／通过／通过 |
| 2 | `assets/templates/layers.svg` | 1600×1589 | 28 | 通过／通过／通过 |
| 3 | `assets/templates/overview-detail.svg` | 1600×900 | 44 | 通过／通过／通过 |
| 4 | `examples/architecture.svg` | 1600×1589 | 28 | 通过／通过／通过 |
| 5 | `examples/lifecycle.svg` | 1600×900 | 44 | 通过／通过／通过 |
| 6 | `verification/forward-test/cold-chain.svg` | 1600×1480 | 16 | 通过／通过／通过 |

目视检查覆盖实际中文／英文／数字字形、图标、文字换行和可读性、关系与端点、遮挡和裁切、配色与编号、阅读顺序、图例和已确认内容。未见明显缺字、文字重叠、连线穿字或裁切。浏览器几何检查为空及字体查询结果没有被当作目视替代。

## 独立新输入走查

给未获得实现结论的独立代理一个新的虚构设备维修请求，只提供本技能和原始材料，并使用隔离工作目录。材料要求五节点 `报修→派单→检修→验收→关闭`；另有 `检修→派单` 的“无法修复，重新派单”和 `验收→检修` 的“验收不通过，继续检修”。明确不画备件库存、收费、通知或设备监控。

1. 代理先给一份完整提纲，包含主顺序拓扑、medium 细节、六条条件关系、1280×720 尺寸、五组精确配色、线型图例、装饰和范围边界；**确认前没有生成本次 SVG**。
2. 测试方一次确认整份提纲，明确是隔离模拟批准；冻结清单 `confirmation.status=simulated`，随后全程用 `--example-mode`，未把模拟批准写成真人授权。
3. 五卡片分别选择白底 `#ffffff`，框边／强调依次为 `#8db8ff`／`#2468ee`、`#bccae2`／`#526b98`、`#ffd27a`／`#f08a00`、`#8fe0d5`／`#0b8f86`、`#b7bfff`／`#5149e8`；文字前景 `#12306b`。颜色用于识别本图卡片，没有按业务职责套固定规则。
4. 主流程本图选择 `#7f8fab` 实线，反馈选择 `#f08a00` 虚线并列图例。`#7f8fab` 是允许使用的白名单成员，**不作为所有图统一连线色**；本例使用它符合本图自主选色规则。
5. 当前静态检查通过，实际 Chrome 渲染到 1280×720，16 项文字进入渲染。生成代理、根代理及额外只读复核代理实际查看同一完整预览，核对两条不同反馈目标及所有条件。没有新增范围外功能。
6. 发布器校验当前静态／渲染／八项目视证据后写入 `设备维修工单.svg`，退出码 0，`written=true`、`final_acceptance=true`。这些字段是**示例模式下**的冻结与本地交付结果。

走查最终 SVG、冻结清单、提纲／命令／各阶段 JSON 及报告位于 `D:/GitHub/skillhub/.trellis/tasks/11-05-editable-diagram-svg/independent-forward/`。最终 SVG SHA-256：`64f99fbfb0d7636acdcc33a653cb9803402bd61f8562f6f502285e678cc2fce9`；清单 SHA-256：`8e54eb45f2717805df8347f35be963491dcb470402fe55bbd329bab16a624b61`；色板 SHA-256：`1d96561cb1848cbfc47559bd9d43f9ea33be0cd0cfae946120539c98afeed2d7`。

本次证明“单次提纲确认→冻结→受控取色→SVG→当前校验→实际渲染目视→本地原子写入”能够跑通；不证明真人业务批准或接收设备排版。

## 四类检查状态与环境边界

| 状态 | 本轮实际项目 |
|---|---|
| **通过** | 89 个行为用例、包内静态资源／链接检查、七份资源实际渲染目视、独立新输入模拟全流程、原始 71 文件未变、相关 Python 语法检查及 `git diff --check`、本次登记预览／缓存／临时文件清理 |
| **失败** | 无遗留失败；已修正的问题和预期拒绝负例不能被标成最终 SVG 通过 |
| **未执行** | 真人具体业务批准及最终风格验收；接收机器／其他 SVG 编辑器／投影设备验证；具体字体文件及全字库覆盖解析；三次同问题回退实战（无连续失败，未触发）；全局安装、上传、提交、部署（不在本次任务范围） |
| **环境受阻** | 官方 `skill-creator/scripts/quick_validate.py` 实际启动后因 `ModuleNotFoundError: No module named 'yaml'` 无法运行；发布器真实符号链接行为用例因 Windows `WinError 1314` 无法创建测试链接 |

官方校验未标为通过，没有安装 PyYAML。另行完成了 frontmatter 必需字段、命名、未完成占位、中文说明及 `agents/openai.yaml` 字段检查；这些窄检查不冒充官方校验。符号链接拒绝实现保留，真实链接用例没有伪造成功。

实际环境：Windows；Python 3.12.14；Node v24.20.0；已有 Playwright 1.62.1；Chrome 156.0.8078.48。使用本机字体回退，没有下载字体。代理查看当前渲染结果不等于接收机器字宽／换行通过，也不等于真人风格验收。

## 复验与清理

已有 Python／Node 环境中从包根运行以下命令；实际渲染还需已有 Playwright／Chromium，必要时传 `--module-dir`、`--browser` 的真实路径，见 [verification.md](../references/verification.md)。

```sh
python verification/exercise_validator.py --report work/validator-tests.json
python verification/exercise_svgkit.py --report work/svgkit-tests.json
python verification/exercise_publish.py --report work/publish-tests.json
node verification/exercise_render.cjs --report work/render-tests.json
python verification/run_checks.py --report work/package-checks.json
```

每份实际新图另走静态→实际渲染→人工／代理目视记录→发布，不依赖本报告。已有模板与示例的确认均为模拟，不可直接作为真实请求授权。渲染和目视证据对应输入哈希，改 SVG 后必须重做受影响检查。

本轮预览 PNG 仅用于检查；保留 SVG、冻结清单和文字／JSON 证据，删除已登记的预览、临时候选、浏览器临时目录及新包内 Python 缓存。实际清理结果见本轮工作目录的 `cleanup-report.json` 和独立演练目录的同名记录；没有删除原技能或他人文件。清理后的 PNG 路径为历史证据位置，可从保留 SVG 重新渲染。

## 同日配色风格修订

用户实际使用后指出融合图偏淡，并指定 `skillhub架构图-codex-1105.svg` 为认可的视觉参考。本次只读渲染并查看两份用户 SVG：认可版有满宽蓝／橙／紫渐变主标题栏；融合版主标题区全为浅色，强色集中在短条、图标与连线。差距主要来自强色面积和视觉层级。

按用户最新要求，将精确蓝／青绿／橙梯度、辅助紫、浅蓝背景、白字主标题栏、白卡细边和轻阴影、基础设施低饱和蓝灰写成默认。新增主配色必须与基准的饱和感、明暗、渐变及使用面积协调；白名单合法不能代替视觉通过。同步更新提纲与目视清单，不新增第二次风格确认。

修正 `svgkit.band()` 将组标题误绑定卡片深色 foreground 的问题。标题栏白字独立按 `texts.fill` 冻结，卡片深字约束保留。相关几何助手 **8 个行为用例通过**，包内 **21 项静态检查通过**；本轮没有把创建时的全部89个用例冒充重跑结果。独立只读文档复核通过。

隔离模拟探针验证饱和蓝标题栏白字与白卡深字：当前结构／冻结／白名单通过，实际渲染为1600×900，代理打开完整PNG检查标题和正文。此探针只验证本次样式机制，不代表重新生成或验收用户业务架构图。探针初次使用内存清单哈希，渲染器正确拒绝与落盘清单不符的静态证据；改用标准CLI重新校验实际文件后通过，原失败记录保留。

本次修订证据位于 `D:/GitHub/skillhub/.trellis/tasks/11-05-editable-svg-color/`，包含 `svgkit-tests.json`、`package-checks.json`、`probe.static.json`、`probe.render.json`、目视记录及安装位置同步日志。预览仅用于检查并在记录后清理。用户两份原SVG未改动；色板仍为原47值，未增加色值。接收设备／其他编辑器未执行，本轮未重跑先前受环境阻碍的官方YAML校验。
