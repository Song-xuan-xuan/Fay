import gc
import importlib
import json
import os
import shutil
import sys
import tempfile
import time
import types


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TempProjectMixin:
    def setUp(self):
        self._cwd = os.getcwd()
        self._temp_dir = tempfile.mkdtemp(prefix='fay-auth-test-')
        os.chdir(self._temp_dir)
        os.mkdir('memory')
        os.mkdir('logs')
        with open('system.conf', 'w', encoding='utf-8') as file:
            file.write('[key]\nstart_mode=web\nfay_url=http://127.0.0.1:5000\n')
        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(
                {
                    'auth': {
                        'enabled': True,
                        'jwt_expiration_hours': 168,
                        'default_admin_username': 'admin',
                        'default_admin_password': 'admin123',
                    },
                    'memory': {'isolate_by_user': True},
                },
                file,
            )

        self._installed_pyaudio_stub = False
        self._stubbed_modules = set()
        self._install_test_stubs()
        self._reset_singletons()

    def tearDown(self):
        self._reset_singletons()
        gc.collect()
        os.chdir(self._cwd)
        self._remove_temp_dir()
        if self._installed_pyaudio_stub:
            sys.modules.pop('pyaudio', None)
        for module_name in self._stubbed_modules:
            self._remove_module(module_name)

    def _remove_temp_dir(self):
        for attempt in range(3):
            try:
                shutil.rmtree(self._temp_dir)
                return
            except PermissionError:
                if attempt == 2:
                    raise
                gc.collect()
                time.sleep(0.1)

    def _install_test_stubs(self):
        if 'pyaudio' in sys.modules:
            self._install_runtime_stubs()
            return

        class FakePyAudio:
            def get_device_count(self):
                return 0

            def get_device_info_by_index(self, index):
                return {'hostApi': 0, 'name': f'Fake Device {index}'}

        sys.modules['pyaudio'] = types.SimpleNamespace(PyAudio=FakePyAudio)
        self._installed_pyaudio_stub = True
        self._install_runtime_stubs()

    def _install_runtime_stubs(self):
        class FakeFeiFei:
            def on_interact(self, interact):
                return ''

        class FakeRecorderListener:
            wakeup_matched = False

        fay_booter_stub = types.SimpleNamespace(
            feiFei=FakeFeiFei(),
            recorderListener=FakeRecorderListener(),
            DeviceInputListenerDict={},
            is_running=lambda: False,
            start=lambda: None,
            stop=lambda: None,
        )
        fay_core_stub = types.ModuleType('core.fay_core')
        qa_service_stub = types.ModuleType('core.qa_service')
        stream_manager_stub = types.ModuleType('core.stream_manager')
        mcp_client_stub = types.ModuleType('faymcp.mcp_client')

        class FakeQAService:
            def record_qapair(self, *args, **kwargs):
                return None

            def remove_qapair(self, *args, **kwargs):
                return True

        class FakeStreamManager:
            def clear_Stream_with_audio(self, *args, **kwargs):
                return None

        qa_service_stub.QAService = FakeQAService
        stream_manager_stub.new_instance = lambda: FakeStreamManager()

        class FakeMcpClient:
            pass

        mcp_client_stub.McpClient = FakeMcpClient

        stubs = {
            'fay_booter': fay_booter_stub,
            'core.fay_core': fay_core_stub,
            'core.qa_service': qa_service_stub,
            'core.stream_manager': stream_manager_stub,
            'faymcp.mcp_client': mcp_client_stub,
        }
        for module_name, module in stubs.items():
            sys.modules[module_name] = module
            self._set_parent_attr(module_name, module)
            self._stubbed_modules.add(module_name)

    def _set_parent_attr(self, module_name, module):
        if '.' not in module_name:
            return
        package_name, attr = module_name.rsplit('.', 1)
        package = importlib.import_module(package_name)
        setattr(package, attr, module)

    def _remove_module(self, module_name):
        sys.modules.pop(module_name, None)
        if '.' not in module_name:
            return
        package_name, attr = module_name.rsplit('.', 1)
        package = sys.modules.get(package_name)
        if package is not None and hasattr(package, attr):
            delattr(package, attr)

    def _reset_singletons(self):
        modules = [
            'utils.config_util',
            'core.content_db',
            'core.digital_human_service',
            'core.live2d_resource_service',
            'core.member_db',
            'core.auth_service',
            'core.audit_service',
            'core.auth_bootstrap',
            'core.wsa_server',
            'migrations.001_add_auth',
            'gui.auth_routes',
            'gui.avatar_routes',
            'gui.dashboard_routes',
            'gui.digital_human_routes',
            'gui.flask_server',
            'faymcp.kb_routes',
            'faymcp.mcp_service',
        ]
        for module_name in modules:
            self._remove_module(module_name)


class FakeHandshakeWebSocket:
    def __init__(self, messages=None, fail_on_recv=False):
        self.messages = list(messages or [])
        self.fail_on_recv = fail_on_recv
        self.closed = []
        self.remote_address = ('127.0.0.1', 54321)

    async def recv(self):
        if self.fail_on_recv:
            raise AssertionError('legacy websocket auth should not read a handshake message')
        if not self.messages:
            raise AssertionError('expected handshake message')
        return self.messages.pop(0)

    async def close(self, code=None, reason=None):
        self.closed.append({'code': code, 'reason': reason})


class FakeStreamingWebSocket(FakeHandshakeWebSocket):
    def __init__(self, stream_messages):
        super().__init__()
        self.stream_messages = list(stream_messages)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.stream_messages:
            raise StopAsyncIteration
        return self.stream_messages.pop(0)
