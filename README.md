# FortiGate Debug Monitor Web Application

一个强大的 Web 应用程序，用于远程连接 FortiGate 防火墙并监控各种 debug 模式输出。

## 功能特点

### 连接方式
- ✅ **SSH连接** - 安全的SSH协议连接
- ✅ **Telnet连接** - 支持传统Telnet连接
- ✅ **Console连接** - 可扩展支持串口console

### 支持的Debug模式

1. **认证调试 (fnbamd)** - 用于RADIUS、LDAP、TACACS+等认证问题
2. **FortiToken调试** - 硬件FortiToken问题诊断
3. **FortiToken Cloud调试** - FortiToken Cloud集成问题
4. **SSL VPN调试** - SSL VPN连接和认证问题
5. **IPsec VPN调试** - IPsec隧道建立和加密问题
6. **OSPF路由调试** - OSPF路由协议问题
7. **BGP路由调试** - BGP路由协议问题
8. **数据包流调试 (Debug Flow)** - 跟踪数据包通过防火墙的路径
9. **WAD代理调试** - Web应用防火墙和代理问题
10. **IPS引擎调试** - 入侵防御系统问题
11. **HA调试** - 高可用性集群问题
12. **DNS调试** - DNS解析和转发问题
13. **DHCP调试** - DHCP服务器问题
14. **FortiLink调试** - FortiSwitch集成问题
15. **SD-WAN调试** - SD-WAN路径选择问题
16. **ZTNA调试** - Zero Trust Network Access问题

### 核心功能

- 🔌 **实时连接监控** - 实时显示连接状态
- 📊 **实时debug输出** - 每秒自动刷新debug信息
- 💾 **输出导出** - 将debug输出保存为文本文件
- 🎯 **自动滚动** - 可选择是否自动滚动到最新输出
- 📝 **时间戳** - 每行输出包含精确时间戳
- 🧹 **清空输出** - 随时清空当前显示的输出
- 📈 **统计信息** - 显示输出行数和监控状态

## 系统架构

### 后端 (Python/Flask)
- **app.py** - Flask REST API服务器
  - 处理SSH/Telnet连接
  - 执行FortiGate命令
  - 实时捕获debug输出
  - 提供文件下载功能

### 前端 (React)
- **index.html** - 单页面React应用
  - 现代化UI界面
  - 实时数据更新
  - 响应式设计
  - Tailwind CSS样式

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务器

```bash
python app.py
```

后端服务器将在 `http://localhost:5000` 运行

### 3. 打开前端界面

使用浏览器打开 `index.html` 文件，或者使用简单的HTTP服务器:

```bash
# Python 3
python -m http.server 8000
```

然后访问 `http://localhost:8000`

### 4. 连接FortiGate

1. 在连接表单中填写:
   - **主机地址**: FortiGate的IP地址
   - **端口**: SSH端口(默认22)或Telnet端口(默认23)
   - **连接类型**: 选择SSH或Telnet
   - **用户名**: FortiGate管理员用户名
   - **密码**: 对应的密码

2. 点击"连接"按钮

### 5. 开始Debug监控

1. 从下拉菜单选择要监控的debug模式
2. 点击"开始监控"按钮
3. 观察实时输出
4. 完成后点击"停止监控"
5. 可以点击"下载输出"保存调试信息

## API接口文档

### 获取Debug模式列表
```
GET /api/debug-modes
```

响应示例:
```json
{
  "modes": [
    {
      "id": "authentication",
      "name": "认证调试 (Authentication - fnbamd)",
      "start_commands": [...],
      "stop_commands": [...]
    },
    ...
  ]
}
```

### 连接FortiGate
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

### 开始Debug监控
```
POST /api/start-debug
Content-Type: application/json

{
  "session_id": "xxx",
  "debug_mode": "authentication"
}
```

### 停止Debug监控
```
POST /api/stop-debug
Content-Type: application/json

{
  "session_id": "xxx",
  "output_id": "yyy",
  "debug_mode": "authentication"
}
```

### 获取Debug输出
```
POST /api/get-output
Content-Type: application/json

{
  "session_id": "xxx"
}
```

### 下载输出文件
```
POST /api/download-output
Content-Type: application/json

{
  "output_id": "yyy"
}
```

### 断开连接
```
POST /api/disconnect
Content-Type: application/json

{
  "session_id": "xxx"
}
```

## FortiGate命令参考

### 认证调试 (fnbamd)
```bash
diagnose debug reset
diagnose debug console timestamp enable
diagnose debug application fnbamd -1
diagnose debug enable

# 停止
diagnose debug application fnbamd 0
diagnose debug reset
```

### FortiToken调试
```bash
diagnose debug application forticldd 255
diagnose fortitoken debug enable

# 查看FortiToken状态
diagnose fortitoken info

# 停止
diagnose fortitoken debug disable
diagnose debug application forticldd 0
```

### SSL VPN调试
```bash
diagnose debug application sslvpn -1
diagnose debug enable

# 停止
diagnose debug application sslvpn 0
diagnose debug reset
```

### IPsec VPN调试
```bash
diagnose vpn ike log-filter clear
diagnose debug application ike -1
diagnose debug enable

# 停止
diagnose debug application ike 0
diagnose debug reset
```

### 数据包流调试
```bash
diagnose debug flow filter clear
diagnose debug flow filter saddr <源IP>
diagnose debug flow filter daddr <目标IP>
diagnose debug flow filter port <端口>
diagnose debug flow show console enable
diagnose debug flow show function-name enable
diagnose debug console timestamp enable
diagnose debug enable
diagnose debug flow trace start 100

# 停止
diagnose debug flow trace stop
diagnose debug disable
diagnose debug reset
```

## 安全建议

1. **不要在生产环境直接使用** - 这是一个调试工具
2. **使用SSH而非Telnet** - SSH提供加密连接
3. **限制访问IP** - 只允许特定IP访问FortiGate管理接口
4. **使用专用调试账号** - 创建具有只读权限的专用账号
5. **及时停止Debug** - Debug会产生大量日志,影响性能
6. **保护敏感信息** - 下载的debug输出可能包含敏感信息

## 故障排除

### 连接失败
- 检查FortiGate IP地址和端口
- 确认FortiGate防火墙规则允许SSH/Telnet访问
- 验证用户名和密码正确
- 检查网络连接

### 无Debug输出
- 确认已选择正确的debug模式
- 检查是否有相关流量触发debug
- 某些debug模式需要特定的触发条件
- 查看FortiGate系统负载是否过高

### 输出不完整
- 增加output buffer大小
- 减少debug详细级别
- 使用更具体的过滤器

## 扩展功能建议

1. **添加Console串口连接支持**
2. **支持多个同时连接**
3. **添加debug输出搜索功能**
4. **支持debug输出语法高亮**
5. **添加常用debug命令模板**
6. **支持保存连接配置**
7. **添加导出为CSV格式**
8. **集成日志分析工具**

## 技术栈

- **后端**: Python 3.8+, Flask, Paramiko
- **前端**: React 18, Tailwind CSS
- **连接**: SSH (Paramiko), Telnet (telnetlib)

## 许可证

MIT License

## 作者

FortiGate Debug Monitor Tool

## 贡献

欢迎提交Issue和Pull Request!

## 更新日志

### v1.0.0 (2024)
- 初始版本发布
- 支持SSH和Telnet连接
- 实现16种常用debug模式
- 实时输出监控
- 文件导出功能

---

**注意**: 此工具仅用于诊断和故障排除目的。请勿在生产环境中长时间运行debug,因为会产生大量日志并可能影响FortiGate性能。
