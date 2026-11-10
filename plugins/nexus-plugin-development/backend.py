"""Developer kit built entirely on the public plugin and management interfaces."""
import io
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from nexus.plugins.api import BaseModel, Field, ToolSpec

ROOT = Path(__file__).resolve().parent
SDK = ROOT / 'skills/nexus-plugin-development/sdk'


class InstallArgs(BaseModel):
    path: str = Field(min_length=1, description='Plugin ZIP path inside the current workspace.')
    replace_existing: bool = Field(default=False, description='Replace an installed plugin when requested by the user.')
    enable: bool = Field(default=True, description='Enable the plugin after importing it.')


class StatusArgs(BaseModel):
    plugin_id: str = Field(default='', description='Plugin ID; empty lists all plugins.')


class EnableArgs(BaseModel):
    plugin_id: str = Field(min_length=1)


class ReferenceArgs(BaseModel):
    path: str = Field(default='README.md', description='Text resource relative to the bundled SDK directory.')
    offset: int = Field(default=1, ge=1)
    limit: int = Field(default=200, ge=1, le=2000)


class Plugin:
    def __init__(self, host):
        self.host = host

    def request(self, path, payload=None, *, binary=False):
        data = payload if binary else (json.dumps(payload).encode() if payload is not None else None)
        headers = {'Content-Type': 'application/zip' if binary else 'application/json'}
        request = Request(self.host.base_url + path, data=data, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except HTTPError as error:
            detail = json.loads(error.read())
            raise ValueError(detail.get('error', str(error))) from error

    def tools(self, scope):
        return [
            ToolSpec('nexus_plugin_reference', 'Read bundled SDK documentation, clients or examples. Returns the SDK directory for copying into the development workspace.',
                     ReferenceArgs, self.reference, read_only=True),
            ToolSpec('nexus_plugin_install', 'Import a workspace plugin ZIP into this Nexus and optionally enable it. Use nexus_plugin_status to verify loading.',
                     InstallArgs, self.install),
            ToolSpec('nexus_plugin_status', 'Read installed plugin versions, enabled state and load errors.',
                     StatusArgs, self.status, read_only=True),
            ToolSpec('nexus_plugin_enable', 'Enable an installed plugin, including after a queued replacement finishes.',
                     EnableArgs, self.enable),
        ]

    def reference(self, context, arguments):
        path = (SDK / arguments['path']).resolve()
        if not path.is_relative_to(SDK.resolve()):
            raise PermissionError('资源须位于 SDK 目录内')
        lines = path.read_text(encoding='utf-8').splitlines()
        start = arguments['offset'] - 1
        end = start + arguments['limit']
        body = '\n'.join(f'{i}: {line}' for i, line in enumerate(lines[start:end], start + 1))
        return {'content': f'SDK directory: {SDK}\nFile: {arguments["path"]}\n{body}\nTotal lines: {len(lines)}'}

    def install(self, context, arguments):
        workspace = Path(context.root).resolve()
        path = (workspace / arguments['path']).resolve()
        if not path.is_relative_to(workspace):
            raise PermissionError('插件包须位于当前工作目录内')
        content = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            manifests = [name for name in archive.namelist()
                         if name == 'plugin.json' or (name.count('/') == 1 and name.endswith('/plugin.json'))]
            if len(manifests) != 1:
                raise ValueError('插件包应包含唯一的 plugin.json')
            plugin_id = json.loads(archive.read(manifests[0]))['id']
        if plugin_id == self.host.id:
            raise ValueError('请通过插件管理更新开发工具插件本身')
        result = self.request('/api/plugins/import?replace=' + ('1' if arguments['replace_existing'] else '0'), content, binary=True)
        current = next(row for row in result['plugins'] if row['id'] == plugin_id)
        if arguments['enable'] and current['status'] not in ('draining', 'closing'):
            from urllib.parse import quote
            result = self.request('/api/plugins/' + quote(plugin_id, safe='') + '/commands', {'operation': 'load'})
        return self.status(context, {'plugin_id': plugin_id})

    def enable(self, context, arguments):
        from urllib.parse import quote
        self.request('/api/plugins/' + quote(arguments['plugin_id'], safe='') + '/commands', {'operation': 'load'})
        return self.status(context, arguments)

    def status(self, context, arguments):
        result = self.request('/api/plugins')
        rows = result['plugins']
        if arguments['plugin_id']:
            rows = [row for row in rows if row['id'] == arguments['plugin_id']]
        return {'content': json.dumps([{key: row[key] for key in ('id', 'version', 'enabled', 'status', 'error', 'progress')}
                                       for row in rows], ensure_ascii=False)}

    def call(self, action, values):
        if action != 'ui':
            raise ValueError('未知操作')
        documents = {'插件介绍': ROOT / 'README.md', 'backend.py': ROOT / 'backend.py',
                     'plugin.json': ROOT / 'plugin.json', '开发技能': ROOT / 'skills/nexus-plugin-development/SKILL.md'}
        documents.update({p.relative_to(SDK).as_posix(): p for p in sorted(SDK.rglob('*'))
                          if p.is_file() and p.suffix in ('.md', '.py', '.mjs', '.json')})
        fields = values.get('values', {})
        selected = fields.get('document', '插件介绍')
        if selected not in documents:
            raise ValueError('请选择列表中的文档')
        echo = fields.get('example_text', '')
        return {'ui_version': 1, 'components': [
            {'id': 'intro', 'type': 'section', 'title': '插件开发与示例',
             'description': '查看插件规范与源码，在对话中提出需求，由助手开发、打包并安装插件。', 'children': [
                 {'id': 'features', 'type': 'text', 'text': '这个插件演示宿主页面、表单交互、Agent 工具和随附技能。SDK 与示例均随包提供。'},
             ]},
            {'id': 'demo', 'type': 'section', 'title': '交互示例', 'children': [
                {'id': 'example-text', 'type': 'field', 'name': 'example_text', 'label': '示例文字', 'value': echo},
                {'id': 'echo', 'type': 'button', 'label': '显示', 'action': 'echo'},
                {'id': 'echo-result', 'type': 'text', 'text': echo or '输入文字后点击显示。'},
            ]},
            {'id': 'docs', 'type': 'section', 'title': '文档与源码', 'children': [
                {'id': 'document', 'type': 'field', 'name': 'document', 'label': '选择文档', 'control': 'select',
                 'value': selected, 'options': [{'label': name, 'value': name} for name in documents]},
                {'id': 'read', 'type': 'button', 'label': '查看', 'action': 'read'},
                {'id': 'source', 'type': 'code', 'text': documents[selected].read_text(encoding='utf-8')},
            ]},
        ]}


def create_plugin(host):
    return Plugin(host)
