# Phase 1: Blueprint Protocol (Deep Design)

本协议将通过多个子步骤引导完成从业务背景到具体落地的完整设计。

---

## 📋 Pre-Check (设计前检查)
**Logic**: 确保 Phase 0 的成果被正确继承，避免信息断层。

* **必须读取**: `.business/{Feature}/` 目录下的文件:
  - `Context Report` (技术栈、架构状态)
  - `DB_Schema.md` (现有表结构，如已生成)
* **风险确认**: 检查 Phase 0 的 Gap Analysis 是否有 🚨 WARN?
  - 如有缺失依赖，本阶段需规划引入方案

---

## 📅 Step 1.1: Context & Concepts (背景与概念)
**Goal**: 明确"我们在解决什么问题"以及"核心术语是什么"。

**Required Input (请回答):**
1.  **Project Background**: 用一句话描述这个功能/模块的业务背景。
2.  **Core Problem**: 它解决了用户的什么痛点？
3.  **Ubiquitous Language (通用语言)**:
    - 请列出 3-5 个核心业务术语（中英文对照）。
    - *Example*: `Product (商品)`, `SKU (库存单元)`, `Listing (上架单)`。

---

## 📅 Step 1.2: Strategic Modeling (战略建模)
**Goal**: 划分领域边界，识别聚合根。

**Required Input (请回答):**
1.  **Bounded Context (限界上下文)**: 这个功能属于哪个子域？(Core/Supporting/Generic)
2.  **Aggregate Root (聚合根)**: 谁是生命周期的管理者？
    - *Check*: 删除它，其他对象是否还有存在的意义？
3.  **Entities & VOs**:
    - 实体 (有唯一 ID): `________`
    - 值对象 (无 ID, 可替换): `________`
4.  **Domain Events**: 会触发什么领域事件？(e.g., `OrderPaidEvent`)
5.  **Domain Services**: 跨聚合的业务逻辑由谁承担？(如有)
6.  **Business Invariants (业务不变量)**:
    - 聚合根在任何时候都必须满足的规则
    - *Example*: "订单总金额不能为负数"、"库存扣减后不能小于 0"
    - *Why*: 防止贫血模型，确保业务逻辑内聚在实体中

---

## 📅 Step 1.3: Tactical Design (战术设计)
**Goal**: 定义接口交互与代码落地思路。

**Required Input (请回答):**
1.  **API Design**:
    | Method | URI | Description |
    |--------|-----|-------------|
    | POST   | /api/xxx | 创建xxx |
    | GET    | /api/xxx/{id} | 查询xxx |

2.  **Interaction Flow (关键交互)**:
    - 描述：Controller -> AppService -> Domain 的调用链路。
    - *重点*: 业务逻辑是否已下沉到 Domain？

3.  **Repository Interface (仓储接口)**:
    ```java
    public interface XxxRepository {
        void save(Xxx aggregate);
        Optional<Xxx> findById(XxxId id);
        // 其他查询方法...
    }
    ```

4.  **DTO Definition (传输对象定义)**:
    - Command (入参): `CreateXxxCmd`, `UpdateXxxCmd`
    - Query (出参): `XxxDTO`, `XxxDetailVO`
    - *Check*: 是否避免了将 Entity 直接暴露给前端？

5.  **Assembler/Converter Strategy**:
    - DTO -> Entity: 由 Assembler 或 MapStruct 转换
    - Entity -> DTO: 同上

6.  **Exception Mapping (异常映射)**:
    | 领域异常 | 错误码 | HTTP 状态码 | 提示信息 |
    |---------|--------|------------|----------|
    | XxxNotFoundException | 4001 | 404 | xxx不存在 |
    | XxxValidationException | 4002 | 400 | 参数校验失败 |

7.  **Architecture Check (架构自检)**:
    - [ ] 是否引入了防腐层 (ACL)？
    - [ ] 聚合根之间是否通过 ID 引用而不是对象引用？
    - [ ] 是否符合最终一致性？
    - [ ] 应用层是否只调用领域层暴露的 Service 和 Repository？
    - [ ] DTO 是否与 Entity 严格分离？

---

## 📅 Step 1.4: Data Modeling (数据建模)
**Goal**: 设计数据库表结构，为持久化做准备。

**Required Input (请回答):**
1.  **Table Design (表设计)**:
    | 表名 | 说明 | 对应领域对象 |
    |------|------|-------------|
    | t_xxx | xxx表 | XxxAggregate |

2.  **Field Design (字段设计)**:
    ```sql
    CREATE TABLE t_xxx (
        id BIGINT PRIMARY KEY COMMENT '主键',
        -- 其他字段...
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    ```

3.  **Primary Key Strategy (主键策略)**:
    - [ ] 自增 ID
    - [ ] 雪花算法
    - [ ] UUID

4.  **Index Plan (索引规划)**:
    - 唯一索引: `________`
    - 普通索引: `________`

5.  **Relation Check (关联检查)**:
    - 与现有表的关联关系 (参考 DB_Schema.md)

---

## 📅 Step 1.5: Dependency Planning (依赖规划)
**Goal**: 处理 Phase 0 Gap Analysis 中发现的依赖缺失。

*(仅当 Phase 0 存在 🚨 WARN 时执行)*

* **新增依赖清单**:
    | GroupId | ArtifactId | Version | 用途 |
    |---------|------------|---------|------|
    | xxx | xxx | x.x.x | 用于... |

* **配置变更**:
    - `application.yml` 需要新增哪些配置项？

---

## 📝 Final Deliverable (最终交付物)

完成上述步骤后，生成 `.business/{Feature}/01_Design.md`，包含以下结构：

```markdown
# {Feature} 技术设计说明书

## 1. 背景与目标
- 业务背景: ...
- 解决问题: ...

## 2. 通用语言
| 术语 | 英文 | 说明 |
|------|------|------|

## 3. 领域建模
### 3.1 限界上下文
### 3.2 聚合根
### 3.3 实体与值对象
### 3.4 领域事件
### 3.5 领域服务
### 3.6 业务不变量

## 4. API 设计
| Method | URI | Description |

## 5. 仓储接口
```java
// Repository interface definitions
```

## 6. DTO 与异常设计
### 6.1 传输对象
### 6.2 异常映射表

## 7. 数据库设计 (如有)
### 7.1 表结构
### 7.2 索引规划

## 8. 依赖变更 (如有)

## 9. 关键测试场景 (TDD 思考)
| 场景 | Given | When | Then |
|------|-------|------|------|
| 正常路径 | ... | ... | ... |
| 边界条件 | ... | ... | ... |

## 10. 架构自检清单
- [ ] ...
```

---

## 🛑 Stop Point (用户审核节点)

**设计文档生成后:**
1. 输出: "📋 设计文档已生成：`.business/{Feature}/01_Design.md`"
2. 询问: "请审核设计文档。输入 **'通过'** 进入任务拆解阶段 (Phase 2)。"
3. **严禁**: 在用户确认前进入下一阶段。