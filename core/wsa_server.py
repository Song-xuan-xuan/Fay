from asyncio import AbstractEventLoop

import websockets
import asyncio
import json
import os
from abc import abstractmethod
from websockets.legacy.server import Serve

from utils import util, config_util
from scheduler.thread_manager import MyThread

WS_POLICY_VIOLATION = 1008
WS_AUTH_TIMEOUT_SECONDS = 10.0
DEFAULT_WS_USERNAME = "User"


def _websocket_auth_enabled():
    auth_config = {}
    if isinstance(config_util.config, dict):
        auth_config = config_util.config.get('auth', {}) or {}
    elif os.path.exists('config.json'):
        try:
            with open('config.json', 'r', encoding='utf-8') as file:
                auth_config = (json.load(file).get('auth') or {})
        except Exception:
            auth_config = {}
    value = auth_config.get('enabled', False)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

class MyServer:
    def __init__(self, host='0.0.0.0', port=10000):
        self.lock = asyncio.Lock()
        self.__host = host  # ip
        self.__port = port  # 端口号
        self.__listCmd = []  # 要发送的信息的列表
        self.__clients = list() 
        self.__server: Serve = None
        self.__event_loop: AbstractEventLoop = None
        self.__running = True
        self.__pending = None
        self.isConnect = False
        self.TIMEOUT = 3  # 设置任何超时时间为 3 秒
        self.__tasks = {}  # 记录任务和开始时间的字典

    # 接收处理
    async def __consumer_handler(self, websocket, path, auth_context=None):
        auth_context = auth_context or {}
        bound_username = auth_context.get('username') if auth_context.get('authenticated') else None
        username = bound_username
        output_setting = None
        try:
            async for message in websocket:
                await asyncio.sleep(0.01)
                message_username = bound_username
                output_setting = None
                try:
                    data = json.loads(message)
                    if bound_username is None:
                        message_username = data.get("Username")
                    output_setting = data.get("Output")
                except json.JSONDecodeError:
                    pass  # Ignore invalid JSON messages
                if message_username is not None or output_setting is not None:
                    remote_address = websocket.remote_address
                    unique_id = f"{remote_address[0]}:{remote_address[1]}"
                    async with self.lock:
                        for i in range(len(self.__clients)):
                            if self.__clients[i]["id"] == unique_id:
                                if message_username is not None:
                                    self.__clients[i]["username"] = message_username
                                    username = message_username
                                if output_setting is not None:
                                    self.__clients[i]["output"] = output_setting
                await self.__consumer(message)
        except websockets.exceptions.ConnectionClosedError as e:
            # 从客户端列表中移除已断开的连接
            await self.remove_client(websocket)
            util.printInfo(1, "User" if username is None else username, f"WebSocket 连接关闭: {e}")

    def get_client_output(self, username):
        clients_with_username = [c for c in self.__clients if c.get("username") == username]
        if not clients_with_username:
            return False
        for client in clients_with_username:
            # 获取output设置，支持布尔值、字符串布尔值、数字等多种格式
            output = client.get("output", True)  # 默认为True，表示需要音频

            # 处理不同类型的输入
            if isinstance(output, bool):
                if output:  # 如果是True
                    return True
            elif isinstance(output, str):
                if output.lower() == 'true':  # 字符串"true"
                    return True
            elif isinstance(output, (int, float)):
                if output != 0 and output != '0':  # 0以外的数字
                    return True

        return False

    # 发送处理        
    async def __producer_handler(self, websocket, path):
        while self.__running:
            await asyncio.sleep(0.01)
            if len(self.__listCmd) > 0:
                message = await self.__producer()
                if message:
                    username = json.loads(message).get("Username")
                    if username is None:
                        # 群发消息
                        async with self.lock:
                            wsclients = [c["websocket"] for c in self.__clients]
                        tasks = [self.send_message_with_timeout(client, message, username, timeout=3) for client in wsclients]
                        await asyncio.gather(*tasks)
                    else:
                        # 向指定用户发送消息
                        async with self.lock:
                            target_clients = [c["websocket"] for c in self.__clients if c.get("username") == username]
                        tasks = [self.send_message_with_timeout(client, message, username, timeout=3) for client in target_clients]
                        await asyncio.gather(*tasks)

    # 发送消息（设置超时）
    async def send_message_with_timeout(self, client, message, username, timeout=3):
        try:
            await asyncio.wait_for(self.send_message(client, message, username), timeout=timeout)
        except asyncio.TimeoutError:
            util.printInfo(1, "User" if username is None else username, f"发送消息超时: 用户名 {username}")
        except websockets.exceptions.ConnectionClosed as e:
            # 从客户端列表中移除已断开的连接
            await self.remove_client(client)
            util.printInfo(1, "User" if username is None else username, f"WebSocket 连接关闭: {e}")

    # 发送消息
    async def send_message(self, client, message, username):
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed as e:
            # 从客户端列表中移除已断开的连接
            await self.remove_client(client)
            util.printInfo(1, "User" if username is None else username, f"WebSocket 连接关闭: {e}")

                
    async def __authenticate_connection(self, websocket):
        if not _websocket_auth_enabled():
            return {'authenticated': False, 'username': DEFAULT_WS_USERNAME, 'role': None, 'uid': None, 'output': True}
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=WS_AUTH_TIMEOUT_SECONDS)
            data = json.loads(message)
        except asyncio.TimeoutError:
            await websocket.close(code=WS_POLICY_VIOLATION, reason='Missing token')
            return None
        except json.JSONDecodeError:
            await websocket.close(code=WS_POLICY_VIOLATION, reason='Invalid token')
            return None

        token = data.get('token')
        if not token:
            await websocket.close(code=WS_POLICY_VIOLATION, reason='Missing token')
            return None
        try:
            from core import auth_service
            payload = auth_service.verify_token(token)
        except Exception:
            await websocket.close(code=WS_POLICY_VIOLATION, reason='Invalid token')
            return None
        return {
            'authenticated': True,
            'username': payload.get('username') or DEFAULT_WS_USERNAME,
            'role': payload.get('role'),
            'uid': payload.get('uid'),
            'output': data.get('Output', True),
        }

    async def __handler(self, websocket, path):
        auth_context = await self.__authenticate_connection(websocket)
        if auth_context is None:
            return
        self.isConnect = True
        util.log(1,"websocket连接上:{}".format(self.__port))
        self.on_connect_handler()
        remote_address = websocket.remote_address
        unique_id = f"{remote_address[0]}:{remote_address[1]}"
        async with self.lock:
            self.__clients.append({
                "id": unique_id,
                "websocket": websocket,
                "username": auth_context.get('username') or DEFAULT_WS_USERNAME,
                "role": auth_context.get('role'),
                "uid": auth_context.get('uid'),
                "output": auth_context.get('output', True),
            })
        consumer_task = asyncio.create_task(self.__consumer_handler(websocket, path, auth_context))#接收
        producer_task = asyncio.create_task(self.__producer_handler(websocket, path))#发送
        done, self.__pending = await asyncio.wait([consumer_task, producer_task], return_when=asyncio.FIRST_COMPLETED)

        for task in self.__pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
        # 从客户端列表中移除已断开的连接
        await self.remove_client(websocket)
        util.log(1, "websocket连接断开:{}".format(unique_id))
                
    async def __consumer(self, message):
        self.on_revice_handler(message)
    
    async def __producer(self):
        if len(self.__listCmd) > 0:
            message = self.on_send_handler(self.__listCmd.pop(0))
            return message
        else:
            return None
        
    async def remove_client(self, websocket):
        async with self.lock:
            self.__clients = [c for c in self.__clients if c["websocket"] != websocket]
            if len(self.__clients) == 0:
                self.isConnect = False
        self.on_close_handler()

    def is_connected(self, username):
        if username is None:
            username = "User"
        if len(self.__clients) == 0:
            return False
        clients = [c for c in self.__clients if c["username"] == username]
        if len(clients) > 0:
            return True
        return False


    #Edit by xszyou on 20230113:通过继承此类来实现服务端的接收后处理逻辑
    @abstractmethod
    def on_revice_handler(self, message):
        pass

    #Edit by xszyou on 20230114:通过继承此类来实现服务端的连接处理逻辑
    @abstractmethod
    def on_connect_handler(self):
        pass
    
    #Edit by xszyou on 20230804:通过继承此类来实现服务端的发送前的处理逻辑
    @abstractmethod
    def on_send_handler(self, message):
        return message

    #Edit by xszyou on 20230816:通过继承此类来实现服务端的断开后的处理逻辑
    @abstractmethod
    def on_close_handler(self):
        pass

    # 创建server
    def __connect(self):
        self.__event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__event_loop)
        self.__isExecute = True
        if self.__server:
            util.log(1, 'server already exist')
            return
        self.__server = websockets.serve(self.__handler, self.__host, self.__port, ping_interval=10, ping_timeout=5)
        asyncio.get_event_loop().run_until_complete(self.__server)
        asyncio.get_event_loop().run_forever()

    # 往要发送的命令列表中，添加命令
    def add_cmd(self, content):
        if not self.__running:
            return
        # keep unicode (emoji/中文) intact for websocket consumers
        jsonStr = json.dumps(content, ensure_ascii=False)
        self.__listCmd.append(jsonStr)
        # util.log('命令 {}'.format(content))

    # 开启服务
    def start_server(self):
        MyThread(target=self.__connect).start()

    # 关闭服务
    def stop_server(self):
        self.__running = False
        self.isConnect = False
        if self.__server is None:
            return
        self.__server.close()
        self.__server = None
        self.__clients = []
        util.log(1, "WebSocket server stopped.")


#ui端server
class WebServer(MyServer):
    def __init__(self, host='0.0.0.0', port=10003):
        super().__init__(host, port)

    def on_revice_handler(self, message):
        pass
    
    def on_connect_handler(self):
        self.add_cmd({"panelMsg": "使用提示：Fay可以独立使用，启动数字人将自动对接。"})

    def on_send_handler(self, message):
        return message

    def on_close_handler(self):
        pass

#数字人端server
class HumanServer(MyServer):
    def __init__(self, host='0.0.0.0', port=10002):
        super().__init__(host, port)

    def on_revice_handler(self, message):
       pass

    def on_connect_handler(self):
        web_server_instance = get_web_instance()  
        web_server_instance.add_cmd({"is_connect": self.isConnect}) 
        

    def on_send_handler(self, message):
        # util.log(1, '向human发送 {}'.format(message))
        if not self.isConnect:
            return None
        return message

    def on_close_handler(self):
        web_server_instance = get_web_instance()  
        web_server_instance.add_cmd({"is_connect": self.isConnect}) 

        

#测试
class TestServer(MyServer):
    def __init__(self, host='0.0.0.0', port=10000):
        super().__init__(host, port)

    def on_revice_handler(self, message):
        print(message)
    
    def on_connect_handler(self):
        print("连接上了")
    
    def on_send_handler(self, message):
        return message
    
    def on_close_handler(self):
        pass



#单例

__instance: MyServer = None
__web_instance: MyServer = None


def new_instance(host='0.0.0.0', port=10002) -> MyServer:
    global __instance
    if __instance is None:
        __instance = HumanServer(host, port)
    return __instance


def new_web_instance(host='0.0.0.0', port=10003) -> MyServer:
    global __web_instance
    if __web_instance is None:
        __web_instance = WebServer(host, port)
    return __web_instance


def get_instance() -> MyServer:
    return __instance


def get_web_instance() -> MyServer:
    return __web_instance

if __name__ == '__main__':
    testServer = TestServer(host='0.0.0.0', port=10000)
    testServer.start_server()
