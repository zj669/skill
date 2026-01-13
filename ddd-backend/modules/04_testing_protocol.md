# Phase 4: Quality Protocol (Testing)

**Tech Lead 指令**: 测试不是为了证明代码“能跑”，而是为了证明代码“在任何情况下都不会崩”。
Agent 在编写测试前，必须读取本协议。

---

## 🏆 Part 1: The Golden Laws 

### 1. The Package Location Rule
* **规则**: 测试类 (`src/test/java/...`) 的包路径，必须与主启动类 (`@SpringBootApplication`) 所在的包路径**完全一致**或为其**子包**。
* **原因**: Spring Boot 的 `@SpringBootTest` 默认只扫描当前包及其子包。路径不对会导致 `BeanDefinitionOverrideException` 或 `NoSuchBeanDefinitionException`。
    * ✅ Correct: `com.antigravity.order.domain.OrderTest` (启动类在 `com.antigravity.order`)
    * ❌ Wrong: `com.test.OrderTest`

### 2. The Layer Isolation Rule 
* **Domain Layer**: 必须写 **Unit Test**。
    * **禁止**: 启动 Spring Context。
    * **工具**: 仅使用 JUnit5 + Mockito。测试纯 POJO 的业务逻辑。
* **App/Infra Layer**: 必须写 **Integration Test**。
    * **允许**: 使用 `@SpringBootTest` 启动容器。
    * **覆盖**: 验证 SQL、Redis 操作、事务回滚。

### 3. The Assert Independence Rule 
* 每个测试方法 (`@Test`) 必须是独立的，不能依赖其他测试方法的执行顺序。
* 严禁在测试代码中使用 `System.out.println` 人肉验证，必须使用 `Assert`。

---

## ⚙️ Part 2: Testing Stack Configuration 

**Agent 请读取以下配置来决定测试代码风格：**

> 用户可以修改默认设置 (Yes/No 或具体库名)

* **Test Framework**: `JUnit 5` (Jupiter)
* **Assertion Lib**: `AssertJ` (推荐使用 `assertThat(...)` 风格，比 JUnit 原生断言更易读)
* **Mocking Lib**: `Mockito`
* **Integration DB**: `H2 (In-Memory)` (或 `TestContainers` + `Docker`)
* **JSON Path**: `Yes` (用于验证 Controller 返回的 JSON 结构)

---

## 📝 Part 3: Execution Protocol 

**Agent 必须按照以下步骤引导用户：**

### Step 4.1: The Test Matrix
不要一上来就写代码！先列出你要测什么。请要求输出以下表格：

| Case ID | Layer | Scenario (场景) | Input Data | Expected (预期) |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | Domain | 订单金额计算 | Items=[$10, $20], VIP=True | Total=$27 (9折) |
| TC-02 | Domain | 支付已取消订单 | Order.status=CANCELLED | Throw `BizException` |
| TC-03 | Infra | 根据ID查询订单 | ID=999 | Return Optional.empty |
| TC-04 | API | 创建订单参数校验 | Qty=-1 | HTTP 400 Bad Request |

### Step 4.2: Implementation
1.  **先写 Unit Test**: 覆盖 Domain 层所有分支。
2.  **后写 Integration Test**: 验证 Repository 和 Controller。
3.  **自检**: 再次确认 `package` 声明是否符合 Golden Law。

---

## 🛡️ Self-Correction Checklist

在输出测试代码前，Agent 必须自问：
1.  [ ] 这个 `@SpringBootTest` 类放在了正确的包里吗？
2.  [ ] 我是否在单元测试里滥用了 `@Autowired`？(Domain测试不应该用它)
3.  [ ] 我是否验证了异常情况？(例如 `assertThrows`)