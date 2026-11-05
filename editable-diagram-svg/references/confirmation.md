# 单次确认、冻结与变更

提纲必须包含标题／目标、证据性质、必须文字、对象及编号、关系方向与条件、边界、拓扑、细节、尺寸与展示宽度、完整精确取色映射、线型图例、图标／装饰及拆图回退。用户一次确认涵盖整份提纲，不再逐项问拓扑或细节。确认前禁止生成本次成图；可分析源素材或查看已有模板。

取色映射同时列明主分组饱和标题栏、尺寸和精确渐变端点、白色标题文字、卡片深色前景以及侧条／强调面积。新增主配色必须说明与蓝／青绿／橙基准的视觉协调；不能用“在白名单内”替代这一判断。用户本次明确指定的配色和风格可直接作为提纲建议依据，不重复询问已经确定的风格政策。

批准后保存 `acceptance.json`；它是本次生成的工作记录，不属于每次自动对外增加的交付文件。保留用户确认依据与时间（实际取得时记录），不得伪造回复。生产模式要求非空 `texts`，每项必有 `id/value/region/fill`；所有可见文字的真实 SVG `id` 与 `data-content-id` 均等于 `texts.id`，一个 `text` 的多行 `tspan` 仍是同一文字对象。`visible_elements` 只引用真实 SVG ID，不引用区域名称或不存在的逻辑 ID。`region` 对应最近祖先的 `data-region` 名称，非节点文字可有独立区域。`nodes`、`relations`、`groups` 和 `line_styles` 可以为空，但必须显式存在并与图一致。字段约定如下：

```json
{
  "schema_version": 1,
  "confirmation": {"status": "approved", "evidence": "本次实际用户批准的消息定位或摘录"},
  "diagram": {
    "id": "diagram-main", "filename": "diagram-main.svg",
    "title": "已确认标题", "description": "已确认范围与边界",
    "topology": "left-to-right", "detail_level": "medium",
    "viewBox": [0, 0, 1920, 1080], "width": 1920, "height": 1080,
    "display_width": 1600, "background": {"id": "diagram-background", "fill": "#f4f9ff"}, "defaults": null
  },
  "texts": [{"id": "text-node-01", "value": "01 提交", "region": "node-01", "fill": "#12306b"}],
  "nodes": [{"id": "node-01", "group": "group-input", "title_text": "text-node-01"}],
  "groups": [{
    "id": "group-input", "members": ["node-01"],
    "paint": {"kind": "solid", "fill": "#fafcff", "stroke": "#8db8ff", "accent": "#2468ee", "foreground": "#12306b"},
    "reason": "本图以蓝色区分输入区，保持同一对象在详图中的识别"
  }],
  "relations": [],
  "line_styles": [],
  "visible_elements": ["diagram-background", "group-input", "node-01", "text-node-01"],
  "assumptions": [],
  "fallback": {"allowed": false, "description": "未批准内容重分配；超出几何修正须先确认"}
}
```

这是字段示意，实际清单必须列全标题、说明、图例、条件标签等文字和全部可见元素，不可原样将示意视为已批准内容。所有组的 `paint.fill` 始终为卡片纯色，`stroke/accent/foreground` 也是明确白名单纯色；`kind:"solid"` 不含渐变。需要渐变标题栏时改为 `kind:"gradient"`，另加 `header_gradient:{"id":"gradient-blue","stops":[{"offset":0,"color":"#3b8bff"},{"offset":1,"color":"#1b57e0"}],"direction":[0,0,1,1]}`，不改变卡片 fill。`diagram.background` 单独冻结背景元素 ID、纯色 fill 或同结构的 gradient；`diagram.defaults` 冻结根 fill、stroke、color。没有背景或默认继承时显式填 null 并为全部可见元素指定 paint。

SVG 根、分组、节点、关系、图例以对应 ID 标记；组记录所有成员，节点用 `data-group-id`，关系用 `data-from`、`data-to`、`data-kind`、`data-condition`、`data-line-style`；`relations` 中同名字段为 `from`、`to`、`kind`、`condition`、`line_style`，再用 `label_text` 指向可见条件标签。线型记录 `id/stroke/dasharray/meaning/legend_text/marker`，其中 id 是逻辑样式名，marker 是真实 SVG ID；`dasharray:""` 表示实线、SVG 不写 dasharray 属性。编号与显示名称由 `texts` 冻结，不由 ID 推断。箭头标记与线色一致，实际条件标签引用必须一一匹配。

默认最终 SVG 的节点卡片外框用 `data-paint-role="card"` 标记并与 `paint.fill/stroke` 一致，分组强调元素和文字前景用 `data-paint-role="accent|foreground"` 标记；渐变组的标题栏用 `data-paint-role="header"` 引用 header_gradient。同一组在不同详图仍用同一 paint，几何可以不同。每项 texts.fill、背景与根默认也逐值比对。校验器据此检查映射，不根据 blue／orange 等预设名推断业务职责。装饰框、背景、图标、阴影、额外标签也须属于 `visible_elements` 清单；`defs` 内几何不单独算可见元素，使用它的实例要登记。可见元素可以是分组容器 ID，其内部纯几何由该容器覆盖，内部文字／节点／关系／图标实例仍须单独登记；根 SVG 不作为豁免全部新增元素的容器。静态比对登记和标注不能证明几何语义正确，须目视核对。

同一元素的坐标、换行、尺寸和线条绕行可为验收修复调整，保持冻结文字和关系；不得将文字移动到隐藏区或裁切以通过。纯改色请求还要冻结原文字、几何、结构和线型，只改获批映射。确认后新增任何可见元素（包括装饰），或改变名称、条件、关系、颜色、图数／尺寸，先说明差异并等待增量确认；不重复确认无变化部分。提纲明确批准的备用拆图可直接执行，冻结总内容不减、模块编号与颜色一致，按备用方案为各图生成对应清单。三次仍失败且备用方案未批准时，提出具体重排／拆图变更；必要确认不能由超时默认同意替代。

`paint.foreground` 是卡片标题的深色前景，对应卡片文字的 `data-paint-role="foreground"`。主分组渐变标题栏的白字单独由 `texts.fill="#ffffff"` 冻结，不标作卡片 foreground；`svgkit.band()` 按该文字项取色。这样同组可同时采用“饱和栏白字”和“白卡深字”，两类文字仍逐对象校验色值。

写入必须幂等：先完成计数、内容、色值与几何断言，再生成完整候选；助手单方法失败不修改累计部件，静态失败不修改最终目标。相同内容重跑不得累加模块／defs 或改无关内容；同字节则不写。完整候选渲染目视后才原子发布合格 SVG。环境受阻可原子保存静态已通过的源码草稿并清楚标注未完成项；已失败检查不能转成“未执行”掩盖。

