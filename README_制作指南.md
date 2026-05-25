# ExtractionGame 制作指南

这是一个基于 UE 第三人称蓝图模板的搜打撤作业项目。目标是先完成 5 分钟单局的最小可玩版本：进入场景、探索、开宝箱拿金币、打怪、4 分钟刷逃生门、触碰逃生门结算。

## 现在怎么打开

1. 双击 `ExtractionGame.uproject`。
2. 如果 UE 提示版本转换，选择用 UE 5.7 打开。
3. 打开默认地图 `Content/ThirdPerson/Lvl_ThirdPerson`。
4. 先另存为 `Content/Maps/LV_Extraction`，后续都在新地图里做。

## 推荐目录

在 Content 下创建这些文件夹：

- `Blueprints/Core`
- `Blueprints/Player`
- `Blueprints/Enemy`
- `Blueprints/Interact`
- `Blueprints/UI`
- `Blueprints/Spawn`
- `Maps`
- `VFX`
- `Audio`

## 第一阶段：角色与全局变量

打开 `BP_ThirdPersonCharacter`，添加变量：

- `Health`，Float，默认 100
- `MaxHealth`，Float，默认 100
- `Gold`，Integer，默认 0
- `CombatPower`，Integer，默认 1
- `bIsDead`，Boolean，默认 false

添加函数：

- `AddGold(Amount:int)`：Gold += Amount，并刷新 UI
- `TakeDamage(Damage:float)`：Health -= Damage；Health <= 0 时触发死亡结算
- `AddCombatPower()`：CombatPower += 1

攻击先做简化版：

- 在 Input 里绑定鼠标左键或键盘 `J`
- 播放攻击动画可先不做，先用角色前方 Sphere Trace 检测怪物
- 命中怪物后调用怪物的 `TakeDamage`

## 第二阶段：100m x 100m 场景

UE 单位是厘米，所以 100m = 10000cm。

地图要求：

- 地面尺寸约 `10000 x 10000`
- 至少 1 层上层结构：平台 + 楼梯
- 放 10 个宝箱点
- 放 5 个怪物刷新点
- 放 2 个逃生门点位
- 添加 `NavMeshBoundsVolume` 覆盖整个可行走区域

检查方式：

- 按 `P` 查看绿色寻路区域
- 玩家和怪物不能卡在楼梯、平台边缘、宝箱旁边

## 第三阶段：宝箱 BP_Chest

创建蓝图 `BP_Chest`，类型 Actor。

组件：

- StaticMesh：箱子模型，可先用 Cube 替代
- Box Collision：交互范围
- Timeline：打开动画，时长 1 秒

变量：

- `bOpened`，Boolean，默认 false
- `bOpening`，Boolean，默认 false
- `OpenTime`，Float，默认 1.0

逻辑：

- 玩家进入 Box Collision：开始 1 秒打开流程
- 玩家离开 Box Collision：如果还没打开，停止打开流程
- 1 秒完成后：随机金币 `Random Integer in Range 10-50`
- 调用玩家 `AddGold`
- 设置 `bOpened = true`
- 播放开箱音效/特效可放到选做

## 第四阶段：怪物 BP_Monster

创建蓝图 `BP_Monster`，父类 Character。

变量：

- `Health`，Float，默认 50
- `AttackDamage`，Float，默认 10
- `AttackRange`，Float，默认 150
- `DetectRange`，Float，默认 1200
- `ChaseLimit`，Float，默认 2000
- `bIsElite`，Boolean，默认 false

必做 AI：

- 创建 `AIController_Monster`
- 创建 `BT_Monster`
- 创建 `BB_Monster`
- 使用行为树实现：巡逻 -> 发现玩家 -> 追击 -> 攻击
- 地图里放 `NavMeshBoundsVolume`

简化实现建议：

- 巡逻：在出生点附近随机点 `AI Move To`
- 发现玩家：距离小于 `DetectRange`
- 追击：`AI Move To Player`
- 攻击：距离小于 `AttackRange`，每 1 秒扣玩家生命
- 怪物死亡：玩家获得 20 金币，战斗力 +1

## 第五阶段：逃生门 BP_ExitDoor

创建蓝图 `BP_ExitDoor`，类型 Actor。

组件：

- StaticMesh：门或传送门模型
- Box Collision：逃生判定
- Niagara / Particle：逃生门特效

默认设置：

- 开始时隐藏，Collision 关闭
- 第 4 分钟时显示，Collision 开启，播放特效

触碰逻辑：

- 玩家进入 Box Collision
- 如果游戏未结束且倒计时大于 0
- 调用 GameMode 的 `WinGame`

## 第六阶段：游戏流程 BP_ExtractionGameMode

建议复制 `BP_ThirdPersonGameMode`，命名为 `BP_ExtractionGameMode`。

变量：

- `MatchTime`，Integer，默认 300
- `ExitSpawnTime`，Integer，默认 240
- `CurrentTime`，Integer，默认 300
- `bGameEnded`，Boolean，默认 false
- `ExitDoors`，Actor Array

BeginPlay：

- 创建主 UI
- 设置 1 秒循环 Timer
- CurrentTime 从 300 开始每秒 -1
- 当 CurrentTime == 60 时显示逃生门，因为此时已经经过 4 分钟
- 当 CurrentTime <= 0 时游戏失败

函数：

- `ShowExitDoors()`
- `WinGame()`
- `LoseGame()`
- `EndGame(ResultText)`

## 第七阶段：UI

创建：

- `WBP_MainHUD`
- `WBP_Result`
- `WBP_Login`

`WBP_MainHUD` 显示：

- 玩家生命条
- 当前金币数
- 倒计时 `MM:SS`

`WBP_Result` 显示：

- 成功逃生 / 死亡失败 / 时间耗尽
- 最终金币数
- 返回主界面按钮

`WBP_Login` 显示：

- 游戏标题
- 开始游戏按钮

## 交付检查表

- [ ] 使用 UE 第三人称角色
- [ ] WSAD 移动、鼠标旋转
- [ ] 角色能攻击
- [ ] 场景约 100m x 100m
- [ ] 至少一层地面 + 一层上层结构
- [ ] 10 个宝箱
- [ ] 5 个怪物刷新点
- [ ] 2 个逃生门点位
- [ ] 怪物巡逻、发现、追击、攻击
- [ ] 怪物能扣玩家血
- [ ] 玩家生命为 0 游戏结束
- [ ] 宝箱靠近打开，1 秒内离开会打断
- [ ] 宝箱随机给 10-50 金币
- [ ] 击杀怪物给 20 金币和战斗力 +1
- [ ] 第 4 分钟刷逃生门
- [ ] 触碰逃生门成功逃生
- [ ] UI 显示生命、金币、倒计时
- [ ] 结算界面显示最终金币

## 今天的最小任务

今天只完成这些：

1. 打开项目。
2. 把默认地图另存为 `LV_Extraction`。
3. 搭一个 10000 x 10000 的灰盒地图。
4. 添加玩家变量 `Health / Gold / CombatPower`。
5. 做一个 `BP_Chest`，能 1 秒打开并加金币。
6. 做一个 `WBP_MainHUD`，显示金币和生命。

完成这六步，就已经有作业原型的第一块骨架了。
