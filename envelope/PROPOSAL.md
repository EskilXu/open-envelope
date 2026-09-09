# OpenEnvelope（暂定名，原 OFB）— RFC-0 rev 2, 2026-09-04

> 独立于 HDEB 的中立标准提案。不是"另一个能量块格式"，而是**把 HDEB 里混在一个记录里的四件事拆开，并把"验证结果"升为一等公民**。
> 状态：草案，供讨论。标注 ★ = 一手来源已核；◆ = 可信二手；◇ = 待核。

## 0. 为什么 HDEB 不够开放（即使开源）

| 问题 | 后果 |
|---|---|
| 名字属于一家厂商的白皮书 | 竞争对手不会采用；标准桌（LF Energy / IEC）不会接一个带厂商名的提案 |
| 一个记录同时装物理、市场、层级、回退、来源 | 任何一层的变更都要 bump 整个 schema；EMS 厂商只关心物理层却被迫理解市场字段 |
| 灵活性用固定字段表达（min/max/ramp/SOC） | 换一种设备（热泵、电解槽、EV 队列）就要加字段；无法表达耦合约束 |
| 校验结果不在标准内 | "被谁、按哪版规则、验过什么"无处落脚 —— 而这恰恰是口碑与数据飞轮的载体 |

## 1. 设计原则

1. **无厂商词汇**。名字、字段、示例都不引用任何公司的产品概念。
2. **层可分离**。四层各自独立成文档、独立版本、独立传输；接收方只需实现它需要的层。
3. **灵活性 = 约束集，不是字段集**。一个块的可行域用线性约束 `A·u ≤ b`（对时间窗内的功率向量 `u`）加少量命名参数表达。固定字段是约束集的语法糖。S2 的 FRBC/PEBC/OMBC、虚拟电池模型、爬坡、SOC 走廊都能落到这一种表示里。
4. **验证是一等对象**。`Attestation` 记录：谁、用哪版规则集、对哪个输入哈希、得到什么结论。可签名，可链式引用。
5. **同意与驻留显式**。每个块带 `consent`：能否出境、能否用于训练、保留期。默认全部为最保守值。
6. **只引用、不重造身份**。所有标识为 `{scheme, id}`：scheme 为发码机构反向域名（`iec.cim.mrid`、`eu.entsoe.eic`、`jp.occto.area`），id 为该机构原码。EIC 不覆盖日本（已核，见 docs/VERIFICATION-2026-09-04.md §3），故不假设任何单一全球码。时间 ISO 8601 带时区，货币 ISO 4217。
7. **测试即标准**。一致性测试套件（JSON 文件 + 期望结果）与 spec 同库同版本；实现通过测试即"符合"。
8. **作为既有开放标准的 profile 提交**，不做替代品：S2 (EN 50491-12-2) ★ 的资源侧、Shapeshifter/UFTP ◆ 的聚合商↔DSO 侧、IEC 62325 CIM 市场 profile ◆ 的交易所侧、OpenADR 3 ◆ 的事件侧。OpenEnvelope 的定位是它们之间**缺失的通用中间表示**。

## 2. 四层模型

```
L3  Assurance   Attestation{rule_set, input_hash, verdict, violations[], signer}   ← 口碑/数据飞轮在此
L2  Offer       市场包装: price, divisibility, linked/exclusive, market_ref            ← 交易所 / 同時市場 three-part offer
L1  Position    schedule / cleared / measured 的实际功率轨迹                          ← 结算与偏差
L0  Envelope    可行域: 时间窗 × 约束集 (A·u ≤ b) + 命名参数 (storage, ramp…)          ← 物理，与市场无关
```

一个 EMS 只实现 L0+L1；一个交易所接口只实现 L2；一个校验服务读 L0+L1、写 L3。**HDEB 的一条记录 ≈ L0∪L1∪L2 压扁后再加 provenance**，可无损映射（见 `docs/mapping.md`）。

## 3. 核心对象（摘要；完整见 `envelope-0.0.3.schema.json`）

**Envelope (L0)**
```json
{"oe": "0.0.3", "layer": "envelope", "id": "urn:oe:env:…",
 "resource_ref": {"node": {"scheme": "iec.cim.mrid", "id": "…"}, "area": {"scheme": "jp.occto.area", "id": "03"}},
 "window": {"start": "…", "end": "…", "step_min": 30},
 "vars": ["p"],                       // 每步一个变量 p[t]，kW，注入为正
 "modes": [{"id":"charge","bounds":{"p":[-250,0]},"min_duration_steps":2,"startup_cost":0}, …],   // 0.0.3 新增：离散模式，承载整数约束
 "aggregation": {"approximation":"inner","of":["…"]},   // 0.0.3 新增：聚合近似声明
 "bounds": {"p": [-250, 250]},
 "constraints": [                      // 线性: sum_j coef_j * var_j <= rhs
   {"name": "soc_max", "terms": [{"var": "p", "t": "*", "coef": 0.5}], "rhs": 300, "sense": "<="},
   {"name": "ramp_up", "diff": {"var": "p", "lag": 1}, "rhs": 1500, "sense": "<="}
 ],
 "params": {"storage": {"capacity_kwh": 1000, "soc0": 0.6, "eta_c": 0.95, "eta_d": 0.95}},
 "fallback": {"mode": "rulebook", "ref": "…", "timeout_s": 2},
 "consent": {"cross_border": false, "training_use": false, "retention_days": 30},
 "provenance": {…}}
```

**Position (L1)**：`{"layer":"position","envelope_ref":…,"kind":"schedule|cleared|measured","series":{"p":[…]}}`

**Offer (L2)**：`{"layer":"offer","envelope_ref":…,"market_ref":{"venue":"JEPX-SPOT","product":"30min"},"price":{…},"divisible":false,"min_acceptance":1.0,"linked":[…],"exclusive_group":null}`

**Attestation (L3)**：
```json
{"layer": "attestation", "subject_refs": ["urn:oe:env:…", "urn:oe:pos:…"],
 "input_sha256": "…", "rule_set": {"id": "oe-rules/kclkvl", "version": "0.1.0", "source": "https://…"},
 "verdict": "fail", "violations": [{"rule": "kcl", "where": "B1", "residual_kw": 100}],
 "checked_at": "…", "signer": {"id": "…", "sig": "…"}}
```

## 4. 为什么这个结构能同时产生"开放口碑"和"数据飞轮"

- **口碑**来自 L3 可公开复核：任何人拿同一个 `input_sha256` 和公开的 `rule_set` 版本都能重跑并得到相同 verdict。规则集开源、版本化、可引用——这是电力行业建立信任的唯一方式（"我能自己重跑你的数字"）。
- **飞轮**来自 L3 的 `violations[]`：它是结构化的**负样本**，天然带标签（哪条物理规则、在哪个节点、差多少）。在 `consent.training_use=true` 时才可进入数据集；这使"贡献数据换免费额度"成为显性、可审计的交易，而非暗箱采集。
- **可执行性边界**：L3 只说"错在哪"，不说"怎么改"。"怎么改"（优化、反事实）在标准之外，是商业层。标准与商业的分界写进结构，而不是靠自律。

## 5. 治理

- 许可：spec CC BY 4.0；参考实现与一致性测试 Apache-2.0；贡献者签署 Apache-2.0 附带的专利授权（不接受 NC / 专有条款）。
- 演进：RFC 流程（`envelope/rfcs/NNNN-*.md`），语义化版本，L0–L3 独立编号。
- 归属：目标在 LF Energy 下托管（该基金会已托管 S2 ★ 相关工作与 Shapeshifter ◆）；备选为向 S2 社区提交"聚合层 profile"。**不成立新联盟。**
- 中立性硬约束：维护者中任一雇主不得占多数席位；规则集变更需两个独立组织的实现通过一致性测试。

## 6. 与 HDEB 的关系

HDEB v0.1（本仓库）是**桥**：它让当前项目的物理层立刻有一个可用的交换格式。OpenEnvelope 是**目的地**：一旦 L0 约束集表示和 L3 证明对象被至少一家外部 EMS 实现，`hdeb-open` 将冻结在 0.x 并提供 `hdeb2oe` 单向转换器。

## 7. 待核清单（2026-09-04 已核，结果见 docs/VERIFICATION-2026-09-04.md）

- ★ LF Energy 无约束集式灵活性表示（FlexMeasures 为命名字段式）→ L0 空位成立；须能无损容纳 FlexMeasures flex-model / S2 FRBC。
- ★ 同時市場 TPO：结构已定（起動費多档 / 最低出力費用 / 阶梯增分曲线 + 運転パラメータ），字段未定，2030 年代前半 → L2 日本 profile 用 `ext["jp.doji"]` 隔离。
- ◆ EIC 不覆盖日本 → 标识改为 `{scheme,id}`，引用 `jp.occto.area` 原码。
- ◆ 届出制不适用于纯校验服务；边界 = 是否"指示"（下发指令）。写入服务条款。

---
*Sources for ★ items: LF Energy on S2 (https://lfenergy.org/interoperability-technologies-behind-the-meter-s2-standard/), S2 JSON schema repo (https://github.com/flexiblepower/s2-json), S2 docs (https://docs.s2standard.org/docs/learn/welcome/).*

## 8. 命名（2026-09-04 增补）

"OFB" 与密码学 Output Feedback 模式撞缩写，且 "Block" 延续了交易所词汇（ブロック入札）而非物理词汇。更 global 的方案：

**Envelope** —— 项目名 `openenvelope`，对象名 Envelope / Position / Offer / Attestation。

理由：
- "flexibility envelope" 是学界既有术语（Nosair & Bouffard 2015 起，2025 ETH 系列沿用），不是新造词。
- 跨语言零摩擦：日 **運転エンベロープ**（航空/电力工程常用）、中 **可行域包络**、英 envelope。三种语言里都已是工程词，不需解释。
- 命名模式对齐 LF Energy 受众已识别的 Open* 家族（OpenADR、OpenSTEF、OpenLEADR）。
- 2026-09-04 检索：GitHub / 能源标准领域无 "OpenEnvelope" 冲突（LBNL EFOnt、OpenTUMFlex、OPEN 等均不撞名）。
- 语义正确：L0 就是可行域的外包络；L1 是包络内的一条轨迹；L2 是对包络的定价；L3 是对轨迹是否落在包络内的证明。

备选（若域名/商标不可得）：`Flexvelope`（可读性差，不推荐）、`FEASIBLE`（缩写勉强）。

已执行（rev 2）：`ofb/` → `envelope/`；schema `$id` → `…/envelope/envelope-0.0.3.schema.json`；`resource_ref` → `{scheme,id}` 命名空间形式（docs/VERIFICATION-2026-09-04.md §3）；`ofb/` 保留为历史目录。
