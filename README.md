# FortiGate Debug Monitor Web Application

A web application for remotely connecting to FortiGate firewalls and monitoring output from common debug modes.

## Features

### Connection Methods
- ✅ **SSH** – Encrypted SSH connections
- ✅ **Telnet** – Traditional Telnet support
- ✅ **Console** – Extensible for serial console support

### Supported Debug Modes

1. **Authentication Debug (fnbamd)** – RADIUS, LDAP, and TACACS+ authentication issues
2. **FortiToken Debug** – Hardware FortiToken troubleshooting
3. **FortiToken Cloud Debug** – FortiToken Cloud integration issues
4. **SSL VPN Debug** – SSL VPN connectivity and authentication issues
5. **IPsec VPN Debug** – IPsec tunnel establishment and encryption problems
6. **OSPF Routing Debug** – OSPF routing protocol issues
7. **BGP Routing Debug** – BGP routing protocol issues
8. **Packet Flow Debug** – Trace packet paths through the firewall
9. **WAD Proxy Debug** – Web application firewall and proxy issues
10. **IPS Engine Debug** – Intrusion Prevention System issues
11. **HA Debug** – High Availability cluster issues
12. **DNS Debug** – DNS resolution and forwarding issues
13. **DHCP Debug** – DHCP server issues
14. **FortiLink Debug** – FortiSwitch integration issues
15. **SD-WAN Debug** – SD-WAN path selection issues
16. **ZTNA Debug** – Zero Trust Network Access issues

### Core Capabilities

- 🔌 **Real-time connection monitoring** – Display connection status
- 📊 **Live debug output** – Refresh debug information every second
- 💾 **Output export** – Save debug output as a text file
- 🎯 **Auto-scroll** – Optional auto-scroll to the latest output
- 📝 **Timestamps** – Each line includes a timestamp
- 🧹 **Clear output** – Reset the displayed output at any time
- 📈 **Statistics** – Show line counts and monitoring status

## Architecture

### Backend (Python/Flask)
- **app.py** – Flask REST API server
  - Handles SSH/Telnet connections
  - Executes FortiGate commands
  - Collects debug output in real time
  - Provides download support

### Frontend (React)
- **index.html** – Single-page React application
  - Modern UI
  - Real-time updates
  - Responsive design
  - Tailwind CSS styling

## Installation and Usage

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the backend server

```bash
python app.py
```

The backend runs at `http://localhost:5000`.

### 3. Open the frontend

Open `index.html` directly in your browser or host it with a simple HTTP server:

```bash
# Python 3
python -m http.server 8000
```

Then visit `http://localhost:8000`.

### 4. Connect to FortiGate

1. Fill in the connection form:
   - **Host Address**: FortiGate IP address
   - **Port**: SSH port (default 22) or Telnet port (default 23)
   - **Connection Type**: SSH or Telnet
   - **Username**: FortiGate admin username
   - **Password**: Corresponding password

2. Click **Connect**

### 5. Start Debug Monitoring

1. Choose a debug mode from the dropdown
2. Click **Start Monitoring**
3. Observe the live output
4. Click **Stop Monitoring** when done
5. Click **Download Output** to save the logs

## API Reference

### List Debug Modes
```
GET /api/debug-modes
```

Response example:
```json
{
  "modes": [
    {
      "id": "authentication",
      "name": "Authentication Debug (fnbamd)",
      "start_commands": [...],
      "stop_commands": [...]
    },
    ...
  ]
}
```

### Connect to FortiGate
```
POST /api/connect
Content-Type: application/json

{
  "host": "192.168.1.99",
  "port": 22,
  "username": "admin",
  "password": "password",
  "connection_type": "ssh"
}
```

### Start Debug Monitoring
```
POST /api/start-debug
Content-Type: application/json

{
  "session_id": "xxx",
  "debug_mode": "authentication"
}
```

### Stop Debug Monitoring
```
POST /api/stop-debug
Content-Type: application/json

{
  "session_id": "xxx",
  "output_id": "yyy",
  "debug_mode": "authentication"
}
```

### Get Debug Output
```
POST /api/get-output
Content-Type: application/json

{
  "session_id": "xxx"
}
```

### Download Output File
```
POST /api/download-output
Content-Type: application/json

{
  "output_id": "yyy"
}
```

### Disconnect
```
POST /api/disconnect
Content-Type: application/json

{
  "session_id": "xxx"
}
```

## FortiGate Command Reference

### Authentication Debug (fnbamd)
```bash
diagnose debug reset
diagnose debug console timestamp enable
diagnose debug application fnbamd -1
diagnose debug enable

# Stop
diagnose debug application fnbamd 0
diagnose debug reset
```

### FortiToken Debug
```bash
diagnose debug application forticldd 255
diagnose fortitoken debug enable

# Check FortiToken status
diagnose fortitoken info

# Stop
diagnose fortitoken debug disable
diagnose debug application forticldd 0
```

### SSL VPN Debug
```bash
diagnose debug application sslvpn -1
diagnose debug enable

# Stop
diagnose debug application sslvpn 0
diagnose debug reset
```

### IPsec VPN Debug
```bash
diagnose vpn ike log-filter clear
diagnose debug application ike -1
diagnose debug enable

# Stop
diagnose debug application ike 0
diagnose debug reset
```

### Packet Flow Debug
```bash
diagnose debug flow filter clear
diagnose debug flow filter saddr <source-ip>
diagnose debug flow filter daddr <destination-ip>
diagnose debug flow filter port <port>
diagnose debug flow show console enable
diagnose debug flow show function-name enable
diagnose debug console timestamp enable
diagnose debug enable
diagnose debug flow trace start 100

# Stop
diagnose debug flow trace stop
diagnose debug disable
diagnose debug reset
```

## Security Recommendations

1. **Avoid production use for long periods** – Debugging generates heavy logs
2. **Prefer SSH over Telnet** – SSH provides encryption
3. **Restrict management access** – Limit FortiGate management interface to trusted IPs
4. **Use a dedicated debug account** – Grant minimal permissions
5. **Stop debug sessions promptly** – Debugging impacts performance
6. **Protect sensitive data** – Downloaded output may contain confidential information

## Troubleshooting

### Connection Failed
- Verify FortiGate IP and port
- Ensure firewall rules allow SSH/Telnet access
- Confirm username and password
- Check network connectivity

### No Debug Output
- Confirm the correct debug mode is selected
- Trigger relevant traffic or events
- Some modes require specific triggers
- Verify FortiGate system load is healthy

### Output Incomplete
- Increase the output buffer
- Reduce debug verbosity
- Apply more specific filters

## Future Enhancements

1. Add console (serial) connection support
2. Allow multiple simultaneous connections
3. Add debug output search
4. Support syntax highlighting for output
5. Provide common debug command templates
6. Save connection presets
7. Export to CSV
8. Integrate log analysis tools

## Tech Stack

- **Backend**: Python 3.8+, Flask, Paramiko
- **Frontend**: React 18, Tailwind CSS
- **Connectivity**: SSH (Paramiko), Telnet (telnetlib)

## License

MIT License

## Contributing

Issues and pull requests are welcome!

## Changelog

### v1.0.0 (2024)
- Initial release
- SSH and Telnet support
- 16 debug modes implemented
- Real-time output monitoring
- File export functionality

---

**Note**: This tool is intended for diagnostics and troubleshooting. Avoid running debug sessions in production for extended periods because logging volume can impact FortiGate performance.
