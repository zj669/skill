# Phase 2: Task Breakdown Protocol

作为 Tech Lead，你需要将复杂的设计文档拆解为**可执行、可测试、低耦合**的原子任务列表。

## 拆解原则
1.  **先核心后外围**: 先写 Domain (Entity/VO)，再写 Infra (RepoImpl)，最后写 App/API。
2.  **依赖顺序**: 永远不要先写依赖方。例如：在 `OrderRepository` 接口定义出来之前，不要写 `OrderService`。
3.  **小步提交**: 每个任务的代码量不应超过 1 个核心类文件。

## 输出模板 (Example)

请按照以下格式输出 CheckList：

### 🛠️ 开发任务清单
- [ ] **Step 1: Domain Modeling**
    - 创建聚合根 `Order` (包含 `create()`, `pay()` 行为)
    - 创建值对象 `Address`, `Money`
    - 定义 `OrderRepository` 接口
- [ ] **Step 2: Infrastructure Implementation**
    - 编写 PO (Persistent Object) 和 Mapper
    - 实现 `OrderRepositoryImpl`
- [ ] **Step 3: Application Service**
    - 编写 `OrderCommandService` (编排事务)
- [ ] **Step 4: Interface Layer**
    - 编写 `OrderController` 和 DTO

---
**Tech Lead 提示**: 请确认以上拆分是否合理？如果没问题，我们将从 Step 1 开始。