# 实施计划：桌面工作台 UI 重构

## 概览

本计划把现有单文件 Canvas 自绘 UI 重构为模块化的 Tkinter/ttk 双栏工作台。转换内核、领域模型、顺序批处理、线程安全事件通道、安全校验、输出协议和 Windows 发布链保持不变。实施采用兼容壳和垂直切片，每个任务结束时应用均应可启动、可测试、可回滚。

详细交互合同见 [桌面工作台 UI 重构规格](../docs/ui-redesign-spec.md)。

## 已确认架构决策

- 保留 Python 3.13 + Tkinter/Tcl-Tk，不增加第三方 UI 依赖。
- 以 `ttk` 原生控件承载交互，以 Canvas 仅承载确有需要的轻量装饰或进度表现。
- 保留 `office_to_markdown.app.MainWindow` 和 `main()` 兼容入口，逐步把实现委派给 `ui/` 包。
- 不改变 `BatchConversionService`、`ConversionOptions`、`BatchItem`、`BatchResult` 的领域合同。
- 先建立行为测试，再替换界面；不得用截图相似替代行为验证。
- 递归默认值冲突作为 Task 0 门禁，不在重构中静默处理。

## 依赖图

```text
Task 0 产品事实门禁
  -> Task 1 行为契约测试
      -> Task 2 UI 状态与主题基础
          -> Task 3 设置面板切片
          -> Task 4 队列面板切片
              -> Task 5 主窗口与任务生命周期集成
                  -> Task 6 可访问性和响应式验证
                      -> Task 7 发布与文档收口
```

## Phase 0：先消除歧义

### Task 0：确认递归扫描默认值

**Description：** 用户已确认“包含子文件夹”默认关闭，以解决代码与产品文档冲突。本任务单独确定产品事实，不和视觉重构混合提交。

**Acceptance criteria：**

- [x] 用户明确选择默认关闭。
- [x] 代码、测试、产品设计和重构规格使用同一默认值。
- [x] 行为变化单独记录在 CHANGELOG，不伪装成 UI 调整。

**Verification：** 针对 `MainWindow`/`UiState` 初始值和 `discover_sources` 调用参数添加断言。

**Dependencies：** 无；已完成。  
**Files likely touched：** `app.py` 或 `ui/state.py`、`tests/test_ui.py`、`docs/product-design.md`、`docs/ui-redesign-spec.md`、`CHANGELOG.md`。  
**Estimated scope：** S。

## Phase 1：锁定兼容行为

### Task 1：建立 UI 行为契约测试

**Description：** 在移动任何界面代码前，将现有输入、选项、任务状态和结果操作转换为独立、可读的行为测试；减少对 Canvas 坐标和私有绘制细节的断言。

**Acceptance criteria：**

- [x] 七个布尔选项和路径/标签正确映射到 `ConversionOptions`。
- [x] 文件去重、顺序、选中结果和安全打开行为有测试。
- [x] 空队列、可开始与运行中的可用动作有明确断言；完整阶段矩阵在 Task 2 状态对象中继续锁定。

**Verification：**

- [ ] `.\.venv-ui\Scripts\python.exe -m pytest tests\test_ui.py --basetemp .\work\pytest-ui -p no:cacheprovider`
- [ ] 既有 `tests/test_conversion.py` 继续通过。

**Dependencies：** Task 0。  
**Files likely touched：** 新增 `tests/test_ui.py`，小幅调整 `tests/test_conversion.py`。  
**Estimated scope：** S。

### Checkpoint A：契约基线

- [x] UI 契约测试能在共享隐藏 Tk 窗口中稳定执行。
- [x] 无源码行为变化。
- [x] 完整 pytest 和 Ruff 通过。

## Phase 2：建立可维护的 UI 基础

### Task 2：提取 UI 状态与主题

**Description：** 创建 `ui/state.py` 和 `ui/theme.py`。状态对象管理 Tk 变量、队列、结果、选中项和任务阶段；主题集中定义 ttk 样式与设计令牌。

**Acceptance criteria：**

- [ ] 状态初始值与当前产品合同一致。
- [ ] 任务阶段转换是显式方法，不散落字符串判断。
- [ ] 颜色、字号、间距和控件尺寸不再定义在多个组件中。

**Verification：**

- [ ] 状态单元测试无需执行真实转换。
- [ ] 创建/销毁隐藏 Tk 根窗口无异常。
- [ ] Ruff 通过。

**Dependencies：** Task 1。  
**Files likely touched：** 新增 `ui/__init__.py`、`ui/state.py`、`ui/theme.py`、`tests/test_ui.py`。  
**Estimated scope：** M。

### Task 3：实现设置面板垂直切片

**Description：** 使用 ttk 实现输出目录、Obsidian 和 PowerPoint 设置，并完整接入现有变量、对话框和选项构造，不等待其他面板完成。

**Acceptance criteria：**

- [ ] 输出目录、默认目录、Vault 和标签交互与现有行为一致。
- [ ] Obsidian 子选项的启用/禁用与校验一致。
- [ ] PNG/PDF 选项保持独立且默认关闭。

**Verification：**

- [ ] 面板状态和 `ConversionOptions` 映射测试通过。
- [ ] 键盘 Tab、Space 和 Enter 手工检查通过。
- [ ] 1040px 宽度下文本和控件无重叠。

**Dependencies：** Task 2。  
**Files likely touched：** 新增 `ui/settings_panel.py`，更新 `ui/state.py`、`tests/test_ui.py`。  
**Estimated scope：** M。

### Checkpoint B：设置切片

- [ ] 新设置面板可以在独立测试宿主创建。
- [ ] 所有选项可构造出与旧 UI 相同的 `ConversionOptions`。
- [ ] 完整 pytest 和 Ruff 通过。

## Phase 3：文件队列与主流程

### Task 4：实现队列面板垂直切片

**Description：** 使用 `ttk.Treeview` 呈现有序文件队列、类型、大小和状态，连接添加文件、扫描文件夹、选择项、结果摘要与受控结果动作。

**Acceptance criteria：**

- [ ] 队列视觉顺序与实际 `sources` 顺序严格一致。
- [ ] 20、100、1000 项可滚动，状态更新不重建无关业务对象。
- [ ] 只有含 `ConversionResult` 的成功/警告项可打开输出和报告。

**Verification：**

- [ ] 队列填充、去重、选择和事件更新自动化测试通过。
- [ ] 长文件名、中文路径、未知文件大小手工检查通过。
- [ ] 打开动作继续只接受结果模型返回路径。

**Dependencies：** Task 2。  
**Files likely touched：** 新增 `ui/queue_panel.py`，更新 `ui/state.py`、`tests/test_ui.py`。  
**Estimated scope：** M。

### Task 5：集成主窗口与任务生命周期

**Description：** 创建双栏 `MainWindow` 和底部状态栏，接入文件对话框、后台线程、事件轮询、开始、取消、完成汇总和异常恢复；旧 `app.py` 变为兼容入口。

**Acceptance criteria：**

- [ ] 所有 Tk 控件只在主线程更新。
- [ ] 开始、取消、完成、部分失败和意外异常状态与规格矩阵一致。
- [ ] 旧入口和 `from office_to_markdown.app import MainWindow` 继续可用。

**Verification：**

- [ ] 使用假 `BatchConversionService` 验证完整 UI 生命周期。
- [ ] 混合状态队列计数与 `BatchResult` 一致。
- [ ] `python -m office_to_markdown` 可创建并关闭真实窗口。

**Dependencies：** Task 3、Task 4。  
**Files likely touched：** 新增 `ui/main_window.py`、`ui/status_bar.py`，重构 `app.py`，更新 `tests/test_ui.py`、`tests/test_conversion.py`。  
**Estimated scope：** M。

### Checkpoint C：端到端 UI

- [ ] 空状态、单文件、多文件、冲突、失败和取消流程可用。
- [ ] 现有转换核心文件没有因 UI 重构而修改行为。
- [ ] 完整 pytest 和 Ruff 通过。

## Phase 4：可访问性、窗口与发布

### Task 6：完成键盘、高 DPI 和响应式验证

**Description：** 校准布局、焦点顺序、状态文字、列宽和窗口约束，在 Windows 常用缩放与窗口尺寸下完成真实 UI 验证。

**Acceptance criteria：**

- [ ] 键盘可完成添加后除系统文件对话框外的主流程。
- [ ] 100%、125%、150%、200% 缩放下无文字遮挡和不可达控件。
- [ ] 默认、最小、最大化和还原状态下双栏与底栏不重叠。

**Verification：**

- [ ] 自动化布局断言不依赖具体像素绘制实现。
- [ ] 四种缩放和四种窗口状态记录手工结果。
- [ ] 使用任务管理器或简单采样确认空闲状态无持续高 CPU。

**Dependencies：** Task 5。  
**Files likely touched：** `ui/theme.py`、`ui/main_window.py`、各面板、`tests/test_ui.py`、`docs/sample-validation-log.md`。  
**Estimated scope：** M。

### Task 7：完成构建、安装和文档收口

**Description：** 执行完整自动化、静态检查、PyInstaller、安装/卸载和新产物启动验证；随后把规划文档和项目事实更新为实际结果。

**Acceptance criteria：**

- [ ] 完整测试、Ruff、构建和安装包均成功。
- [ ] 新 exe 与安装后程序能创建主窗口并完成基础转换。
- [ ] 核心文档只记录经过验证的最终结构和结果。

**Verification：**

- [ ] `.\.venv-ui\Scripts\python.exe -m pytest --basetemp .\work\pytest -p no:cacheprovider`
- [ ] `.\.venv-ui\Scripts\python.exe -m ruff check .`
- [ ] `scripts/build.ps1`
- [ ] `scripts/package-installer.ps1`
- [ ] 手工安装、启动、转换、卸载冒烟测试。

**Dependencies：** Task 6。  
**Files likely touched：** `PROJECT.md`、`ARCHITECTURE.md`、`DECISIONS.md`、`CHANGELOG.md`、`README.md`、`docs/problems.md`、`docs/sample-validation-log.md`。  
**Estimated scope：** M。

### Checkpoint D：发布候选

- [ ] 所有规格验收条件满足。
- [ ] 无新增依赖、网络、遥测或隐私数据持久化。
- [ ] 构建产物时间戳和运行时内容来自本次构建。
- [ ] 未通过项目和剩余风险被明确记录。

## 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| ttk 视觉在不同 Windows/Tk 版本略有差异 | 中 | 优先保证布局和语义；用项目 `.venv-ui` 和分发产物双重验证 |
| Treeview 视觉顺序与处理顺序漂移 | 高 | 禁止交互排序；以 `UiState.sources` 为唯一处理顺序并测试 |
| 重构时改变选项默认值 | 高 | Task 1 先锁定映射；递归默认关闭已在 Task 0 单独确认 |
| 后台线程触碰 Tk 控件 | 高 | 保持 `queue.Queue` 事件通道；用假服务测试线程边界 |
| 原生控件主题造成禁用文字对比不足 | 中 | 在真实 Windows 主题和缩放下手工验证 |
| `app.py` 拆分破坏 PyInstaller 隐式导入 | 高 | 保留兼容入口；Task 7 完整构建和新 exe 启动验证 |
| 旧 Canvas 测试与新结构强耦合 | 中 | 迁移为行为和几何约束测试，不保留无价值的私有坐标断言 |
| 一次性重写导致难以定位回归 | 高 | 每个任务独立提交或独立检查点，禁止跨阶段批量落地 |

## Codex 执行规则

1. 每次只执行一个 Task；开始前重新读取本计划、规格和相关源码。
2. 每个 Task 先写或调整测试，再实现，再运行聚焦测试和 Ruff。
3. 完成 Checkpoint 前运行完整测试；失败不得继续下一阶段。
4. 不修改 `adapters.py`、`markdown.py`、`service.py`、`batch.py` 的业务行为，除非发现阻塞性缺陷并先向用户说明。
5. 不删除旧 Canvas 实现，直到新主窗口已通过 Checkpoint C；迁移完成后通过 Git 历史回滚，不保留双实现开关。
6. 不安装新包；确需依赖必须暂停并获得用户确认。
7. 不使用真实私人 Office 文件作为测试 fixture。
8. 每个交付单元同步受影响文档并按全局 SOP 做脱敏归档。

## 实施前待确认

- [x] “包含子文件夹”默认关闭（Task 0 已确认）。
- [ ] 目标版本号是否采用 v0.4.0；若不确认，实施期间继续记入 Unreleased。
