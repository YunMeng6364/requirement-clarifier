# 校验、渲染、发布与清理

工作目录为新skill包根。`python` 指已经核实的Python3，`node` 指已有Node；静态／发布仅用Python标准库，包内渲染需要已有Playwright和Chromium兼容浏览器。命令中的示例文件／实际环境路径必须替换，不下载或安装依赖。读取输入来源，先静态预检，再在浏览器中渲染。

## 生产流水线

```sh
python scripts/validate_svg.py work/candidate.svg --acceptance work/acceptance.json --report work/static-check.json
node scripts/render_svg.cjs --input work/candidate.svg --output work/preview.png --acceptance work/acceptance.json --static-report work/static-check.json --width 1600 --audit work/preview.render.json
python scripts/publish_svg.py --candidate work/candidate.svg --output diagram.svg --acceptance work/acceptance.json --static-report work/static-check.json --render-report work/preview.render.json --review work/visual-review.json --report work/publish.json
```

`work/` 是本次登记的私有工作目录，最终SVG不在验收前反复覆盖。脚本支持示例专用 `--example-mode`，只用于包内simulated确认；真实请求必须approved。兼容 `--expect`／`--expected-file` 可以验证旧词表，但完整冻结验收列“未执行”、`production_ready:false`，不能生产发布。

Playwright／浏览器不在默认位置时，给渲染命令加 `--module-dir ACTUAL_NODE_MODULES --browser ACTUAL_CHROMIUM`；用先核实的路径，不能原样执行占位值。`--audit` 明确报告路径；`--width` 为已冻结展示宽、有效范围320–8192；按viewBox比例输出，高度超过16384用已批准的拆图／分区方案。

## 静态范围与封闭SVG子集

`validate_svg.py` 覆盖UTF-8、真正XML解析、无DTD／ENTITY／远程样式、SVG命名空间、显式尺寸／viewBox、唯一ID、内部引用、无外部资源／活动内容／image、非空title／desc、可编辑text、47色白名单、逐对象文字／颜色／区域、节点／关系／图例／可见登记、冻结组paint与背景／根默认。

颜色只写presentation属性或简单内联style；style元素保留普通字体相关声明。禁止style元素paint、CSS变量、转义／@规则／动态伪类／!important、RGB／HSL、短／八位hex、颜色名以及动态改变paint。所有defs、marker、symbol都检查；currentColor仅限合法icon实例继承，未受控默认黑色失败。已确认组用 `data-paint-role="card|accent|foreground|header"` 表明用途，具体schema见 [confirmation.md](confirmation.md)。

可见文字的SVG id与data-content-id都等于texts.id，一项一text，tspan切原字符串；关键字在别处出现不通过逐对象检查。区域data-bounds为根viewBox四个有限数、正宽高；复杂变换不能静默跳过。脚本仍不能证明实际字形齐全、文字未遮挡、连接几何目标或业务真实性，必须下一阶段核对。

## 当前证据与实际目视

报告schema统一：`schema_version:1`、`stage`（static／render／visual／publish）、`status`、`ok`、`svg_path`、`svg_sha256`、`acceptance_sha256`、`palette_sha256`、`checks`、`results`、`limitations`。哈希是64位小写SHA-256。每项results含key／status／reason／evidence；四种status仅“通过／失败／未执行／环境受阻”。`production_ready` 表示已完整冻结检查，不由词表模式设置。

render另记录 `png_path/png_sha256/preview:{width,height}`、版本、文字／图标数量、区域与几何；visual另记录png_sha256、preview、reviewed_at、acceptance_version（等于acceptance_sha256）；publish另含output_path、written、final_acceptance。阶段status先失败，其次环境受阻、必需项未执行，否则通过；本阶段ok不覆盖未执行的其他项目。退出码0通过、1检查失败、2参数／清单／配置错误、3环境受阻。草稿已写也可退出3，必须看written与final_acceptance。

渲染脚本检查静态证据与当前文件三个哈希一致，阻止网络，等待字体后生成本次PNG，不能接受旧文件存在作为本次成功。所有生产文字区域必须有效。几何或屏幕字号记录不是目视结论。

代理实际查看完整PNG及必要局部，按展示尺寸检查：中文／英文／数字、图标、标题换行、关键条件可读、溢出／遮挡／裁切、连线不穿字、端点与marker、分支条件、并行／汇合、反馈目标、编号／名称／颜色对应、图例／阅读顺序、边界与已确认内容。纵向图按可阅读宽度滚读；不能只看缩略图或放大局部。font lookup不证明真实字体命中；记录实际环境，接收机器或投影未测写未执行。

目视后手工记录工作文件 `visual-review.json`，按照上述通用schema，每个检查写真实结果，不由渲染器自动声称“已看过”。必须有八个已执行检查键：`glyphs`（字形）、`icons`（图标，批准不使用时核对为通过）、`text_layout`、`connections`、`clipping`、`colors`、`reading_order`、`content`；全部通过才能作为成品证据。`reviewed_at` 用实际ISO8601时间，`acceptance_version` 必须等于清单SHA-256，preview与PNG哈希须与当前render一致。用户最终风格喜好没有确认则未执行，不额外强制第二个确认闸门。

`colors` 必须记录两种不同结论：静态白名单／冻结配色是否通过，以及实际视觉是否符合提纲中的配色风格。核对很浅的蓝色背景、饱和主标题栏与白字、白卡和轻阴影、基础设施蓝灰、强色面积及新增主色与蓝／青绿／橙的协调；全部主区退化为淡底、强色仅剩图标／短条时，不能写风格通过。新增主色虽合法，但过于跳脱、明显更淡或破坏明暗层级，仍属视觉失败。实际颜色统一性依渲染目视判断，不用白名单检查或单个饱和度数字冒充。

## 原子写入与草稿

`publish_svg.py` 先重新核对候选、清单、白名单及证据当前哈希，检查静态／渲染／目视通过，再比较字节；相同不写，不同才在目标同目录写完整临时文件、flush/fsync、确认目标未被并发更改后原子替换。成品文件名必须等于冻结的diagram.filename，草稿可用明确draft名；拒绝符号链接目标，避免写入其指向路径。断言失败不改目标，失败临时文件清理。它只落盘本地文件，不上传或部署。

环境确实受阻时，静态通过可保存明确草稿：

```sh
python scripts/publish_svg.py --candidate work/candidate.svg --output diagram-draft.svg --acceptance work/acceptance.json --static-report work/static-check.json --render-report work/render-blocked.json --draft-reason "没有可用浏览器，渲染验收未完成" --report work/publish.json
```

`render-blocked.json` 必须有当前三个输入哈希、stage=render、status=环境受阻、真实原因且无失败，不能任意字符串绕过验收。Node本身缺失时由执行代理根据真实环境错误及核实文件哈希建同schema记录，不伪造尝试。检查失败保持失败，不伪装成环境受阻或未执行。

纯改色加 `--baseline original.svg --change-contract change.json`，合同为 `schema_version:1`、`baseline_sha256` 和非空 `mappings:[{"old":"#3b8bff","new":"#5b6cff","count":2}]`，count必须是已核实的正整数；该示意不能套用到未读过的图。仅改paint属性或内联声明，所有其他字节相等以保护文字／几何／结构／线型；原值已全部替换且新状态完整时幂等无写，混合／未知／次数不符失败。新增可见元素先说明等确认。

## 修订与清理

同问题连续修三次仍失败就改布局、扩大区域或拆图；只能直接执行提纲批准的回退，超出冻结内容／尺寸／颜色／图数先给具体差异确认。不得删关键文字、藏错误、放宽标准交差。更改SVG后重新检查当前证据。

交付给SVG链接、内容对照、精确选色与理由、实际命令及分列四类结果。记录文字证据和SVG／PNG哈希后清理本次登记的预览与临时候选、临时浏览器产物；保留冻结清单及文字／JSON工作报告用于续作，未要求则不增加对外交付文件。只删除核实属于本次的路径，不删原包或他人文件。清理失败写环境受阻并列路径。

## 包自身验证

```sh
python verification/exercise_validator.py --report work/validator-tests.json
python verification/exercise_publish.py --report work/publish-tests.json
node verification/exercise_render.cjs --report work/render-tests.json
python verification/exercise_svgkit.py --report work/svgkit-tests.json
python verification/run_checks.py --report work/package-checks.json
```

验证助手的实际参数以 `--help` 为准；若当前渲染环境需路径，传核实的module-dir／browser。资源正反例不等于真实用户审批。包的本次创建实测记录位于 `verification/REPORT.md`；以后新图重新执行，不继承旧通过。
