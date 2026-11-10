---
name: nexus-plugin-development
description: 使用随附的 Nexus 插件 SDK 开发、修改、打包或排查插件；在涉及 plugin.json、宿主能力、工具与技能、插件页面或独立 Python/Node 服务时使用。
---

# Nexus 插件开发

插件 SDK 的完整独立副本位于本技能旁的`sdk/`。以其中的文档、客户端和示例为接口依据，不要求用户提供 Nexus 源码，也不要从其他版本或旧插件猜测公开接口。

## SDK 索引

先读取入口：`nexus_plugin_reference(path="README.md")`。

| 目标 | 资源 |
|---|---|
| 开发入口、文件清单、最短工作流 | `sdk/README.md` |
| 清单、能力版本、生命周期与全部接口 | `sdk/SDK.md` |
| 宿主渲染页面、字段、弹窗与错误 | `sdk/UI.md` |
| 直接 Python 工具和配套技能 | `sdk/examples/tool-skill/plugin.json`、`backend.py`、`skills/example-workflow/SKILL.md` |
| 宿主渲染页面 | `sdk/examples/host-page/plugin.json`、`backend.py` |
| 独立 Python / Node 服务客户端与stdio适配 | `sdk/nexus_host.py`、`sdk/nexus-host.mjs` |
| 在任意目录打包 | `sdk/build.py` |

示例行中的`backend.py`等路径相对于对应示例目录。文本资源通过`nexus_plugin_reference`读取，`path`相对于SDK目录（表中路径去掉`sdk/`前缀），支持`offset`与`limit`分页，不必一次读完全部SDK。工具返回的`SDK directory`是SDK实际目录，可用已授权命令工具完整复制到开发工作区。保留目录结构，构建器从自己的位置找到共享客户端和文档。

## 选择实现方式

- 新的 Agent 工具或配套技能，从`tool-skill`示例开始；宿主内Python工具只从`nexus.plugins.api`导入公开声明类型。
- 普通表单和管理页面优先参考`host-page`与`UI.md`，使用宿主组件，不另造主题、CSS或交互协议。已有iframe页面按SDK约定接入。
- 独立Python/Node服务使用随附客户端和`serve`。宿主注入地址与插件凭据，日志写stderr，stdout留给stdio协议。
- `models/dialogues`用于插件自己管理模型调用；`jobs`运行插件代码；`work`启动复用Nexus工具和审批的后台Agent工作。根据实际需要选择，不用伪造用户消息代替工作接口。

## 开发与交付

复制需要的示例到新的插件目录，修改ID、版本、清单和README。只声明实际使用的`requires_host`能力；按SDK说明处理请求ID、工作归属、结果、取消和清理。需要的业务依赖由插件声明。

在开发工作区执行`python <独立SDK目录>/build.py <插件目录>`生成ZIP。先核对构建器支持的打包范围；验证清单位于包根目录、资源和依赖声明完整、普通开发数据未夹带。

用插件自身的定向测试和实际宿主验证相应工具、技能或页面。只有SDK时可以编写、静态检查和打包；加载、宿主能力与页面联调需要兼容版本的Nexus，真实模型或第三方服务需另行配置。分别说明已完成的阶段，不把ZIP生成等同于插件可正常运行。

## 直接安装到当前 Nexus

用户要求安装时，调用 `nexus_plugin_install(path="工作目录内的插件.zip")`，默认导入并启用。用户明确要求替换已安装版本时传 `replace_existing=true`；只导入而不启用时传 `enable=false`。安装工具通过宿主已有管理接口工作，无需修改 Nexus 源码或手工操作安装目录。

调用后用 `nexus_plugin_status(plugin_id="插件ID")` 查询加载结果。`loading` 是仍在加载，`ready` 才是加载成功；报错则依据实际错误修复。已提交的替换可能先等待旧调用结束，再加载新版本，不要重复导入；若替换结束后未启用，用 `nexus_plugin_enable(plugin_id="插件ID")` 启用。安装成功后在新的模型请求中使用新增工具和技能。更新本开发工具插件使用插件管理入口。
