# profiles/ — 每个既有标准到 OpenEnvelope 四层的映射

目录：`profiles/<ecosystem>/<standard-id>/`
- `mapping.yaml`   字段级映射（源字段 → 目标层.字段，单位换算，缺省值，有损标记）
- `vectors/`       一致性测试向量：`<case>.in.<ext>` 与 `<case>.out.json`（期望的 L0/L1/L2）
- `NOTES.md`       访问性、许可、术语对照、已知不可映射项

原则：只引用既有标准的字段名与语义，不复制其文本（多数为付费标准）。
