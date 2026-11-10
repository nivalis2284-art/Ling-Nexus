# 插件开发与示例

这是可独立安装的 Nexus 插件开发包，同时也是插件系统的完整示例。

## 使用

在插件管理中导入 ZIP 并启用。打开「插件开发与示例」功能页，可查看开发说明、SDK、示例源码和本插件源码，并操作表单交互示例。页面由 Nexus 宿主组件渲染，自动适配主题。

启用后，在对话中说明需要的插件功能，例如：“帮我开发一个文本处理插件，提供设置页，完成后安装到当前 Nexus。”助手可读取随附的插件开发技能和 SDK，在工作目录生成源码、运行检查、打包，并调用安装工具完成导入与启用，无需修改 Nexus 源码。

## 组成

- `backend.py`：宿主页面与 Agent 工具声明，使用公开的 `nexus.plugins.api`。
- `skills/nexus-plugin-development/SKILL.md`：按需读取的开发流程和 SDK 索引。
- `skills/nexus-plugin-development/sdk/`：完整 SDK，包含文档、Python/Node 客户端、构建器及两个独立示例。
- `nexus_plugin_reference`：按需分页读取随附 SDK；返回资源目录，供助手复制到开发工作区。
- `nexus_plugin_install`：读取当前工作目录中的 ZIP，通过当前宿主现有的管理 HTTP 接口导入并可选启用；替换同名插件须显式指定 `replace_existing`。
- `nexus_plugin_status`：查询安装版本、启用状态、加载进度与错误。
- `nexus_plugin_enable`：启用已导入插件，也可在等待旧版本调用结束、替换完成后启用新版本。

安装返回后应查询状态，`loading` 表示仍在加载，`ready` 才表示加载成功。开发工具插件本身通过插件管理更新。新插件的源码和构建产物保留在工作目录，安装目录由 Nexus 管理。

## 开发与分发

仓库内 SDK 的编辑源为 `nexus-plugin-sdk/`；打包前将其内容同步到技能旁的 `sdk/`，不包含缓存、字节码或生成的 ZIP。执行 `python plugin-dev/build.py nexus-plugin-development` 生成可安装 ZIP。

SDK 1.2.0，Python 3.12，宿主需支持插件技能与 UI v1；SDK 读取由本插件工具提供。此插件不需要模型密钥；助手执行开发使用 Nexus 当前配置的模型和工具权限。独立示例可从 SDK 中复制到其他目录开发与打包。
