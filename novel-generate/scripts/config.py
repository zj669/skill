"""
Novel-Generate 配置文件
战力锚点与系统常量

⚠️ 占位符版本 - 仅定义接口规范
"""

# ============================================================
# 境界体系 (Cultivation Levels)
# ============================================================

LEVELS = {
    "练气": {
        "sub_levels": 9,  # 练气一层到九层
        "base_lifespan": 100,
        "lifespan_per_level": 0,
        "power_range": (1, 100),
    },
    "筑基": {
        "sub_levels": 3,  # 初期、中期、后期
        "base_lifespan": 200,
        "lifespan_per_level": 50,
        "power_range": (100, 500),
    },
    "金丹": {
        "sub_levels": 3,
        "base_lifespan": 500,
        "lifespan_per_level": 100,
        "power_range": (500, 2000),
    },
    "元婴": {
        "sub_levels": 3,
        "base_lifespan": 1000,
        "lifespan_per_level": 200,
        "power_range": (2000, 10000),
    },
    "化神": {
        "sub_levels": 3,
        "base_lifespan": 2000,
        "lifespan_per_level": 500,
        "power_range": (10000, 50000),
    },
}

# ============================================================
# 货币体系 (Currency System)
# ============================================================

CURRENCY = {
    "金币": 1,
    "灵石": 100,  # 1灵石 = 100金
    "中品灵石": 10000,  # 1中品 = 100下品
    "上品灵石": 1000000,
}

# ============================================================
# 物品品阶 (Item Grades)
# ============================================================

ITEM_GRADES = ["凡品", "灵品", "宝品", "仙品", "神品"]

ITEM_GRADE_POWER = {
    "凡品": 1.0,
    "灵品": 2.0,
    "宝品": 5.0,
    "仙品": 20.0,
    "神品": 100.0,
}

# ============================================================
# 战斗系统 (Combat System)
# ============================================================

# 跨境界战力系数
CROSS_LEVEL_FACTOR = 10  # 高一大境界 = 10倍基础战力

# 属性相克
ELEMENT_COUNTER = {
    "金": "木",
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
}

ELEMENT_BONUS = 1.5  # 克制伤害加成


# ============================================================
# 爽点曲线 (Emotional Curve)
# ============================================================

EMO_THRESHOLDS = {
    "consecutive_low_trigger": 3,  # 连续3章低谷触发强制爽点
    "low_score": 20,  # 低于此值视为低谷
    "high_score": 60,  # 高于此值视为高潮
}


# ============================================================
# 悬念管理 (Hook Management)
# ============================================================

HOOK_CONFIG = {
    "max_unresolved": 10,  # 最多未回收悬念数
    "force_resolve_interval": 20,  # 每20章强制回收1个
}


# ============================================================
# 辅助函数
# ============================================================

def get_power_range(level_name: str) -> tuple:
    """获取境界对应的战力范围"""
    for level, config in LEVELS.items():
        if level in level_name:
            return config["power_range"]
    return (0, 0)


def can_defeat(attacker_level: str, defender_level: str, attacker_items: list = None) -> bool:
    """
    判断攻击者是否有可能击败防御者
    返回 True 表示合理，False 表示战力越界
    """
    attacker_power = get_power_range(attacker_level)[1]
    defender_power = get_power_range(defender_level)[0]
    
    # 考虑装备加成
    if attacker_items:
        # TODO: 根据装备计算加成
        pass
    
    # 超过2个大境界视为不合理
    if defender_power > attacker_power * (CROSS_LEVEL_FACTOR ** 2):
        return False
    
    return True
