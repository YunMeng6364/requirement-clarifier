# 来源与迁移范围

本包按 `SVG技能融合方案.md` 的裁决制作，材料只取同级三个限定源包；不读取其他目录副本。源码根相对来源清单：`architecture-diagram-generator/`、`diagram-creator/`、`technical-report-svg/`。源文件哈希如下为本次读取时 SHA-256，便于追溯，不是后续作品固定期望。

三个原目录均保留；规范派原模板／脚本、流程派 HTML／CSS／主题／画布、汇报派旧 PNG／安装与通过报告不纳入运行资源。新资源在独立目录改造，不回写原包。

| 新文件 | 迁移方式 | 限定来源 |
|---|---|---|
| `SKILL.md` | 改造 | `technical-report-svg/SKILL.md`；`technical-report-svg/references/verification.md`；`diagram-creator/SKILL.md`；`architecture-diagram-generator/references/workflow.md` |
| `agents/openai.yaml` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `assets/icons.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `assets/icons.svg` | 改造 | `technical-report-svg/assets/icons.svg` |
| `assets/templates/flow.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `assets/templates/flow.svg` | 改造 | `technical-report-svg/assets/templates/flow.svg` |
| `assets/templates/layers.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `assets/templates/layers.svg` | 改造 | `technical-report-svg/assets/templates/layers.svg` |
| `assets/templates/overview-detail.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `assets/templates/overview-detail.svg` | 改造 | `technical-report-svg/assets/templates/overview-detail.svg` |
| `examples/approved-content.md` | 改造 | `technical-report-svg/examples/approved-content.md` |
| `examples/architecture.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `examples/architecture.expected.json` | 复制 | `technical-report-svg/examples/architecture.expected.json` |
| `examples/architecture.svg` | 改造 | `technical-report-svg/examples/architecture.svg` |
| `examples/build_examples.py` | 改造 | `technical-report-svg/examples/build_examples.py` |
| `examples/lifecycle.acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `examples/lifecycle.expected.json` | 复制 | `technical-report-svg/examples/lifecycle.expected.json` |
| `examples/lifecycle.svg` | 改造 | `technical-report-svg/examples/lifecycle.svg` |
| `references/color-spec.md` | 改造 | `architecture-diagram-generator/references/color-spec.md`；`technical-report-svg/references/style-spec.md` |
| `references/confirmation.md` | 改造 | `technical-report-svg/SKILL.md`；`technical-report-svg/references/verification.md`；`diagram-creator/SKILL.md`；`architecture-diagram-generator/references/workflow.md` |
| `references/input-topology.md` | 改造 | `diagram-creator/SKILL.md`；`diagram-creator/references/topology-layouts.md` |
| `references/palette.json` | 改造 | `architecture-diagram-generator/references/color-spec.md`；`technical-report-svg/references/style-spec.md` |
| `references/style-spec.md` | 改造 | `technical-report-svg/references/style-spec.md` |
| `references/usage.md` | 改造 | `technical-report-svg/references/usage.md` |
| `references/verification.md` | 改造 | `technical-report-svg/references/verification.md` |
| `scripts/publish_svg.py` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `scripts/render_svg.cjs` | 改造 | `technical-report-svg/scripts/render_svg.cjs` |
| `scripts/svgkit.py` | 改造 | `technical-report-svg/scripts/svgkit.py` |
| `scripts/validate_svg.py` | 改造 | `technical-report-svg/scripts/validate_svg.py` |
| `verification/checklist.md` | 改造 | `technical-report-svg/verification/checklist.md` |
| `verification/REPORT.md` | 新建 | 本次实际实现、行为校验、资源渲染目视及独立模拟演练记录 |
| `verification/exercise_publish.py` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/exercise_render.cjs` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/exercise_svgkit.py` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/exercise_validator.py` | 改造 | `technical-report-svg/verification/exercise_validator.py` |
| `verification/forward-test/CONTENT.md` | 改造 | `technical-report-svg/verification/forward-test/CONTENT.md` |
| `verification/forward-test/acceptance.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/forward-test/build.py` | 改造 | `technical-report-svg/verification/forward-test/build.py` |
| `verification/forward-test/cold-chain.svg` | 改造 | `technical-report-svg/verification/forward-test/cold-chain.svg` |
| `verification/forward-test/expected.json` | 复制 | `technical-report-svg/verification/forward-test/expected.json` |
| `verification/publish-results.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/render-results.json` | 新建 | 本次实现／示例冻结契约；入口与参考遵循已定融合方案 |
| `verification/run_checks.py` | 改造 | `technical-report-svg/verification/run_checks.py` |

| 来源文件 | SHA-256 |
|---|---|
| `architecture-diagram-generator/references/color-spec.md` | `a1423165c711ba1bdd6d73163746b15f6b366acc5d431935e8c2b5a96e34b951` |
| `architecture-diagram-generator/references/workflow.md` | `2ad266d8818691d766a33c5b4bf0ce060ef0109ad801d221b3ade74955ab179b` |
| `diagram-creator/SKILL.md` | `555b7141643375e7f73c43dd34edb18be9d113b8cfb252a7d0d41afda53b104a` |
| `diagram-creator/references/topology-layouts.md` | `60d883532fa3d562b490fbab48d6e051af2deac92cb99c194e4a14e6c6675ec8` |
| `technical-report-svg/SKILL.md` | `0052db19c741090a75a77c8b70524242315dd5d9b6ee879db6f6ad26e9e3d586` |
| `technical-report-svg/assets/icons.svg` | `224e0578c349af7b9f657b4c7d0d34a561c937419d2dcef1a83be62a87cb4ad4` |
| `technical-report-svg/assets/templates/flow.svg` | `7b95439c6593b25e6cc32558425663b4e8afea8d35cc5fd364487c9a3eb28ef2` |
| `technical-report-svg/assets/templates/layers.svg` | `52f58db6282abd5a2bace2ffb5940cf56bf5e5f0e3d8d911f5a0fcc426b9d12f` |
| `technical-report-svg/assets/templates/overview-detail.svg` | `9b279f988921bc74360549cc2c80acc2507867fbbaa1fa66e3ffe082c8ab71b6` |
| `technical-report-svg/examples/approved-content.md` | `328bbaa7e34ceaaa2b636561ca019a28544fafb22460d8db6622f4603928129b` |
| `technical-report-svg/examples/architecture.expected.json` | `7044c1da662f8fea198ef08db5f9e01ee03369e74705f6dc710505a4df6a98f9` |
| `technical-report-svg/examples/architecture.svg` | `f6ef0d7d150f0e5d602b2bf1d33bbd8fdb3c37bd63f9da1fea66820b46ce7c7b` |
| `technical-report-svg/examples/build_examples.py` | `7158683dde6c240c8096749390ee406e9f2168007e5f5462c50d058ba88b35ed` |
| `technical-report-svg/examples/lifecycle.expected.json` | `6f5a603309d19f9043814847ed754ecabaccf4af6a468d6c73cc91cd66890529` |
| `technical-report-svg/examples/lifecycle.svg` | `a1147bed251ccad09e18fadabc49bc0ac993b3b1cbbc44021d2fa871ef6961ae` |
| `technical-report-svg/references/style-spec.md` | `f3609419f4ad683520aaafbdc40effafb64049c102e71d008da1db38123baf9d` |
| `technical-report-svg/references/usage.md` | `554e8a3a35b5a1160475700b126ca8004bf36c1f60e9e65893315cc7ff8bd8a7` |
| `technical-report-svg/references/verification.md` | `fc0abbce3c592f11e5ad5351d90ad8ab8564894deaba8be1242ea5168c72ee3b` |
| `technical-report-svg/scripts/render_svg.cjs` | `13435c2abd2e43e98073f5fb2a1d2079773b14bf4fafe14ca026a6b226a2a7bc` |
| `technical-report-svg/scripts/svgkit.py` | `eed0be89047a56d3f5fa9a11facd4716288f3b1a3929907487056657e35ff94d` |
| `technical-report-svg/scripts/validate_svg.py` | `9c769ce13a32cd781a2b9137d55e213123a2ee26e7bb57e55508a883636d1fba` |
| `technical-report-svg/verification/checklist.md` | `b8765fe64ac178b6c3ef43c0caf087c8d50fca60384923f0256340856c76d816` |
| `technical-report-svg/verification/exercise_validator.py` | `b8f2d52bc64c2d0223ab80dc9b2dabe8843475d9d5f0b90cb27b9e7064df1968` |
| `technical-report-svg/verification/forward-test/CONTENT.md` | `563719891314dfb724aa3399ef8733518ec4581d488a800b385f34459e75af13` |
| `technical-report-svg/verification/forward-test/build.py` | `cb9fdbc2e5062ac20ab9f35096cacf410cfc665927d0055bf2f111a3978e1a5f` |
| `technical-report-svg/verification/forward-test/cold-chain.svg` | `e750ea0f8554bcf0647254611686b8fd9bcc2432838246d5f2d1883948392eaa` |
| `technical-report-svg/verification/forward-test/expected.json` | `65817d4b8eecb095e863c81d0ad03d462c8b368787484cafe6c1d77c411f9f17` |
| `technical-report-svg/verification/run_checks.py` | `8a3fe2b8c4442bdb8387de7de8bd1880c54a756170497e6103166e1276f23e43` |

`assets/icons.svg` 的17个 symbol 几何来自汇报派，保留24×24网格与1.8轮廓；展示页颜色／登记改造。三模板、两示例和冷链资源保留原几何与关键文字，仅清色并补冻结ID／分组。新acceptance均显式simulated，不能代替真实批准。

颜色迁移只影响声明：短白 `#fff`→`#ffffff`；`#0b9488`→`#0b8f86`；`#c76b00`／`#b26600`→`#a2620a`；`#5d55d7`→`#5149e8`；`#c6dafb`→`#8db8ff`；`#9ce0d6`→`#8fe0d5`；`#f6cf8a`→`#ffd27a`；`#cbc8fa`→`#b7bfff`；`#bdcfe7`→`#cfe0fb`；`#092343`→`#12306b`。并集已允许的 `#2468ee` 保留，不扩充白名单、不绑定职责。

来源三包未发现明确许可证／作者署名文本；“原创”或工具名不是许可授权。本包保留可识别的原声明，不虚构作者或许可证，不根据仓库许可证替三包赋权。本次本地制作不包含发布／重新许可。当前验证见 `../verification/REPORT.md`，后续每次输出重新校验和渲染，不继承旧通过。
