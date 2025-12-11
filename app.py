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
        "name": "Authentication Debug (fnbamd)",
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
        "name": "FortiToken Debug",
        "commands": [
            "diagnose debug reset",
            "diagnose debug console timestamp enable",
            "diagnose debug application forticldd 255",
            "diagnose fortitoken debug enable",
            "diagnose debug enable"
        ],
        "stop_commands": [
            "diagnose fortitoken debug disable",
            "diagnose debug application forticldd 0",
            "diagnose debug reset"
        ]
    },
    "fortitoken_cloud": {
        "name": "FortiToken Cloud Debug",
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
        "name": "SSL VPN Debug",
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
        "name": "IPsec VPN Debug",
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
        "name": "Routing Debug - OSPF",
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
        "name": "Routing Debug - BGP",
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
        "name": "Packet Flow Debug",
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
        "name": "WAD Proxy Debug",
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
        "name": "IPS Engine Debug",
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
        "name": "High Availability (HA) Debug",
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
        "name": "DNS Debug",
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
        "name": "DHCP Server Debug",
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
        "name": "FortiLink Debug",
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
        "name": "SD-WAN Debug",
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
        "name": "ZTNA Debug",
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
    """FortiGate connection manager"""
    
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
        """Establish an SSH connection"""
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
            # Clear any initial channel output
            if self.shell.recv_ready():
                logger.debug("Clearing initial SSH channel output for %s", self.host)
                self.shell.recv(65535)
            return True, "SSH connection successful"
        except Exception as e:
            logger.exception("SSH connection failed for %s:%s", self.host, self.port)
            return False, f"SSH connection failed: {str(e)}"

    def connect_telnet(self):
        """Establish a Telnet connection"""
        try:
            logger.debug("Initializing Telnet client for %s:%s", self.host, self.port)
            self.client = telnetlib.Telnet(self.host, self.port, timeout=10)
            # Wait for login prompts
            self.client.read_until(b"login: ", timeout=5)
            self.client.write(self.username.encode('ascii') + b"\n")
            self.client.read_until(b"Password: ", timeout=5)
            self.client.write(self.password.encode('ascii') + b"\n")
            time.sleep(1)
            return True, "Telnet connection successful"
        except Exception as e:
            logger.exception("Telnet connection failed for %s:%s", self.host, self.port)
            return False, f"Telnet connection failed: {str(e)}"

    def connect(self):
        """Create a connection using the configured protocol"""
        if self.connection_type == 'ssh':
            logger.info("Attempting SSH connection to %s:%s", self.host, self.port)
            return self.connect_ssh()
        elif self.connection_type == 'telnet':
            logger.info("Attempting Telnet connection to %s:%s", self.host, self.port)
            return self.connect_telnet()
        else:
            return False, "Unsupported connection type"

    def send_command(self, command, wait_time=1):
        """Send a command over the active connection"""
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
            return f"Command execution error: {str(e)}"

    def start_debug_monitoring(self, debug_mode, commands=None):
        """Start debug monitoring for the selected mode or custom commands"""
        if debug_mode == 'custom':
            if not commands:
                return False, "Custom commands are required"
            start_commands = commands
            mode_name = "custom commands"
        else:
            if debug_mode not in DEBUG_MODES:
                return False, "Invalid debug mode"
            mode_config = DEBUG_MODES[debug_mode]
            start_commands = mode_config['commands']
            mode_name = mode_config['name']

        # Send debug start commands
        for cmd in start_commands:
            self.send_command(cmd, wait_time=0.5)
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_output)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("Started debug monitoring: mode=%s session=%s", debug_mode, self.current_output_id)

        return True, f"Started monitoring {mode_name}"

    def _monitor_output(self):
        """Background thread to collect device output"""
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
                self.output_buffer.append(f"Monitoring error: {str(e)}")
                break

    def stop_debug_monitoring(self, debug_mode, stop_commands=None):
        """Stop debug monitoring for the selected mode"""
        self.is_monitoring = False

        logger.info("Stopping debug monitoring: mode=%s session=%s", debug_mode, self.current_output_id)

        if debug_mode == 'custom':
            if stop_commands:
                for cmd in stop_commands:
                    self.send_command(cmd, wait_time=0.5)
        elif debug_mode in DEBUG_MODES:
            mode_config = DEBUG_MODES[debug_mode]
            for cmd in mode_config['stop_commands']:
                self.send_command(cmd, wait_time=0.5)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

        return True, "Monitoring stopped"

    def get_output(self):
        """Return a copy of the current output buffer"""
        output = self.output_buffer.copy()
        return output

    def clear_output(self):
        """Clear the current output buffer"""
        self.output_buffer.clear()

    def disconnect(self):
        """Disconnect and clean up resources"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        if self.connection_type == 'ssh' and self.client:
            self.client.close()
        elif self.connection_type == 'telnet' and self.client:
            self.client.close()


@app.route('/api/debug-modes', methods=['GET'])
def get_debug_modes():
    """Return all available debug modes"""
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
    """Create a new FortiGate connection"""
    data = request.json

    logger.info("Received connection request", extra={'host': data.get('host'), 'connection_type': data.get('connection_type', 'ssh')})

    host = data.get('host')
    port = data.get('port', 22)
    username = data.get('username')
    password = data.get('password')
    connection_type = data.get('connection_type', 'ssh')
    
    if not all([host, username, password]):
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400

    # Create connection object
    session_id = f"{host}_{username}_{int(time.time())}"
    conn = FortiGateConnection(host, port, username, password, connection_type)

    # Attempt to connect
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
    """Start debug monitoring for a session"""
    data = request.json
    session_id = data.get('session_id')
    debug_mode = data.get('debug_mode')
    custom_commands = data.get('custom_commands')
    custom_stop_commands = data.get('custom_stop_commands')

    def _parse_commands(cmds):
        if not cmds:
            return []
        if isinstance(cmds, str):
            return [c.strip() for c in cmds.splitlines() if c.strip()]
        if isinstance(cmds, list):
            return [str(c).strip() for c in cmds if str(c).strip()]
        return []

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': 'Invalid session ID'}), 400

    conn = active_sessions[session_id]
    output_id = f"{session_id}_{debug_mode}_{int(time.time())}"
    logger.info("Starting debug", extra={'session_id': session_id, 'debug_mode': debug_mode, 'output_id': output_id})
    parsed_custom_commands = _parse_commands(custom_commands)
    parsed_custom_stop_commands = _parse_commands(custom_stop_commands)

    debug_outputs[output_id] = {
        'session_id': session_id,
        'debug_mode': debug_mode,
        'start_time': datetime.now().isoformat(),
        'output': [],
        'start_commands': parsed_custom_commands if debug_mode == 'custom' else DEBUG_MODES.get(debug_mode, {}).get('commands', []),
        'stop_commands': parsed_custom_stop_commands if debug_mode == 'custom' else DEBUG_MODES.get(debug_mode, {}).get('stop_commands', [])
    }

    conn.current_output_id = output_id

    if debug_mode == 'custom':
        if not parsed_custom_commands:
            return jsonify({'success': False, 'message': 'Custom commands are required'}), 400
        success, message = conn.start_debug_monitoring(debug_mode, parsed_custom_commands)
    else:
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
    """Stop debug monitoring for a session"""
    data = request.json
    session_id = data.get('session_id')
    output_id = data.get('output_id')
    debug_mode = data.get('debug_mode')
    custom_stop_commands = data.get('custom_stop_commands')

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': 'Invalid session ID'}), 400

    conn = active_sessions[session_id]
    logger.info("Stopping debug", extra={'session_id': session_id, 'debug_mode': debug_mode, 'output_id': output_id})
    stop_commands = []
    if debug_mode == 'custom':
        # Prefer provided stop commands, fall back to stored commands for this output
        if custom_stop_commands:
            if isinstance(custom_stop_commands, str):
                stop_commands = [c.strip() for c in custom_stop_commands.splitlines() if c.strip()]
            elif isinstance(custom_stop_commands, list):
                stop_commands = [str(c).strip() for c in custom_stop_commands if str(c).strip()]
        elif output_id and output_id in debug_outputs:
            stop_commands = debug_outputs[output_id].get('stop_commands', [])

    success, message = conn.stop_debug_monitoring(debug_mode, stop_commands)

    conn.current_output_id = None

    # Save final output
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
    """Return debug output for a session"""
    data = request.json
    session_id = data.get('session_id')

    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': 'Invalid session ID'}), 400

    conn = active_sessions[session_id]
    output = conn.get_output()

    logger.debug("Serving output", extra={'session_id': session_id, 'lines': len(output)})

    return jsonify({
        'success': True,
        'output': output
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Return basic usage statistics"""
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
    """Download debug output for a completed session"""
    data = request.json
    output_id = data.get('output_id')

    if output_id not in debug_outputs:
        return jsonify({'success': False, 'message': 'Invalid output ID'}), 400

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
    
    # Build file content
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
    
    # Create the downloadable file
    filename = f"fortigate_debug_{output_data['debug_mode']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    return send_file(
        io.BytesIO(file_content.encode('utf-8')),
        mimetype='text/plain',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect an active FortiGate session"""
    data = request.json
    session_id = data.get('session_id')

    if session_id in active_sessions:
        conn = active_sessions[session_id]
        conn.disconnect()
        del active_sessions[session_id]
        logger.info("Disconnected session", extra={'session_id': session_id})
        return jsonify({'success': True, 'message': 'Disconnected successfully'})

    return jsonify({'success': False, 'message': 'Invalid session ID'}), 400


@app.route('/api/execute-command', methods=['POST'])
def execute_command():
    """Execute a custom CLI command"""
    data = request.json
    session_id = data.get('session_id')
    command = data.get('command')
    
    if session_id not in active_sessions:
        return jsonify({'success': False, 'message': 'Invalid session ID'}), 400

    if not command:
        return jsonify({'success': False, 'message': 'Command cannot be empty'}), 400

    conn = active_sessions[session_id]
    logger.info("Executing custom command", extra={'session_id': session_id, 'command': command})
    output = conn.send_command(command, wait_time=2)

    return jsonify({
        'success': True,
        'output': output
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
