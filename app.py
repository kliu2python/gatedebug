#!/usr/bin/env python3
"""
FortiGate Debug Monitor Web Application
Backend API Server with SSH/Telnet/Console support
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import paramiko
import telnetlib
import io
import threading
import time
import json
import logging
from datetime import datetime
import os

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger("fortigate_debug")

app = Flask(__name__)
CORS(app)

# Global storage for active sessions and debug outputs
active_sessions = {}
debug_outputs = {}

# Usage tracking
usage_metrics = {
    'total_sessions': 0,
    'unique_users': set()
}

# FortiGate Debug Commands Configuration
DEBUG_MODES = {
    "authentication": {
        "name": "认证调试 (Authentication - fnbamd)",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application fnbamd -1"
        ],
        "stop_commands": [
            "diagnose debug application fnbamd 0",
            "diagnose debug reset"
        ]
    },
    "fortitoken": {
        "name": "FortiToken调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application forticldd 255",
            "diagnose fortitoken debug enable"
        ],
        "stop_commands": [
            "diagnose fortitoken debug disable",
            "diagnose debug application forticldd 0",
            "diagnose debug reset"
        ]
    },
    "fortitoken_cloud": {
        "name": "FortiToken Cloud调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application ftm-push -1"
        ],
        "stop_commands": [
            "diagnose debug application ftm-push 0",
            "diagnose debug reset"
        ]
    },
    "ssl_vpn": {
        "name": "SSL VPN调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application sslvpn -1"
        ],
        "stop_commands": [
            "diagnose debug application sslvpn 0",
            "diagnose debug reset"
        ]
    },
    "ipsec_vpn": {
        "name": "IPsec VPN调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose vpn ike log-filter clear",
            "diagnose debug application ike -1"
        ],
        "stop_commands": [
            "diagnose debug application ike 0",
            "diagnose debug reset"
        ]
    },
    "routing_ospf": {
        "name": "路由调试 - OSPF",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose ip router ospf level info",
            "diagnose ip router ospf all enable"
        ],
        "stop_commands": [
            "diagnose ip router ospf all disable",
            "diagnose debug reset"
        ]
    },
    "routing_bgp": {
        "name": "路由调试 - BGP",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose ip router bgp level info",
            "diagnose ip router bgp all enable"
        ],
        "stop_commands": [
            "diagnose ip router bgp all disable",
            "diagnose debug reset"
        ]
    },
    "packet_flow": {
        "name": "数据包流调试 (Debug Flow)",
        "commands": [
            "diagnose debug reset",
            "diagnose debug flow filter clear",
            "diagnose debug console timestamp enable",
            "diagnose debug flow show console enable",
            "diagnose debug flow show function-name enable",
            "diagnose debug enable",
            "diagnose debug flow trace start 100"
        ],
        "stop_commands": [
            "diagnose debug flow trace stop",
            "diagnose debug disable",
            "diagnose debug reset"
        ]
    },
    "wad_proxy": {
        "name": "WAD代理调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application wad -1"
        ],
        "stop_commands": [
            "diagnose debug application wad 0",
            "diagnose debug reset"
        ]
    },
    "ips": {
        "name": "IPS引擎调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application ipsmonitor -1"
        ],
        "stop_commands": [
            "diagnose debug application ipsmonitor 0",
            "diagnose debug reset"
        ]
    },
    "ha": {
        "name": "高可用性 (HA) 调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application hatalk -1",
            "diagnose debug application hasync -1"
        ],
        "stop_commands": [
            "diagnose debug application hatalk 0",
            "diagnose debug application hasync 0",
            "diagnose debug reset"
        ]
    },
    "dns": {
        "name": "DNS调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application dnsproxy -1"
        ],
        "stop_commands": [
            "diagnose debug application dnsproxy 0",
            "diagnose debug reset"
        ]
    },
    "dhcp": {
        "name": "DHCP服务器调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application dhcps -1"
        ],
        "stop_commands": [
            "diagnose debug application dhcps 0",
            "diagnose debug reset"
        ]
    },
    "fortilink": {
        "name": "FortiLink调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application fortilink -1"
        ],
        "stop_commands": [
            "diagnose debug application fortilink 0",
            "diagnose debug reset"
        ]
    },
    "sdwan": {
        "name": "SD-WAN调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application sdwan-monitor -1"
        ],
        "stop_commands": [
            "diagnose debug application sdwan-monitor 0",
            "diagnose debug reset"
        ]
    },
    "ztna": {
        "name": "ZTNA调试",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application ztnad -1"
        ],
        "stop_commands": [
            "diagnose debug application ztnad 0",
            "diagnose debug reset"
        ]
    }
}


class FortiGateConnection:
    """FortiGate连接管理类"""
    
    def __init__(self, host, port, username, password, connection_type='ssh'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection_type = connection_type
        self.client = None
        self.shell = None
        self.output_buffer = []
        self.is_monitoring = False
        self.monitor_thread = None
        self.current_output_id = None
        
    def connect_ssh(self):
        """SSH连接"""
        try:
            logger.debug("Initializing SSH client for %s:%s", self.host, self.port)
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            self.shell = self.client.invoke_shell(width=200, height=50)
            time.sleep(1)
            # 清空初始输出
            if self.shell.recv_ready():
                logger.debug("Clearing initial SSH channel output for %s", self.host)
                self.shell.recv(65535)
            return True, "SSH连接成功"
        except Exception as e:
            logger.exception("SSH connection failed for %s:%s", self.host, self.port)
            return False, f"SSH连接失败: {str(e)}"
    
    def connect_telnet(self):
        """Telnet连接"""
        try:
            logger.debug("Initializing Telnet client for %s:%s", self.host, self.port)
            self.client = telnetlib.Telnet(self.host, self.port, timeout=10)
            # 等待登录提示
            self.client.read_until(b"login: ", timeout=5)
            self.client.write(self.username.encode('ascii') + b"\n")
            self.client.read_until(b"Password: ", timeout=5)
            self.client.write(self.password.encode('ascii') + b"\n")
            time.sleep(1)
            return True, "Telnet连接成功"
        except Exception as e:
            logger.exception("Telnet connection failed for %s:%s", self.host, self.port)
            return False, f"Telnet连接失败: {str(e)}"
    
    def connect(self):
        """建立连接"""
        if self.connection_type == 'ssh':
            logger.info("Attempting SSH connection to %s:%s", self.host, self.port)
            return self.connect_ssh()
        elif self.connection_type == 'telnet':
            logger.info("Attempting Telnet connection to %s:%s", self.host, self.port)
            return self.connect_telnet()
        else:
            return False, "不支持的连接类型"
    
    def send_command(self, command, wait_time=1):
        """发送命令"""
        try:
            if self.connection_type == 'ssh':
                logger.debug("Sending SSH command: %s", command)
                self.shell.send(command + "\n")
                time.sleep(wait_time)
                output = ""
                while self.shell.recv_ready():
                    output += self.shell.recv(65535).decode('utf-8', errors='ignore')
                return output
            elif self.connection_type == 'telnet':
                logger.debug("Sending Telnet command: %s", command)
                self.client.write(command.encode('ascii') + b"\n")
                time.sleep(wait_time)
                return self.client.read_very_eager().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.exception("Command execution error on %s via %s", self.host, self.connection_type)
            return f"命令执行错误: {str(e)}"
    
    def start_debug_monitoring(self, debug_mode):
        """启动debug监控"""
        if debug_mode not in DEBUG_MODES:
            return False, "无效的debug模式"
        
        # 发送debug启动命令
        mode_config = DEBUG_MODES[debug_mode]
        for cmd in mode_config['commands']:
            self.send_command(cmd, wait_time=0.5)
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_output)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("Started debug monitoring: mode=%s session=%s", debug_mode, self.current_output_id)

        return True, f"已启动 {mode_config['name']} 监控"
    
    def _monitor_output(self):
        """监控输出线程"""
        while self.is_monitoring:
            try:
                if self.connection_type == 'ssh' and self.shell.recv_ready():
                    data = self.shell.recv(65535).decode('utf-8', errors='ignore')
                    if data:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        formatted = f"[{timestamp}] {data}"
                        self.output_buffer.append(formatted)
                        if self.current_output_id and self.current_output_id in debug_outputs:
                            debug_outputs[self.current_output_id]['output'].append(formatted)
                elif self.connection_type == 'telnet':
                    data = self.client.read_very_eager().decode('utf-8', errors='ignore')
                    if data:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        formatted = f"[{timestamp}] {data}"
                        self.output_buffer.append(formatted)
                        if self.current_output_id and self.current_output_id in debug_outputs:
                            debug_outputs[self.current_output_id]['output'].append(formatted)
                time.sleep(0.1)
            except Exception as e:
                logger.exception("Monitoring thread error for %s", self.host)
                self.output_buffer.append(f"监控错误: {str(e)}")
                break
    
    def stop_debug_monitoring(self, debug_mode):
        """停止debug监控"""
        self.is_monitoring = False

        logger.info("Stopping debug monitoring: mode=%s session=%s", debug_mode, self.current_output_id)

        if debug_mode in DEBUG_MODES:
            mode_config = DEBUG_MODES[debug_mode]
            for cmd in mode_config['stop_commands']:
                self.send_command(cmd, wait_time=0.5)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        return True, "已停止监控"
    
    def get_output(self):
        """获取输出缓冲区"""
        output = self.output_buffer.copy()
        return output
    
    def clear_output(self):
        """清空输出缓冲区"""
        self.output_buffer.clear()
    
    def disconnect(self):
        """断开连接"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        if self.connection_type == 'ssh' and self.client:
            self.client.close()
        elif self.connection_type == 'telnet' and self.client:
            self.client.close()


@app.route('/api/debug-modes', methods=['GET'])
def get_debug_modes():
    """获取所有可用的debug模式"""
    logger.debug("Fetching available debug modes")
    modes = []
    for key, value in DEBUG_MODES.items():
        modes.append({
            'id': key,
            'name': value['name'],
            'start_commands': value['commands'],
            'stop_commands': value['stop_commands']
        })
    return jsonify({'modes': modes})


@app.route('/api/connect', methods=['POST'])
def connect_fortigate():
    """连接到FortiGate"""
    data = request.json

    logger.info("Received connection request", extra={'host': data.get('host'), 'connection_type': data.get('connection_type', 'ssh')})

    host = data.get('host')
    port = data.get('port', 22)
    username = data.get('username')
    password = data.get('password')
    connection_type = data.get('connection_type', 'ssh')
    
    if not all([host, username, password]):
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    # 创建连接对象
    session_id = f"{host}_{username}_{int(time.time())}"
    conn = FortiGateConnection(host, port, username, password, connection_type)

    # 尝试连接
    success, message = conn.connect()

    if success:
        active_sessions[session_id] = conn
        usage_metrics['total_sessions'] += 1
        usage_metrics['unique_users'].add(username)
        logger.info("Connection established", extra={'session_id': session_id, 'host': host, 'type': connection_type})
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': message
        })
    else:
        logger.warning("Connection failed", extra={'host': host, 'type': connection_type, 'message': message})
        return jsonify({'success': False, 'message': message}), 500


@app.route('/api/start-debug', methods=['POST'])
def start_debug():
    """启动debug监控"""
    data = request.json
    session_id = data.get('session_id')
    debug_mode = data.get('debug_mode')

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': '无效的会话ID'}), 400

    conn = active_sessions[session_id]
    output_id = f"{session_id}_{debug_mode}_{int(time.time())}"
    logger.info("Starting debug", extra={'session_id': session_id, 'debug_mode': debug_mode, 'output_id': output_id})
    debug_outputs[output_id] = {
        'session_id': session_id,
        'debug_mode': debug_mode,
        'start_time': datetime.now().isoformat(),
        'output': []
    }

    conn.current_output_id = output_id

    success, message = conn.start_debug_monitoring(debug_mode)

    if success:
        return jsonify({
            'success': True,
            'output_id': output_id,
            'message': message
        })
    else:
        conn.current_output_id = None
        debug_outputs.pop(output_id, None)
        logger.error("Failed to start debug", extra={'session_id': session_id, 'debug_mode': debug_mode, 'message': message})
        return jsonify({'success': False, 'message': message}), 500


@app.route('/api/stop-debug', methods=['POST'])
def stop_debug():
    """停止debug监控"""
    data = request.json
    session_id = data.get('session_id')
    output_id = data.get('output_id')
    debug_mode = data.get('debug_mode')

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': '无效的会话ID'}), 400

    conn = active_sessions[session_id]
    logger.info("Stopping debug", extra={'session_id': session_id, 'debug_mode': debug_mode, 'output_id': output_id})
    success, message = conn.stop_debug_monitoring(debug_mode)

    conn.current_output_id = None

    # 保存最终输出
    if output_id and output_id in debug_outputs:
        final_output = conn.get_output()
        debug_outputs[output_id]['output'] = final_output
        debug_outputs[output_id]['end_time'] = datetime.now().isoformat()
    
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/get-output', methods=['POST'])
def get_output():
    """获取debug输出"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': '无效的会话ID'}), 400

    conn = active_sessions[session_id]
    output = conn.get_output()

    logger.debug("Serving output", extra={'session_id': session_id, 'lines': len(output)})

    return jsonify({
        'success': True,
        'output': output
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取基础使用统计信息"""
    logger.debug(
        "Stats requested",
        extra={
            'total_sessions': usage_metrics['total_sessions'],
            'unique_users': len(usage_metrics['unique_users']),
            'active_sessions': len(active_sessions)
        }
    )
    return jsonify({
        'success': True,
        'total_sessions': usage_metrics['total_sessions'],
        'unique_users': len(usage_metrics['unique_users']),
        'active_sessions': len(active_sessions)
    })


@app.route('/api/download-output', methods=['POST'])
def download_output():
    """下载debug输出"""
    data = request.json
    output_id = data.get('output_id')

    if output_id not in debug_outputs:
        return jsonify({'success': False, 'message': '无效的输出ID'}), 400

    output_data = debug_outputs[output_id]
    logger.info(
        "Preparing download",
        extra={
            'output_id': output_id,
            'session_id': output_data.get('session_id'),
            'debug_mode': output_data.get('debug_mode'),
            'lines': len(output_data.get('output', []))
        }
    )
    
    # 生成文件内容
    content = []
    content.append(f"FortiGate Debug Output")
    content.append(f"=" * 80)
    content.append(f"Debug Mode: {DEBUG_MODES.get(output_data['debug_mode'], {}).get('name', 'Unknown')}")
    content.append(f"Start Time: {output_data.get('start_time', 'N/A')}")
    content.append(f"End Time: {output_data.get('end_time', 'N/A')}")
    content.append(f"=" * 80)
    content.append("")
    content.extend(output_data['output'])
    
    file_content = "\n".join(content)
    
    # 创建文件
    filename = f"fortigate_debug_{output_data['debug_mode']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    return send_file(
        io.BytesIO(file_content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """断开连接"""
    data = request.json
    session_id = data.get('session_id')

    if session_id in active_sessions:
        conn = active_sessions[session_id]
        conn.disconnect()
        del active_sessions[session_id]
        logger.info("Disconnected session", extra={'session_id': session_id})
        return jsonify({'success': True, 'message': '已断开连接'})
    
    return jsonify({'success': False, 'message': '无效的会话ID'}), 400


@app.route('/api/execute-command', methods=['POST'])
def execute_command():
    """执行自定义命令"""
    data = request.json
    session_id = data.get('session_id')
    command = data.get('command')
    
    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': '无效的会话ID'}), 400

    if not command:
        return jsonify({'success': False, 'message': '命令不能为空'}), 400

    conn = active_sessions[session_id]
    logger.info("Executing custom command", extra={'session_id': session_id, 'command': command})
    output = conn.send_command(command, wait_time=2)

    return jsonify({
        'success': True,
        'output': output
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
