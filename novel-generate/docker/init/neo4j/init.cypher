// ============================================================
// Novel-Generate Neo4j 初始化脚本
// 包含：约束定义、索引创建、示例数据
// ============================================================

// ============================================================
// 1. 约束定义 (确保数据唯一性)
// ============================================================

// 角色名唯一
CREATE CONSTRAINT character_name IF NOT EXISTS
FOR (c:Character) REQUIRE c.name IS UNIQUE;

// 势力名唯一
CREATE CONSTRAINT faction_name IF NOT EXISTS
FOR (f:Faction) REQUIRE f.name IS UNIQUE;

// 物品ID唯一
CREATE CONSTRAINT item_id IF NOT EXISTS
FOR (i:Item) REQUIRE i.item_id IS UNIQUE;

// ============================================================
// 2. 索引创建 (提升查询性能)
// ============================================================

// 角色状态索引
CREATE INDEX character_status IF NOT EXISTS
FOR (c:Character) ON (c.status);

// 势力类型索引
CREATE INDEX faction_type IF NOT EXISTS
FOR (f:Faction) ON (f.type);

// ============================================================
// 3. 节点标签说明
// ============================================================
// 
// :Character - 角色节点
//   属性: name, level, status(alive/dead), spirit_root, spirit_power
//
// :Faction - 势力节点
//   属性: name, type(宗门/家族/势力/国家), power_level
//
// :Item - 物品节点  
//   属性: item_id, name, grade, type(武器/丹药/功法/杂物)
//
// :Location - 地点节点
//   属性: name, type(城市/秘境/宗门), danger_level

// ============================================================
// 4. 关系类型说明
// ============================================================
//
// 人物关系:
//   -[:KILLED {chapter: N}]->        A击杀B
//   -[:HATES {intensity: 1-100}]->   A仇恨B
//   -[:LOVES {intensity: 1-100}]->   A喜欢B
//   -[:ALLIED]->                     A与B结盟
//   -[:OWES {reason: "..."}]->       A欠B人情
//   -[:MASTER_OF]->                  A是B的师父
//   -[:STUDENT_OF]->                 A是B的徒弟
//
// 势力关系:
//   -[:BELONGS_TO {role: "长老"}]->  A属于B势力
//   -[:ENEMY_OF]->                   A势力敌对B势力
//   -[:ALLIED_WITH]->                A势力与B势力结盟
//
// 物品关系:
//   -[:OWNS]->                       A拥有物品B
//   -[:CREATED]->                    A创造了物品B

// ============================================================
// 5. 示例数据 (可选，用于测试)
// ============================================================

// 创建主角
MERGE (yefan:Character {name: '叶凡'})
SET yefan.level = '练气一层',
    yefan.status = 'alive',
    yefan.spirit_root = '木灵根',
    yefan.spirit_power = 100,
    yefan.novel_id = 'novel_001';

// 创建初始势力
MERGE (yunzong:Faction {name: '云霄宗'})
SET yunzong.type = '宗门',
    yunzong.power_level = 3,
    yunzong.novel_id = 'novel_001';

// 创建主角的初始物品
MERGE (sword:Item {item_id: 'item_001'})
SET sword.name = '破旧铁剑',
    sword.grade = '凡品',
    sword.type = '武器',
    sword.novel_id = 'novel_001';

// 建立关系
MATCH (yefan:Character {name: '叶凡'})
MATCH (sword:Item {item_id: 'item_001'})
MERGE (yefan)-[:OWNS]->(sword);

// 创建神秘老爷爷 (悬念人物)
MERGE (grandpa:Character {name: '戒指老爷爷'})
SET grandpa.status = 'dormant',
    grandpa.level = '未知',
    grandpa.novel_id = 'novel_001';

// 主角与老爷爷的关系
MATCH (yefan:Character {name: '叶凡'})
MATCH (grandpa:Character {name: '戒指老爷爷'})
MERGE (grandpa)-[:BOUND_TO {type: '金手指'}]->(yefan);
