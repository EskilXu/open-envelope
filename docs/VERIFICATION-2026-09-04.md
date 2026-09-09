# 核实记录 2026-09-04（对 PROPOSAL §7 待核清单）

★ 一手来源已核 · ◆ 可信二手 · ◇ 仍未核

## 1. LF Energy 是否已有约束集式（polytope）灵活性表示 — ★ 没有（交换格式层面）
- FlexMeasures（LF Energy）的 flex-model 是**命名字段**式：`power-capacity`、`soc-minima/maxima/targets`、`group`（共享逆变器上限）、power bands（= S2 operation modes）。内部编译为 Pyomo/HiGHS 的 MILP，但**约束集本身不是可交换对象**。
  来源：https://flexmeasures.readthedocs.io/stable/concepts/flexibility-configuration.html ；/stable/concepts/device_scheduler.html
- Shapeshifter/UFTP、S2 均为消息协议，非可行域表示。
- 约束集/zonotope/polytope 表示只存在于学术文献（ETH NCCR Automation 等，arXiv 2505.16374 / 2505.16396 / 2511.02668）。
- 另需对齐：LBNL **EFOnt**（Energy Flexibility Ontology，https://github.com/LBNL-ETA/EnergyFlexibilityOntology）— 本体层，非交换格式。
- **结论**：OFB L0 的约束集表示是空位。要求：FlexMeasures flex-model 与 S2 FRBC 必须能**无损映射进** L0；反向为有损。

## 2. 同時市場 three-part offer 最终字段 — ★ 未最终确定；结构已定
来源：同時市場の在り方等に関する検討会《第二次中間取りまとめ》2025-10-15（METI）
https://www.meti.go.jp/shingikai/energy_environment/doji_shijo_kento/pdf/20251015_1.pdf
- 已定：売り入札**原则按发电机单位**；スリーパート情報 = ①起動費（可按停机时长登记多档）②最低出力費用 ③增分費用カーブ（**阶梯式**登记，非连续曲线）；另登记運転パラメータ：出力容量上限・下限、起動時間、出力変化速度 等。
- 未定：運転パラメータ具体清单"詳細設計時に決定"（参考 PJM：最小停止/稼働時間、日/周最大起動回数等）；§6.6「揚水発電・DER の取扱い」列为待检討；脚注 15：DER"複数の電源をまとめて入札することもありうる"。
- 时间线：2030 年代前半，五阶段。前日 48 コマ沿用；時間前市場拟 3 回/日；直前市場 24 或 48 回/日。
- **对本项目的关键数据**：スポット売り入札中ブロック入札占 60–80%，約定率仅数%（2025 Q1，监视等委 図 7）。这就是"能量块表达能力不足"的官方量化证据。
- **结论**：L2 日本 profile 现在只能定义到"三部件 + 阶梯增分曲线 + 参数占位"；字段名以 2030 前详细设计为准，用 `ext["jp.doji"]` 隔离。

## 3. EIC 是否覆盖日本 9 区 — ◆ 不覆盖
- ENTSO-E 自述 EIC 用于 Internal European Market 参与者与对象的标识；发码由 CIO + 各 LIO 执行，无日本 LIO。
  来源：https://www.entsoe.eu/Documents/EDI/Library/EIC_Short_Guide_and_FAQ_V3_Approved%20April%202016.pdf
- **结论**：L0 `resource_ref` 改为**命名空间化标识**：`{"scheme":"jp.occto.area","id":"03"}`（OCCTO/JEPX エリア番号 01–10 ◇待核具体编号表）、`{"scheme":"eic","id":"10YJP-…"}` 不成立。全球通用模式：`scheme` = 发码机构反向域名，`id` = 该机构原始码，不自造码。

## 4. 届出制对纯校验服务的适用性 — ◆ 不适用，但有一条边界
- 特定卸供給事業 = 从发电事业者以外的、有供给能力者处**集约电力并向一般送配電/小売等供给**，>1,000kW，届出制（2022-04 起）。
  来源：資源エネルギー庁 届出说明会资料 https://www.enecho.meti.go.jp/category/electricity_and_gas/electricity_measures/009/shiryou/06_shiryou1.pdf
- 纯校验服务不供电、不集约 → 不属特定卸供給事業，无届出义务。
- **边界**：法条定义里"发电又は放電を**指示**する方法により…集約"——一旦服务从"判定对/错"变为"下发指令"，性质改变。这与 OFB 的 L3（verdict only）/ 商业层（instruction）分界完全一致，应写入服务条款。
- 另一条不受此影响的义务：客户若为经济安保法指定的 ≥50 万 kW 聚合商，其導入計画書须列出構成設備供应商——义务在客户侧，但我们的实体属性会被审。
- ◇ 仍需日本律师确认：电気事業法外的个人情报/計量法是否触及。

## 命名结论 → 见 PROPOSAL §8
