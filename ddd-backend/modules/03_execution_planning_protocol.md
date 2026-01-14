# Phase 3: Execution Planning Protocol (任务规划)

将详细设计转化为可执行的任务清单，输出 `tasks.md` 供 AI 追踪进度。

---

## 📋 Pre-Check (规划前检查)

* **必须读取**: 
  - `.business/{Feature}/01_Design.md` (战略设计)
  - `.business/{Feature}/02_DetailedDesign.md` (详细设计)
* **确认详细设计已通过审核**

---

## 拆解原则

1.  **先核心后外围**: 先写 Domain (Entity/VO)，再写 Infra (RepoImpl)，最后写 App/API。
2.  **依赖顺序**: 永远不要先写依赖方。例如：在 `OrderRepository` 接口定义出来之前，不要写 `OrderService`。
3.  **小步提交**: 每个任务的代码量不应超过 1 个核心类文件。
4.  **可验证性**: 每个 Step 完成后应能通过编译，或能写单元测试验证。

---

## DDD 分层任务顺序

按照 DDD 分层架构，任务应遵循以下顺序：

```
Step 1: Domain Layer (领域层)
    ├── 实体 (Entity)
    ├── 值对象 (ValueObject)
    ├── 聚合根 (Aggregate Root)
    ├── 领域事件 (Domain Event)
    ├── 仓储接口 (Repository Interface)
    └── 领域服务 (Domain Service)
        ↓
Step 2: Infrastructure Layer (基础设施层)
    ├── 持久化对象 (PO/DO)
    ├── Mapper 接口
    ├── 仓储实现 (Repository Impl)
    └── 外部服务网关 (Gateway Impl)
        ↓
Step 3: Application Layer (应用层)
    ├── 应用服务 (Application Service)
    ├── DTO/Command/Query
    └── Assembler (转换器)
        ↓
Step 4: Interface Layer (接口层)
    ├── Controller
    ├── Request/Response VO
    └── 参数校验
```

---

## 📝 输出格式

### 📄 交付物: `tasks.md`

保存到 `.business/{Feature}/tasks.md`，使用标准 Checklist 格式：

```markdown
# {Feature} 任务清单

## 概要
- 总任务数: X
- 预估工时: X 小时
- 涉及文件: X 个

---

## Step 1: Domain Layer
- [ ] 1.1 创建聚合根 `Order.java` <!-- id: 1.1 -->
    - 包含 `create()`, `pay()`, `cancel()` 行为
    - 实现业务不变量校验
- [ ] 1.2 创建值对象 `Money.java`, `Address.java` <!-- id: 1.2 -->
- [ ] 1.3 定义仓储接口 `OrderRepository.java` <!-- id: 1.3 -->
- [ ] 1.4 定义领域异常 `OrderNotFoundException.java` <!-- id: 1.4 -->

## Step 2: Infrastructure Layer
- [ ] 2.1 创建 PO `OrderPO.java` <!-- id: 2.1 -->
- [ ] 2.2 创建 Mapper `OrderMapper.java` <!-- id: 2.2 -->
- [ ] 2.3 实现仓储 `OrderRepositoryImpl.java` <!-- id: 2.3 -->
- [ ] 2.4 创建转换器 `OrderConverter.java` <!-- id: 2.4 -->

## Step 3: Application Layer
- [ ] 3.1 创建 Command `CreateOrderCmd.java` <!-- id: 3.1 -->
- [ ] 3.2 创建 DTO `OrderDTO.java` <!-- id: 3.2 -->
- [ ] 3.3 创建应用服务 `OrderApplicationService.java` <!-- id: 3.3 -->
- [ ] 3.4 创建 Assembler `OrderAssembler.java` <!-- id: 3.4 -->

## Step 4: Interface Layer
- [ ] 4.1 创建 Controller `OrderController.java` <!-- id: 4.1 -->
- [ ] 4.2 创建 Request/Response VO <!-- id: 4.2 -->
```

---

## 任务编写规范

### 任务 ID 格式
使用 `<!-- id: X.X -->` 注释标记任务 ID，便于 AI 追踪：
- `1.1`, `1.2` → Step 1 的子任务
- `2.1`, `2.2` → Step 2 的子任务

### 任务状态标记
- `[ ]` → 待执行
- `[/]` → 进行中
- `[x]` → 已完成

### 任务描述要求
每个任务应包含：
- 文件名（带 `.java` 后缀）
- 关键职责（一句话描述）
- 依赖关系（如有）

---

## 🛑 Stop Point (用户审核节点)

**任务规划完成后:**
1. 输出: "📋 任务清单已生成：`.business/{Feature}/tasks.md`"
2. 询问: "请审核任务清单。输入 **'开始'** 进入编码阶段 (Phase 4)。"
3. **严禁**: 在用户确认前开始编码。

---

## 🔄 与其他协议的集成

```
Phase 1: 战略设计 → 01_Design.md
    ↓
Phase 2: 详细设计 → 02_DetailedDesign.md
    ↓
Phase 3: 任务规划 → tasks.md  ← 当前阶段
    ↓
Phase 4: 编码实现 (逐个完成 tasks.md 中的任务)
    ↓
Phase 5: 测试验收 (引用 tasks.md 确认范围)
```
