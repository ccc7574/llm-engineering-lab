# T03: 拆解 Transformer Block，定位每个模块在系统里的职责

## 背景

系统已经能跑，团队也大致知道 attention 有用，但工程师对 `model.py` 仍然普遍有畏难情绪。代码一长，大家就默认“这是研究员写的，不要动”。这会直接阻塞后面的 SFT 和推理增强改造。

## 任务目标

- 把 Transformer block 拆成工程师可以讨论的几个部件
- 明确每个部件的输入输出和职责
- 为后续插入日志、可视化和改造点打基础

## 业务约束

- 不能停留在公式推导
- 必须映射到真实代码结构
- 每个模块最好都能单独描述副作用和调参影响

## 你需要改的代码

- `code/stage1_nanogpt_core/model.py`
- `code/stage1_nanogpt_core/debug_block.py`
- `assets/figures/transformer_block_flow.png`

## 交付标准

- 输出一张 block 级数据流图
- 解释 LayerNorm、attention、MLP、residual 各自职责
- 说明为什么 residual 对训练稳定和信息保留重要
- 标出后续 SFT 或推理增强可能会碰到的代码位置

## 原理补充

可以把一个 Transformer block 简化理解为:

1. 先规范化输入，降低训练不稳定
2. 通过 attention 从历史上下文中取信息
3. 通过 MLP 做位置内的非线性变换
4. 通过 residual 保留原始信息并方便深层优化

对工程师最重要的不是背公式，而是理解这些部件像什么:

- LayerNorm 像稳定接口的预处理
- attention 像内容寻址读取
- MLP 像局部特征变换器
- residual 像给后续模块保留原始通路

## 实验步骤

1. 在 forward 中打印关键 tensor 形状
2. 观察进入 block 前后的表示变化
3. 做一个禁用某个部件的 toy 对照实验
4. 记录 loss、采样质量和训练稳定性变化

## 结果解读

如果这一单写得好，读者后面再看 SFT、KV cache 或 verifier 时，就不会觉得一切都是“黑箱魔法”。

## 线上风险

- 只讲功能，不讲模块之间的配合关系
- 把 residual 的价值说成“只是避免梯度消失”
- 忽略实现细节和张量形状，导致读者无法下手改代码
