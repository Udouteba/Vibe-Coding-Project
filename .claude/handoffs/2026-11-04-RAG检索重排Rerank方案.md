# Session Handoff: RAG 检索 Rerank 重排方案

**日期:** 2026-11-04
**项目:** C:\Users\86189\Desktop\给排水智库APP（给排水智库）
**状态:** 方案已定，**未编码**（选型与参数已确认）

## 选型与参数（已确认）

- **模型：`BAAI/bge-reranker-base`**（~1.1GB，中文 rerank 标杆，CPU 友好）。
- **召回数量 N=20**（bi-encoder 先粗召回 20 条）→ **精排取 top 6**（沿用 `RETRIEVE_TOP_K=6`）。
- 备选（未用，备查）：`bge-reranker-v2-m3`（更高精度/多语言，~2.3GB）、`bge-reranker-v2-minicpm-layerwise`（~0.3GB 更轻）、`bge-reranker-large`（CPU 不推荐）。

## 选型理由

1. CPU 环境：~1.1GB、单对 50–150ms，20 对精排约 1–3 秒；large/v2-m3 在 CPU 慢且占内存。
2. 中文够用：base 的 rerank 精度已明显改善排序；base→large 边际收益小。
3. 零新增依赖：项目已装 `sentence-transformers==2.7.0`（`requirements.txt:26`），其 `CrossEncoder` 直接加载 base，无需 FlagEmbedding。
4. 兼容性稳：base 对现有 `transformers<5.0` 锁定兼容；v2 系列较新可能连锁改依赖。

## 集成方式

1. `vector_store_service.py` 加 `get_reranker()` 单例（lazy 加载 `CrossEncoder`，模式同现有 `get_embeddings()`）。
2. `search()` 流程改为：
   - bi-encoder + cosine 粗召回 **top 20**（各分类分别召回后合并）；
   - `reranker.predict([(query, content) ...])` 精排，取 **top 6**；
   - 结果走现有 `TTLCache` 缓存（复用已有缓存机制）。
3. 模型权重走已配的 `HF_ENDPOINT`（hf-mirror.com）下载。

## 注意点（编码时处理）

- **score 语义变化**：bge-reranker 输出 logit（非 cosine 的 [0,1]），若替换 score 会导致 `compute_low_confidence` 的 `RETRIEVE_MIN_SCORE=0.25` 阈值失效。建议 **rerank 只用于排序，score 保留 cosine**（阈值不变、改动最小）；或 rerank 后 sigmoid 归一化并重调阈值。
- **CPU 延迟需实测**：预估精排 +1~3 秒，具体以实测为准；batch 推理可提速。
- **准确性收益**：cross-encoder 显著提升专业术语场景的 top 命中率，减少「相似但无关」条文混入。

## MMR（待定，未选型）

用户此前提过 MMR 多样性筛选：计算量 <1ms、可减少多轮追问冗余。本次先定 Rerank，MMR 可在 Rerank 落地后视结果冗余情况再上（放 `search()` 合并排序后）。

## 待办

- [ ] 编码：`get_reranker()` 单例 + `search()` 加粗召回 20 → 精排 6。
- [ ] 实测 CPU 精排延迟与排序质量提升。
- [ ] （待定）是否加 MMR。

## 关联

- 上游：[[2026-11-04-RAG对话真工具检索方案]]（真工具检索会调用 `search()`，Rerank 在其内部生效）、[[2026-11-04-RAG切块方案]]
- 关键文件：`backend/app/services/vector_store_service.py`、`backend/config.py`（可加 `RERANK_*` 配置）
