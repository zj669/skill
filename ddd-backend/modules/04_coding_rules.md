# Phase 4: Construction Protocol (Coding)

本协议定义了 Antigravity 项目的代码构建标准。
**Tech Lead 指令**: 请严格区分"架构红线"与"用户配置"，优先满足架构红线。

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

## � Part 4: Execution Loop (执行回路)

**每个 Task 必须按以下回路执行，防止惯性滑坡：**

```
┌─────────────────────────────────────────────────────────────┐
│  For each task in tasks.md:                                 │
│                                                             │
│  1. READ: 读取 02_DetailedDesign.md 中对应的伪代码          │
│  2. LOCATE: 确定代码放在哪个包（参考 Part 5 包结构）        │
│  3. WRITE: 编写代码                                         │
│  4. CHECK: 自检（Part 6 对照检查）                          │
│  5. COMPILE: mvn compile 验证                               │
│  6. MARK: 更新 tasks.md 状态 [ ] → [x]                      │
│                                                             │
│  ⚠️ 任何步骤失败 → GOTO Phase X (Debugging)                │
└─────────────────────────────────────────────────────────────┘
```

### 自检问题 (每写完一个类必须问自己)

1. **这个类放对位置了吗？** (Domain 层不应有 @Service/@Component)
2. **Entity 有行为吗？** (只有 getter/setter → 贫血模型 → 重构！)
3. **业务逻辑在哪？** (如果在 AppService 里写了 if/else → 下沉到 Domain！)
4. **直接返回 Entity 了吗？** (Controller 返回 Entity → 改为 DTO！)

---

## 📦 Part 5: Package Structure (包结构模版)

```
com.example.{module}
├── interfaces/               # 接口层
│   ├── controller/
│   │   └── OrderController.java
│   ├── dto/
│   │   ├── request/
│   │   │   └── CreateOrderRequest.java
│   │   └── response/
│   │       └── OrderResponse.java
│   └── assembler/
│       └── OrderAssembler.java
│
├── application/              # 应用层
│   ├── service/
│   │   └── OrderApplicationService.java
│   └── command/
│       └── CreateOrderCmd.java
│
├── domain/                   # 领域层 (纯净！无框架注解)
│   ├── model/
│   │   ├── Order.java        # 聚合根
│   │   ├── OrderItem.java    # 实体
│   │   └── Money.java        # 值对象
│   ├── repository/
│   │   └── OrderRepository.java  # 接口
│   ├── service/
│   │   └── OrderDomainService.java
│   └── event/
│       └── OrderCreatedEvent.java
│
└── infrastructure/           # 基础设施层
    ├── persistence/
    │   ├── po/
    │   │   └── OrderPO.java
    │   ├── mapper/
    │   │   └── OrderMapper.java
    │   ├── repository/
    │   │   └── OrderRepositoryImpl.java
    │   └── converter/
    │       └── OrderConverter.java
    └── gateway/
        └── PaymentGatewayImpl.java
```

---

## �📝 Part 6: Code Pattern Examples (代码模版)

### 6.1 聚合根模版 (充血模型)

```java
// ✅ 正确：充血模型，业务逻辑内聚
package com.example.order.domain.model;

public class Order {
    private OrderId id;
    private List<OrderItem> items;
    private Money totalAmount;
    private OrderStatus status;
    
    // 工厂方法：创建订单
    public static Order create(List<OrderItem> items, User user) {
        if (items == null || items.isEmpty()) {
            throw new OrderEmptyException("订单项不能为空");
        }
        
        Money total = calculateTotal(items);
        if (user.isVip()) {
            total = total.multiply(0.9);
        }
        
        Order order = new Order();
        order.id = OrderId.generate();
        order.items = new ArrayList<>(items);
        order.totalAmount = total;
        order.status = OrderStatus.CREATED;
        return order;
    }
    
    // 行为方法：支付
    public void pay() {
        if (this.status != OrderStatus.CREATED) {
            throw new IllegalStateException("只有待支付订单可以支付");
        }
        this.status = OrderStatus.PAID;
    }
    
    // 行为方法：取消
    public void cancel() {
        if (this.status == OrderStatus.SHIPPED) {
            throw new IllegalStateException("已发货订单不能取消");
        }
        this.status = OrderStatus.CANCELLED;
    }
    
    private static Money calculateTotal(List<OrderItem> items) {
        return items.stream()
            .map(OrderItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }
}
```

### 6.2 应用服务模版 (编排者，不含业务逻辑)

```java
// ✅ 正确：应用服务只做编排，不含 if/else 业务逻辑
package com.example.order.application.service;

@Service
@RequiredArgsConstructor
public class OrderApplicationService {
    
    private final OrderRepository orderRepository;
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;
    
    @Transactional
    public OrderDTO createOrder(CreateOrderCmd cmd) {
        // 1. 获取依赖对象
        User user = userRepository.findById(cmd.getUserId())
            .orElseThrow(() -> new UserNotFoundException(cmd.getUserId()));
        
        // 2. 调用领域层（业务逻辑在这里！）
        Order order = Order.create(cmd.toOrderItems(), user);
        
        // 3. 持久化
        orderRepository.save(order);
        
        // 4. 发布事件
        eventPublisher.publishEvent(new OrderCreatedEvent(order.getId()));
        
        // 5. 转换返回
        return OrderAssembler.toDTO(order);
    }
}
```

### 6.3 仓储实现模版

```java
// ✅ 正确：仓储实现在 Infra 层
package com.example.order.infrastructure.persistence.repository;

@Repository
@RequiredArgsConstructor
public class OrderRepositoryImpl implements OrderRepository {
    
    private final OrderMapper orderMapper;
    private final OrderConverter converter;
    
    @Override
    public void save(Order order) {
        OrderPO po = converter.toPO(order);
        if (po.getId() == null) {
            orderMapper.insert(po);
        } else {
            orderMapper.updateById(po);
        }
    }
    
    @Override
    public Optional<Order> findById(OrderId id) {
        OrderPO po = orderMapper.selectById(id.getValue());
        return Optional.ofNullable(po).map(converter::toDomain);
    }
}
```

### 6.4 ❌ 反模式警示

```java
// ❌ 错误：贫血模型 + 业务逻辑散落在 Service
public class Order {
    private Long id;
    private BigDecimal amount;
    private String status;
    // 只有 getter/setter，没有行为！
}

@Service
public class OrderService {
    public void pay(Long orderId) {
        Order order = orderRepository.findById(orderId);
        // ❌ 业务逻辑散落在 Service！
        if ("CREATED".equals(order.getStatus())) {
            order.setStatus("PAID");  // ❌ 直接 set！
            orderRepository.save(order);
        }
    }
}
```

---

## ✅ Part 7: Pre-Flight Checklist (飞行前检查)

**生成每个 Task 的代码前，必须确认：**

| # | 检查项 | 通过? |
|---|--------|-------|
| 1 | 是否符合 Part 1 的架构分层？ | [ ] |
| 2 | 是否匹配 Part 2 的技术栈配置？ | [ ] |
| 3 | 是否满足 Part 3 的用户特殊约束？ | [ ] |
| 4 | Entity 是否有行为方法？(非贫血) | [ ] |
| 5 | 业务逻辑是否在 Domain 层？ | [ ] |
| 6 | Controller 是否只返回 DTO？ | [ ] |
| 7 | Repository 接口是否在 Domain 层？ | [ ] |

**如果任何一项为 No → 立即修正，不要提交！**