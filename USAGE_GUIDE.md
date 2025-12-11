# FortiGate Debug Monitor - 使用指南

## 快速开始

### 步骤1: 安装和启动

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 启动后端服务器(方式一: 使用启动脚本)
./start.sh

# 或者 (方式二: 直接运行)
python3 app.py
```

### 步骤2: 打开Web界面

有两种方式打开前端:

**方式一: 直接在浏览器打开**
```
file:///path/to/index.html
```

**方式二: 使用HTTP服务器**
```bash
# 在项目目录下运行
python3 -m http.server 8000

# 然后访问
http://localhost:8000
```

### 步骤3: 连接FortiGate

1. 在连接表单填写FortiGate信息:
   - 主机: `192.168.1.99`
   - 端口: `22` (SSH) 或 `23` (Telnet)
   - 用户名: `admin`
   - 密码: `你的密码`
   - 连接类型: `SSH` (推荐)

2. 点击"连接"按钮

## 常见使用场景

### 场景1: 调试RADIUS认证失败

**问题**: 用户无法通过RADIUS服务器认证登录SSL VPN

**解决步骤**:
1. 连接到FortiGate
2. 选择debug模式: "认证调试 (Authentication - fnbamd)"
3. 点击"开始监控"
4. 让用户尝试登录SSL VPN
5. 观察debug输出,查找认证失败原因
6. 点击"停止监控"
7. 下载debug输出进行详细分析

**期望输出示例**:
```
[2024-12-10 10:30:15.123] handle_req-Rcvd auth req 123456 for user1 in RADIUS_Server
[2024-12-10 10:30:15.234] fnbamd_radius_auth_send-Compose RADIUS request
[2024-12-10 10:30:15.345] __fnbamd_rad_send-Sent radius req to server 'RADIUS_Server'
[2024-12-10 10:30:15.456] fnbamd_radius_auth_validate_pkt-RADIUS resp code 2 (Access-Accept)
```

### 场景2: 调试IPsec VPN隧道无法建立

**问题**: 两个FortiGate之间的IPsec VPN隧道无法建立

**解决步骤**:
1. 连接到FortiGate
2. 选择debug模式: "IPsec VPN调试"
3. 点击"开始监控"
4. 尝试建立VPN隧道 (或等待自动重连)
5. 观察IKE协商过程
6. 查找phase 1或phase 2失败原因
7. 下载输出分析详细错误

**常见问题特征**:
- Pre-shared key不匹配: `authentication failed`
- 加密算法不匹配: `no proposal chosen`
- 对端不可达: `timeout waiting for response`

### 场景3: 调试数据包流

**问题**: 流量无法通过FortiGate,不确定是否被policy阻止

**解决步骤**:
1. 连接到FortiGate
2. 选择debug模式: "数据包流调试 (Debug Flow)"
3. 在CLI中设置过滤器(可选,通过"执行自定义命令"):
   ```
   diagnose debug flow filter saddr 192.168.1.100
   diagnose debug flow filter daddr 8.8.8.8
   diagnose debug flow filter port 443
   ```
4. 点击"开始监控"
5. 触发流量
6. 观察数据包路径
7. 确认是policy允许还是拒绝

**期望输出示例**:
```
[2024-12-10 10:35:20.123] id=20085 trace_id=1 func=print_pkt_detail
[2024-12-10 10:35:20.124] packet received from port1
[2024-12-10 10:35:20.125] src=192.168.1.100:54321
[2024-12-10 10:35:20.126] dst=8.8.8.8:443
[2024-12-10 10:35:20.127] proto=6
[2024-12-10 10:35:20.128] find a session, id-00012345
[2024-12-10 10:35:20.129] npu_flag=00 npu_rgwy=8.8.8.8:443
```

### 场景4: 调试FortiToken认证

**问题**: FortiToken Mobile无法正常工作

**解决步骤**:
1. 连接到FortiGate
2. 选择debug模式: "FortiToken Cloud调试"
3. 点击"开始监控"
4. 用户尝试使用FortiToken登录
5. 观察FortiToken验证过程
6. 检查是否能连接到FortiGuard服务器
7. 下载输出进行分析

### 场景5: 调试SD-WAN路径选择

**问题**: SD-WAN没有选择期望的链路

**解决步骤**:
1. 连接到FortiGate
2. 选择debug模式: "SD-WAN调试"
3. 点击"开始监控"
4. 产生需要路由的流量
5. 观察SD-WAN规则匹配和路径选择
6. 检查链路健康检查状态
7. 分析为什么选择了特定链路

## 高级技巧

### 技巧1: 使用过滤器减少输出

对于数据包流调试,可以使用过滤器:

```bash
# 只显示特定源IP的流量
diagnose debug flow filter saddr 192.168.1.100

# 只显示特定目标IP的流量
diagnose debug flow filter daddr 8.8.8.8

# 只显示特定端口的流量
diagnose debug flow filter port 443

# 组合多个过滤器
diagnose debug flow filter saddr 192.168.1.100
diagnose debug flow filter daddr 8.8.8.8
diagnose debug flow filter port 443
```

### 技巧2: 调整Debug级别

某些debug模式支持不同的详细级别:

```bash
# 最详细的输出
diagnose debug application fnbamd -1

# 中等详细级别
diagnose debug application fnbamd 7

# 最小输出
diagnose debug application fnbamd 1
```

### 技巧3: 限制输出行数

对于debug flow,可以限制捕获的包数量:

```bash
# 只捕获100个数据包
diagnose debug flow trace start 100

# 无限捕获
diagnose debug flow trace start 999999
```

### 技巧4: 同时启用多个Debug

可以同时启用多个debug模式(谨慎使用):

```bash
diagnose debug application fnbamd -1
diagnose debug application sslvpn -1
diagnose debug enable
```

## 性能考虑

### ⚠️ 重要警告

1. **Debug会产生大量CPU负载** - 不要在高负载的生产环境长时间运行
2. **输出会占用大量内存** - 及时停止和清空输出
3. **某些debug模式特别消耗资源** - 如packet flow debug

### 最佳实践

1. ✅ **只在需要时启用debug**
2. ✅ **使用过滤器减少输出**
3. ✅ **在非业务高峰期调试**
4. ✅ **完成后立即停止debug**
5. ✅ **定期清空输出缓冲区**

## 常见错误和解决方案

### 错误1: "连接失败: Connection refused"

**原因**: 
- FortiGate SSH/Telnet服务未启用
- 防火墙规则阻止连接
- IP地址或端口错误

**解决**:
```bash
# 在FortiGate上启用SSH
config system global
    set admin-ssh-port 22
end

# 允许管理IP访问
config firewall address
    edit "Admin_IP"
        set type iprange
        set start-ip 192.168.1.100
        set end-ip 192.168.1.100
    next
end
```

### 错误2: "认证失败"

**原因**: 用户名或密码错误

**解决**: 
- 验证用户名和密码
- 确认账号有管理员权限
- 检查账号是否被锁定

### 错误3: "无Debug输出"

**原因**:
- 没有触发相关事件
- Debug命令未正确执行
- 输出被过滤器过滤

**解决**:
1. 确认debug已启动(查看"监控中"状态)
2. 触发相关事件(如登录尝试、流量发送等)
3. 检查过滤器设置
4. 尝试清空输出并重新开始

### 错误4: "连接断开"

**原因**:
- 网络不稳定
- FortiGate重启
- 会话超时

**解决**:
- 检查网络连接
- 重新连接
- 如果频繁断开,考虑使用有线连接

## 输出分析技巧

### 分析认证Debug输出

查找关键字:
- `Rcvd auth req` - 收到认证请求
- `Access-Accept` - 认证成功
- `Access-Reject` - 认证失败
- `timeout` - 超时
- `Group 'XXX'` - 用户组匹配

### 分析IPsec Debug输出

查找关键字:
- `negotiation result accepted` - Phase 1成功
- `established` - 隧道建立成功
- `authentication failed` - 认证失败
- `no proposal chosen` - 算法不匹配
- `Dead Peer Detection` - DPD检测

### 分析数据包流Debug输出

查找关键字:
- `find a session` - 找到会话
- `new session` - 创建新会话
- `policy_check` - 策略检查
- `denied by` - 被策略拒绝
- `NAT` - NAT转换

## 支持的FortiOS版本

此工具理论上支持所有FortiOS版本,但已在以下版本测试:
- FortiOS 7.6.x ✅
- FortiOS 7.4.x ✅
- FortiOS 7.2.x ✅
- FortiOS 7.0.x ✅

较旧版本的命令语法可能略有不同,请参考对应版本的CLI参考手册。

## 获取帮助

如遇到问题:
1. 查看README.md文档
2. 检查FortiGate CLI参考手册
3. 访问Fortinet技术文档网站
4. 联系Fortinet技术支持

---

**提示**: 保存此文档以便离线参考!
