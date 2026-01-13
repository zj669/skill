# Phase 1: Blueprint Protocol (Deep Design)

本协议将通过三个子步骤（Sub-steps）引导完成从业务背景到具体落地的完整设计。

## 📅 Step 1.1: Context & Concepts
**Goal**: 明确“我们在解决什么问题”以及“核心术语是什么”。

**Required Input (请回答):**
1.  **Project Background**: 用一句话描述这个功能/模块的业务背景。
2.  **Core Problem**: 它解决了用户的什么痛点？
3.  **Ubiquitous Language (通用语言)**:
    - 请列出 3-5 个核心业务术语（中英文对照）。
    - *Example*: `Product (商品)`, `SKU (库存单元)`, `Listing (上架单)`。

---

## 📅 Step 1.2: Strategic Modeling
**Goal**: 划分领域边界，识别聚合根。

**Required Input (请回答):**
1.  **Bounded Context (限界上下文)**: 这个功能属于哪个子域？(Core/Supporting/Generic)
2.  **Aggregate Root (聚合根)**: 谁是生命周期的管理者？
    - *Check*: 删除它，其他对象是否还有存在的意义？
3.  **Entities & VOs**:
    - 实体 (有唯一ID): `________`
    - 值对象 (无ID,以此代彼): `________`
4.  **Domain Events**: 会触发什么领域事件？(e.g., `OrderPaidEvent`)

---

## 📅 Step 1.3: Tactical Design & Verification
**Goal**: 定义接口交互与代码落地思路。

**Required Input (请回答):**
1.  **API Design**:
    - `Method URI`: ________________
    - `Input Command`: ________________
2.  **Interaction Flow (关键交互)**:
    - 描述：Controller -> AppService -> Domain 的调用链路。
    - *重点*: 业务逻辑是否已下沉到 Domain？
3.  **Architecture Check (架构自检)**:
    - [ ] 是否引入了防腐层 (ACL)？
    - [ ] 聚合根之间是否通过 ID 引用而不是对象引用？
    - [ ] 是否符合最终一致性？

## 📝 Final Deliverable (最终交付物)
完成上述三步后，请将所有信息汇总，生成一份完整的 技术设计说明书。