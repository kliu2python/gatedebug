# FortiGate Debug Monitor - Usage Guide

## Quick Start

### Step 1: Install and Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start the backend server (option 1: startup script)
./start.sh

# or (option 2: run directly)
python3 app.py
```

### Step 2: Open the Web UI

You can open the frontend two ways:

**Option 1: Open directly in the browser**
```
file:///path/to/index.html
```

**Option 2: Use an HTTP server**
```bash
# From the project directory
python3 -m http.server 8000

# Then visit
http://localhost:8000
```

### Step 3: Connect to FortiGate

1. Fill out the connection form:
   - Host: `192.168.1.99`
   - Port: `22` (SSH) or `23` (Telnet)
   - Username: `admin`
   - Password: `your-password`
   - Connection Type: `SSH` (recommended)

2. Click **Connect**

## Common Scenarios

### Scenario 1: Troubleshooting RADIUS authentication failures

**Problem**: Users cannot authenticate to SSL VPN through the RADIUS server.

**Steps**:
1. Connect to FortiGate
2. Select debug mode: "Authentication Debug (fnbamd)"
3. Click **Start Monitoring**
4. Ask the user to attempt SSL VPN login
5. Review debug output for failure reasons
6. Click **Stop Monitoring**
7. Download the debug output for analysis

**Expected output example**:
```
[2024-12-10 10:30:15.123] handle_req-Rcvd auth req 123456 for user1 in RADIUS_Server
[2024-12-10 10:30:15.234] fnbamd_radius_auth_send-Compose RADIUS request
[2024-12-10 10:30:15.345] __fnbamd_rad_send-Sent radius req to server 'RADIUS_Server'
[2024-12-10 10:30:15.456] fnbamd_radius_auth_validate_pkt-RADIUS resp code 2 (Access-Accept)
```

### Scenario 2: IPsec VPN tunnel will not establish

**Problem**: The IPsec VPN tunnel between two FortiGate devices will not come up.

**Steps**:
1. Connect to FortiGate
2. Select debug mode: "IPsec VPN Debug"
3. Click **Start Monitoring**
4. Attempt to bring the tunnel up (or wait for auto-retry)
5. Observe the IKE negotiation process
6. Identify phase 1 or phase 2 failures
7. Download the output for detailed review

**Common symptoms**:
- Pre-shared key mismatch: `authentication failed`
- Cipher mismatch: `no proposal chosen`
- Remote peer unreachable: `timeout waiting for response`

### Scenario 3: Packet flow debugging

**Problem**: Traffic is not passing through FortiGate and you need to know if a policy is blocking it.

**Steps**:
1. Connect to FortiGate
2. Select debug mode: "Packet Flow Debug"
3. (Optional) Set filters via **Execute Custom Command** in the CLI:
   ```
   diagnose debug flow filter saddr 192.168.1.100
   diagnose debug flow filter daddr 8.8.8.8
   diagnose debug flow filter port 443
   ```
4. Click **Start Monitoring**
5. Generate the traffic
6. Observe the packet path
7. Confirm whether a policy allows or blocks it

**Expected output example**:
```
[2024-12-10 10:35:20.123] id=20085 trace_id=1 func=print_pkt_detail
[2024-12-10 10:35:20.124] packet received from port1
[2024-12-10 10:35:20.125] src=192.168.1.100:54321
[2024-12-10 10:35:20.126] dst=8.8.8.8:443
[2024-12-10 10:35:20.127] proto=6
[2024-12-10 10:35:20.128] find a session, id-00012345
[2024-12-10 10:35:20.129] npu_flag=00 npu_rgwy=8.8.8.8:443
```

### Scenario 4: FortiToken authentication issues

**Problem**: FortiToken Mobile is not working correctly.

**Steps**:
1. Connect to FortiGate
2. Select debug mode: "FortiToken Cloud Debug"
3. Click **Start Monitoring**
4. Have the user attempt a FortiToken login
5. Observe the FortiToken validation process
6. Check connectivity to FortiGuard servers
7. Download the output for analysis

### Scenario 5: SD-WAN path selection

**Problem**: SD-WAN is not choosing the desired link.

**Steps**:
1. Connect to FortiGate
2. Select debug mode: "SD-WAN Debug"
3. Click **Start Monitoring**
4. Generate traffic that requires routing
5. Observe SD-WAN rule matching and path selection
6. Check health-check status for each link
7. Analyze why a specific link was chosen

## Advanced Tips

### Tip 1: Use filters to reduce output

For packet flow debugging you can filter traffic:

```bash
# Show only traffic from a specific source IP
diagnose debug flow filter saddr 192.168.1.100

# Show only traffic to a specific destination IP
diagnose debug flow filter daddr 8.8.8.8

# Show only a specific port
diagnose debug flow filter port 443

# Combine filters
diagnose debug flow filter saddr 192.168.1.100
diagnose debug flow filter daddr 8.8.8.8
diagnose debug flow filter port 443
```

### Tip 2: Adjust debug verbosity

Some modes support different verbosity levels:

```bash
# Maximum detail
diagnose debug application fnbamd -1

# Medium detail
diagnose debug application fnbamd 7

# Minimal output
diagnose debug application fnbamd 1
```

### Tip 3: Limit output volume

For debug flow you can limit the captured packet count:

```bash
# Capture only 100 packets
diagnose debug flow trace start 100

# Capture indefinitely
diagnose debug flow trace start 999999
```

### Tip 4: Enable multiple debug modes (use with caution)

You can run more than one debug mode at the same time:

```bash
diagnose debug application fnbamd -1
diagnose debug application sslvpn -1
diagnose debug enable
```

## Performance Considerations

### ⚠️ Important warnings

1. **Debugging is CPU-intensive** – Avoid prolonged use in high-load production environments.
2. **Output consumes memory** – Stop sessions and clear output promptly.
3. **Some modes are resource-heavy** – Packet flow debug is especially intensive.

### Best practices

1. ✅ Enable debug only when needed
2. ✅ Use filters to reduce output
3. ✅ Troubleshoot during off-peak hours
4. ✅ Stop debug as soon as possible
5. ✅ Clear the output buffer regularly

## Common Errors and Fixes

### Error 1: "Connection failed: Connection refused"

**Causes**:
- SSH/Telnet service disabled on FortiGate
- Firewall rules blocking access
- Incorrect IP or port

**Fix**:
```bash
# Enable SSH on FortiGate
config system global
    set admin-ssh-port 22
end

# Allow management IP access
config firewall address
    edit "Admin_IP"
        set type iprange
        set start-ip 192.168.1.100
        set end-ip 192.168.1.100
    next
end
```

### Error 2: "Authentication failed"

**Cause**: Incorrect username or password

**Fix**:
- Verify credentials
- Confirm the account has admin privileges
- Check whether the account is locked

### Error 3: "No debug output"

**Causes**:
- No triggering events
- Debug commands not executed correctly
- Output filtered out

**Fix**:
1. Confirm debug is running (see monitoring status)
2. Trigger relevant events (login attempts, traffic, etc.)
3. Check filter settings
4. Clear output and restart monitoring

### Error 4: "Connection lost"

**Causes**:
- Unstable network
- FortiGate rebooted
- Session timeout

**Fix**:
- Check network connectivity
- Reconnect
- If disconnects are frequent, use a wired connection

## Output Analysis Tips

### Reading authentication debug output

Look for keywords:
- `Rcvd auth req` – Authentication request received
- `Access-Accept` – Authentication succeeded
- `Access-Reject` – Authentication failed
- `timeout` – Timeout occurred
- `Group 'XXX'` – User group matching

### Reading IPsec debug output

Look for keywords:
- `negotiation result accepted` – Phase 1 succeeded
- `established` – Tunnel established
- `authentication failed` – Authentication failure
- `no proposal chosen` – Algorithm mismatch
- `Dead Peer Detection` – DPD checks

### Reading packet flow debug output

Look for keywords:
- `find a session` – Session found
- `new session` – New session created
- `policy_check` – Policy check
- `denied by` – Blocked by policy
- `NAT` – NAT translation applied

## Supported FortiOS Versions

The tool should work with all FortiOS versions and has been tested with:
- FortiOS 7.6.x ✅
- FortiOS 7.4.x ✅
- FortiOS 7.2.x ✅
- FortiOS 7.0.x ✅

Older versions may have slightly different CLI syntax; refer to your version's CLI reference.

## Getting Help

If you run into issues:
1. Review the README.md documentation
2. Check the FortiGate CLI reference manual
3. Visit the Fortinet documentation site
4. Contact Fortinet technical support

---

**Tip**: Save this guide for offline reference!
