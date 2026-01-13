# Phase 3: Construction Protocol (Coding)

本协议定义了 Antigravity 项目的代码构建标准。
**Tech Lead 指令**: 请严格区分“架构红线”与“用户配置”，优先满足架构红线。

---

## 🏗️ Part 1: Architecture Iron Laws
**任何代码生成都必须死守以下物理定律：**

### 1. The Dependency Rule
* **Domain Layer (核心)**: 严禁依赖 `Spring Web`, `MyBatis`, `Persistence Annotations`。它是纯净的 Java POJO。
* **Application Layer**: 仅依赖 `Domain Layer`。负责事务 (`@Transactional`) 和编排。
* **Interface / Infra Layer**: 指向 `Application` 和 `Domain`。

### 2. The Anti-Anemia Rule
* ❌ **禁止**: 创建只包含 `@Data` 的贫血实体，业务逻辑散落在 Service 中。
* ✅ **强制**: 核心业务规则必须封装在 Entity / Domain Service 中。
    * *Example*: `order.pay()` 而不是 `service.setOrderStatus(PAID)`。

### 3. The Layer Boundary
* **Controller**: 只能返回 DTO，**严禁**直接返回 Entity。
* **Repository**: 接口定义在 Domain 层，实现类 (`Impl`) 必须在 Infra 层。

---

## 🛠️ Part 2: Tech Stack Configuration
**Agent 请读取以下配置来决定代码风格：**

> 用户可以在此区域修改默认设置 (填 `Yes/No` 或具体库名)

* **Lombok Usage**: `Yes` (使用 @Data, @Builder 等简化代码)
* **ORM Framework**: `MyBatis-Plus` (或 JPA / MyBatis)
* **JSON Library**: `Jackson`
* **Bean Mapping**: `MapStruct` (如果不使用，则用 BeanUtils)
* **Date Time**: `java.time.LocalDateTime` (严禁使用 java.util.Date)
* **API Documentation**: `Swagger/Knife4j` (Controller 需加注解)

---

## ⚡ Part 3: User Custom Constraints
**Agent 在生成代码前，必须检查此处是否有额外指令：**

> [!USER_RULES_START]
> (此处留空，等待用户填入特定要求。如果为空，则遵循标准风格。)
> [!USER_RULES_END]

---

## 📝 Implementation Checklist (执行步骤)
在生成每个 Task 的代码时，执行以下检查：
1.  [ ] 是否符合 Part 1 的架构分层？
2.  [ ] 是否匹配 Part 2 的技术栈配置？
3.  [ ] 是否满足 Part 3 的用户特殊约束？
4.  [ ] **Self-Correction**: 如果发现 Entity 只有 Getters/Setters，立即重构为充血模型。