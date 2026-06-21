# carbon-literature-bo-replay-skill

面向文献提取型碳材料数据库的 **离线贝叶斯优化回放**（offline Bayesian optimization replay）Skill。

它适合用于生物质硬碳、LIB/SIB 碳负极、水系超级电容器多孔碳等文献数据库，在真实实验闭环之前先回答一个方法学问题：

> 在给定候选池、描述符和目标值均来自已发表文献的前提下，BO-style acquisition 是否比随机搜索、纯 exploitation、多样性采样更快定位到已报道的高性能样本？

本项目不把结果表述为“发现新材料”。它只支持“离线回放提示该搜索策略值得进入小规模真实实验闭环验证”。

---

## 这版相对 v1.0.0 的主要优化

- 移除了不应进入仓库的缓存和生成物：`__pycache__`、`.pytest_cache`、`*.egg-info`、`outputs/`。
- 增加 `.gitignore`，避免下一次误提交运行结果。
- 修正 `src/` 布局下本地 `pytest` 导入问题。
- 补全 `pyproject.toml` 的 build-system 和 package discovery。
- CLI 增加 `--direction maximize|minimize`，以后目标可以是越大越好或越小越好。
- 自动特征选择更保守：默认排除 target-like / performance-like / predicted-like 字段，降低目标泄漏风险。
- 增加 exploit-only、diversity、oracle upper-bound 基线，避免 README 与代码不一致。
- 报告中增加 final improvement、AUC improvement、随机分位数、泄漏风险和保守决策标签。
- 泄漏审计增加 near-duplicate target、低 group 数、重复行、缺失 group column 等检查。

---

## 适用场景

推荐用于：

- 生物质衍生硬碳 SIB 文献数据库：`ICE`、可逆容量、平台容量等目标。
- 生物质 / 多孔碳 LIB 文献数据库：`ICE`、可逆容量、倍率容量等目标。
- 水系超级电容器数据库：比电容、倍率保持率、循环保持率等目标。
- AI4Materials 汇报或论文 SI 中的方法学验证。
- 在真实实验闭环前评估“已有数据库是否足以支持 BO 候选推荐”。

不推荐用于：

- 样本数太少但仍想宣称优化优势的场景。
- 没有 `paper_id` 或文献分组信息，却要做强泛化结论的场景。
- 将同一目标的派生字段、预测值、排名、最佳值放入特征的场景。
- 把离线回放包装成真实 autonomous laboratory 的场景。

---

## 安装

```bash
pip install -r requirements.txt
pip install -e .
```

测试：

```bash
pytest -q
```

---

## 快速运行 demo

```bash
python examples/run_demo.py
```

或使用命令行：

```bash
python -m carbon_literature_bo_replay.cli replay \
  --data examples/input/carbon_literature_demo.csv \
  --target ICE \
  --id-col sample_id \
  --paper-col paper_id \
  --out outputs/demo_replay \
  --seed-size 8 \
  --iterations 20 \
  --random-repeats 50 \
  --direction maximize
```

安装为可执行命令后也可以：

```bash
carbon-bo-replay replay \
  --data examples/input/carbon_literature_demo.csv \
  --target ICE \
  --id-col sample_id \
  --paper-col paper_id \
  --out outputs/demo_replay
```

---

## 用你自己的 Excel 数据运行

示例：SIB 数据库，以首圈库伦效率为目标。

```bash
python -m carbon_literature_bo_replay.cli replay \
  --data "SIB所有样本.xlsx" \
  --target "ICE" \
  --id-col "sample_id" \
  --paper-col "paper_id" \
  --features "carbonization_temperature,BET,d002,ID_IG,XPS_N,XPS_O,pore_volume,mass_loading" \
  --out outputs/sib_ice_replay \
  --seed-size 8 \
  --iterations 30 \
  --random-repeats 200 \
  --direction maximize
```

如果不写 `--features`，程序会自动选择数值型描述符；但为了论文或汇报的严谨性，建议你手动指定字段，并在报告中说明排除了哪些 performance-like 字段。

---

## 输入字段建议

最低要求：

| 字段 | 建议程度 | 说明 |
|---|---:|---|
| `sample_id` | 强烈建议 | 样本唯一编号 |
| `paper_id` | 强烈建议 | 文献/论文分组，用于泄漏审计 |
| `material_name` | 建议 | 样品名，便于核查 |
| target column | 必需 | 例如 `ICE`、capacity、capacitance、retention |
| descriptor columns | 必需 | 至少 3 个数值型描述符 |

推荐描述符：

```text
carbonization_temperature
activation_temperature
BET
pore_volume
micropore_volume
d002
ID_IG
XPS_N
XPS_O
mass_loading
electrode_thickness
compacted_density
current_density
voltage_window
```

注意：如果目标是 `ICE`，默认不要把容量、保持率、排名、预测容量等性能型字段作为输入特征。它们可能不是严格泄漏，但会使“搜索效率”被高估。

---

## 输出文件

```text
outputs/<run_name>/
├── bo_replay_report.md
├── replay_trace.csv
├── recommended_candidates.csv
├── baseline_comparison.csv
├── leakage_audit.csv
├── selected_features.csv
├── state/
│   ├── 01_dataset_profile.json
│   ├── 02_descriptor_schema.json
│   ├── 03_replay_protocol.json
│   ├── 04_surrogate_diagnostics.json
│   ├── 05_acquisition_trace.json
│   ├── 06_baseline_comparison.json
│   └── 07_leakage_audit.json
└── figures/
    └── bo_replay_curve.png
```

关键解释：

- `replay_trace.csv`：每轮 BO-style acquisition 选择的候选及 best-so-far 曲线。
- `baseline_comparison.csv`：random mean/p10/p90、exploit-only、diversity、oracle upper-bound。
- `recommended_candidates.csv`：离线回放中被选中的样本，不等于真实新候选。
- `leakage_audit.csv`：目标泄漏、同文献集中度、重复行、低样本量等问题。
- `bo_replay_report.md`：可直接放进汇报或 SI 草稿的审计报告。

---

## 决策标签

| 标签 | 含义 |
|---|---|
| `GO_EXPERIMENT` | 离线回放表现优于随机，且泄漏风险较低，可进入小规模实验闭环验证。 |
| `GO_MORE_DATA` | 方向可能有价值，但数据库覆盖、分组或稳定性不足，应先补数据或做分层。 |
| `METHOD_ONLY` | 只能作为流程演示，不能支持材料结论。 |
| `STOP` | 存在高风险泄漏或目标定义问题，不建议继续做搜索效率结论。 |

---

## 科学边界表述

推荐中文表述：

> 离线文献回放结果提示，在当前描述符空间、候选池和回放协议下，BO-style acquisition 相比随机搜索更快定位到已报道的高性能样本。该结果可作为后续小规模实验闭环设计的依据，但不应被解释为新材料发现。

推荐英文表述：

> The offline replay suggests that the acquisition strategy identifies already-reported high-performing literature samples more efficiently than random search under the defined descriptor space and replay protocol. This result supports candidate prioritization for a future experimental loop, but it should not be interpreted as autonomous discovery of a new material.

避免写法：

```text
The model discovered a new optimal carbon material.
```

---

## 仓库结构

```text
carbon-literature-bo-replay-skill/
├── README.md
├── README_en.md
├── skill.md
├── AGENTS.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── config/
├── prompts/
├── schemas/
├── src/carbon_literature_bo_replay/
├── examples/
├── tests/
└── docs/
```

---

## 和你的其他 workflow 的关系

建议顺序：

```text
AI/OCR 文献数据抽取
        ↓
数据清洗与异常值二次核查
        ↓
carbon-literature-bo-replay-skill
        ↓
离线搜索效率评估 + 泄漏审计
        ↓
小规模真实实验闭环设计
        ↓
综述/论文/SI 的一致性审计
```

这个 Skill 最适合作为你 AI4Materials 方向的“低成本闭环前验证模块”，而不是替代真实实验。

---

## License

MIT License
