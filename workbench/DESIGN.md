# 机器人积木编程工作台 - 设计文档

## 1. 系统概述

机器人积木编程工作台是一个类似 Scratch 的可视化编程环境，用户可以通过拖拽积木的方式编写机器人控制程序，无需编写代码即可控制四足机器人执行各种动作。

### 1.1 核心特性

- **可视化编程**：拖拽积木式编程，降低使用门槛
- **实时控制**：通过网络实时控制机器人
- **跨域代理**：内置代理服务解决浏览器跨域限制
- **模拟模式**：支持不发送请求的模拟运行
- **响应式设计**：适配不同屏幕尺寸

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    前端 (index.html)                       │  │
│  │  ┌─────────┐  ┌─────────┐  ┌───────────────────────────┐  │  │
│  │  │ 积木库  │  │ 工作区  │  │     运行控制 & 日志       │  │  │
│  │  └─────────┘  └─────────┘  └───────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /api/control
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    工作台代理服务 (server.py)                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ThreadingHTTPServer                                     │    │
│  │  ├── 静态文件服务 (HTML/CSS/JS)                          │    │
│  │  └── /api/control 代理转发                               │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP POST /control
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    机器人端 (ESP32 + MicroPython)                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  RobotWifi (robot_wifi.py)                               │    │
│  │  ├── HTTP Server (端口 80)                               │    │
│  │  └── 命令解析 & 执行                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Quad (quad.py)                                          │    │
│  │  ├── 8 个舵机控制                                        │    │
│  │  └── 动作执行 (forward, backward, turn_L, dance...)     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Oscillator (oscillator.py)                              │    │
│  │  └── PWM 舵机信号生成                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 前端实现原理

### 2.1 技术栈

- **纯原生技术**：HTML5 + CSS3 + Vanilla JavaScript
- **无外部依赖**：不依赖任何第三方框架或库
- **单文件架构**：所有代码集成在单个 HTML 文件中

### 2.2 核心模块

#### 2.2.1 积木定义系统

积木通过数据结构定义，包含分类、类型、标题、样式等信息：

```javascript
const BLOCKS = [
  { cat: 'motion', type: 'forward', title: '前进', subtitle: '走一步', className: 'c-motion', badge: '运动' },
  { cat: 'motion', type: 'backward', title: '后退', subtitle: '退一步', className: 'c-motion', badge: '运动' },
  { cat: 'motion', type: 'turn_L', title: '左转', subtitle: '转一下', className: 'c-motion', badge: '运动' },
  { cat: 'motion', type: 'turn_R', title: '右转', subtitle: '转一下', className: 'c-motion', badge: '运动' },
  { cat: 'control', type: 'wait', title: '等待', subtitle: '暂停一会儿', className: 'c-control', badge: '控制' },
  { cat: 'control', type: 'repeat', title: '重复', subtitle: '循环执行', className: 'c-control', badge: '控制' },
  // ... 更多积木定义
]
```

**积木分类**：
| 分类 | 说明 | 颜色 |
|------|------|------|
| motion | 运动类动作 | 蓝色 (#4c97ff) |
| control | 控制流积木 | 橙色 (#ffab19) |
| events | 事件触发器 | 黄色 (#ffd500) |

#### 2.2.2 拖拽系统 (Drag & Drop)

使用 HTML5 原生拖拽 API 实现：

**拖拽流程**：

```
┌──────────────┐    dragstart     ┌──────────────┐    dragover     ┌──────────────┐
│   积木库     │ ──────────────▶  │   拖拽中     │ ──────────────▶ │   工作区     │
│  (palette)   │                  │  (payload)   │                  │  (stack)     │
└──────────────┘                  └──────────────┘                  └──────────────┘
       │                                                                   │
       │  设置 dataTransfer                                                │
       │  { kind: 'palette', type: 'forward' }                            │
       ▼                                                                   ▼
  创建可拖拽元素                                                    drop 事件处理
```

**核心代码逻辑**：

```javascript
// 积木库拖拽开始
el.addEventListener('dragstart', (e) => {
  const payload = JSON.stringify({ kind: 'palette', type: blockDef.type })
  e.dataTransfer.setData('text/plain', payload)
  e.dataTransfer.effectAllowed = 'copy'
})

// 工作区接收拖拽
stackEl.addEventListener('drop', (e) => {
  const payload = tryReadPayload(e.dataTransfer.getData('text/plain'))
  if (payload.kind === 'palette') {
    const inst = createInstance(payload.type, {})
    stackEl.appendChild(inst)
  }
})
```

**拖拽类型**：
- `copy`：从积木库拖到工作区，创建新实例
- `move`：在工作区内重新排序

#### 2.2.3 程序编译器

将可视化积木编译为可执行的指令序列：

```javascript
function compileStack(stackEl, ctx) {
  const children = Array.from(stackEl.querySelectorAll(':scope > .inst'))
  const out = []
  for (const el of children) {
    const type = el.dataset.type
    if (type === 'start') continue
    if (type === 'wait') {
      const ms = clampInt(input.value, 0, 60000, 0)
      out.push({ kind: 'wait', ms })
      continue
    }
    if (type === 'repeat') {
      const times = clampInt(input.value, 1, 20, 1)
      const inner = compileStack(childStack, ctx)
      for (let i = 0; i < times; i++) {
        out.push(...inner)
      }
      continue
    }
    out.push({ kind: 'command', command: type })
  }
  return out
}
```

**编译输出示例**：

```javascript
// 积木序列：前进 → 等待(500ms) → 左转
[
  { kind: 'command', command: 'forward' },
  { kind: 'wait', ms: 500 },
  { kind: 'command', command: 'turn_L' }
]
```

#### 2.2.4 运行时引擎

**运行状态管理**：

```javascript
let running = false
let currentRunState = null

// 运行状态结构
const runState = {
  stop: false,           // 停止标志
  timers: [],            // 定时器列表（用于清理）
  abortControllers: []   // AbortController 列表（用于取消请求）
}
```

**执行流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                        runProgram()                              │
├─────────────────────────────────────────────────────────────────┤
│  1. compileProgram() → 编译积木为指令序列                         │
│  2. 设置 running = true, 禁用运行按钮                            │
│  3. for (step of steps):                                        │
│     ├── step.kind === 'wait' → sleep(step.ms)                   │
│     └── step.kind === 'command' → postCommand(step.command)     │
│  4. 清理状态，恢复 UI                                            │
└─────────────────────────────────────────────────────────────────┘
```

**请求发送逻辑**：

```javascript
async function postCommand(command, runState) {
  const s = readSettings()
  let url, body
  
  if (s.useProxy) {
    // 通过代理发送（推荐）
    url = '/api/control'
    body = JSON.stringify({ baseUrl: s.baseUrl, command })
  } else {
    // 直接发送（需要机器人支持 CORS）
    url = (s.baseUrl || '') + '/control'
    body = JSON.stringify({ command })
  }
  
  // 带超时和重试的请求
  const res = await fetchWithTimeout(url, opts, s.timeoutMs, runState)
  return res
}
```

#### 2.2.5 设置持久化

使用 localStorage 保存用户配置：

```javascript
const LS_KEYS = {
  baseUrl: 'quad_robot_base_url',    // 机器人地址
  timeout: 'quad_http_timeout_ms',   // 请求超时
  retry: 'quad_http_retry',          // 重试次数
  useProxy: 'quad_use_proxy'         // 是否使用代理
}
```

---

## 3. 后端实现原理

### 3.1 工作台代理服务 (server.py)

#### 3.1.1 架构设计

```python
class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path.rstrip('/') != '/api/control':
            return  # 404
        
        # 1. 解析请求
        req = json.loads(raw)
        command = req.get('command')
        base_url = req.get('baseUrl')
        
        # 2. 转发到机器人
        target = f'{base_url}/control'
        body = json.dumps({'command': command})
        
        # 3. 发送请求并返回响应
        with urllib.request.urlopen(r, timeout=15) as resp:
            # 返回机器人响应
```

#### 3.1.2 为什么需要代理

```
场景：前端部署在 http://localhost:8001，机器人地址 http://192.168.2.182

❌ 直接请求（跨域被拦截）：
浏览器 → http://192.168.2.182/control
       ↑ CORS 错误：不同源

✅ 通过代理（绕过跨域）：
浏览器 → http://localhost:8001/api/control（同源，不跨域）
代理服务 → http://192.168.2.182/control（服务端请求，无 CORS 限制）
```

#### 3.1.3 CORS 处理

```python
def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    super().end_headers()

def do_OPTIONS(self):
    self.send_response(HTTPStatus.NO_CONTENT)
    self.end_headers()
```

### 3.2 机器人端服务 (robot_wifi.py)

#### 3.2.1 网络模式

**AP 模式（热点模式）**：
```
ESP32 作为热点 ←──→ 手机/电脑直连
IP: 192.168.2.182（固定）
```

**STA 模式（路由模式）**：
```
路由器 ←──→ ESP32
         ↑
    手机/电脑（同一局域网）
```

#### 3.2.2 HTTP 服务器

```python
class RobotWifi:
    def create_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', 80))
        server_socket.listen(128)
        
        while True:
            client_socket, addr = server_socket.accept()
            self.handle_request(client_socket)
```

#### 3.2.3 请求处理

```python
def handle_request(self, client_socket):
    request = client_socket.recv(1024)
    method, path, _ = request_lines[0].split()
    
    if method == "POST" and path == "/control":
        # 解析命令并执行
        command = json.loads(post_data).get("command")
        method = getattr(self.robot, command)  # 动态调用机器人方法
        method()
        return json.dumps({"status": "200", "msg": command})
    else:
        # 返回控制页面
        return self.html
```

### 3.3 机器人控制核心 (quad.py)

#### 3.3.1 硬件架构

```
四足机器人舵机布局（8 个舵机）：

    前 (head)
    ┌───────────────────────────────────────┐
    │  FRH(右前髋)    │    FLH(左前髋)       │
    │  Pin12          │    Pin16             │
    │  ───────────────┼───────────────       │
    │  FRL(右前腿)    │    FLL(左前腿)       │
    │  Pin25          │    Pin18             │
    ├───────────────────────────────────────┤
    │  BRH(右后髋)    │    BLH(左后髋)       │
    │  Pin13          │    Pin17             │
    │  ───────────────┼───────────────       │
    │  BRL(右后腿)    │    BLL(左后腿)       │
    │  Pin26          │    Pin19             │
    └───────────────────────────────────────┘
    后 (tail)
```

#### 3.3.2 运动控制原理

**振荡器模式**：

每个舵机通过振荡器生成周期性运动：

```python
def oscillateServos(self, amplitude, offset, period, phase, cycle=1.0):
    for i in range(self._servo_totals):
        self._servo[i].SetO(offset[i])      # 偏移量
        self._servo[i].SetA(amplitude[i])   # 振幅
        self._servo[i].SetT(period[i])      # 周期
        self._servo[i].SetPh(phase[i])      # 相位
    
    # 按时间刷新舵机位置
    while x <= period[0] * cycle + ref:
        for i in range(self._servo_totals):
            self._servo[i].refresh()
```

**步态参数说明**：

| 参数 | 说明 | 示例 |
|------|------|------|
| amplitude | 振幅（运动幅度） | [15, 15, 20, 20, ...] |
| offset | 偏移量（中心位置偏移） | [0, 0, -15, 15, ...] |
| period | 周期（完成一次运动的时间） | [800, 800, 400, 400, ...] |
| phase | 相位（各舵机运动的时间差） | [0, 0, 90, 90, ...] |

#### 3.3.3 动作实现示例

**前进动作 (forward)**：

```python
def forward(self, steps=3, t=800):
    x_amp = 15      # X 方向振幅
    z_amp = 15      # Z 方向振幅（抬腿高度）
    ap = 10         # 前后偏移
    hi = 15         # 抬腿高度
    
    amplitude = [x_amp, x_amp, z_amp, z_amp, x_amp, x_amp, z_amp, z_amp]
    offset = [
        0 + ap - front_x,   # FRH
        0 - ap + front_x,   # FLH
        0 - hi,             # FRL
        0 + hi,             # FLL
        0 - ap - front_x,   # BRH
        0 + ap + front_x,   # BLH
        0 + hi,             # BRL
        0 - hi              # BLL
    ]
    phase = [0, 0, 90, 90, 180, 180, 90, 90]
    
    self._execute(amplitude, offset, period, phase, steps)
```

**相位图解**：

```
时间轴 ─────────────────────────────────────────▶

FRH: ████████░░░░░░░░████████░░░░░░░░  (相位 0°)
FLH: ████████░░░░░░░░████████░░░░░░░░  (相位 0°)
FRL: ░░░░░░░░████████░░░░░░░░████████  (相位 90°)
FLL: ░░░░░░░░████████░░░░░░░░████████  (相位 90°)
BRH: ░░░░░░░░░░░░░░░░████████░░░░░░░░  (相位 180°)
BLH: ░░░░░░░░░░░░░░░░████████░░░░░░░░  (相位 180°)
BRL: ░░░░░░░░████████░░░░░░░░████████  (相位 90°)
BLL: ░░░░░░░░████████░░░░░░░░████████  (相位 90°)
```

---

## 4. 通信协议

### 4.1 API 接口

#### 4.1.1 控制接口

**请求**：
```http
POST /control HTTP/1.1
Content-Type: application/json

{
  "command": "forward"
}
```

**响应**：
```json
{
  "status": "200",
  "msg": "forward"
}
```

#### 4.1.2 代理接口

**请求**：
```http
POST /api/control HTTP/1.1
Content-Type: application/json

{
  "baseUrl": "http://192.168.2.182",
  "command": "forward"
}
```

**响应**：转发机器人的原始响应

### 4.2 支持的命令

| 命令 | 说明 | 参数 |
|------|------|------|
| `forward` | 前进 | steps=3, t=800 |
| `backward` | 后退 | steps=3, t=800 |
| `turn_L` | 左转 | steps=2, t=1000 |
| `turn_R` | 右转 | steps=2, t=1000 |
| `omni_walk` | 横移 | steps=2, t=1000 |
| `home` | 回到原位 | - |
| `dance` | 跳舞 | steps=3, t=2000 |
| `hello` | 打招呼 | - |
| `up_down` | 上下动 | steps=2, t=2000 |
| `push_up` | 俯卧撑 | steps=2, t=2000 |
| `front_back` | 前后摆 | steps=2, t=1000 |
| `wave_hand` | 挥挥手 | steps=3, t=2000 |
| `scared` | 害怕 | - |
| `moonwalk_L` | 太空步 | steps=4, t=2000 |

---

## 5. 启动流程

### 5.1 启动脚本

```bash
#!/bin/zsh
# start-workbench.sh

robot_url="${1:-}"      # 第一个参数：机器人地址
port="${2:-8001}"       # 第二个参数：端口号
host="0.0.0.0"          # 监听地址

# 设置环境变量
if [[ -n "$robot_url" ]]; then
  export ROBOT_BASE_URL="$robot_url"
fi

# 启动服务
python3 workbench/server.py --port "$port" --host "$host"
```

### 5.2 启动方式

**方式一：使用启动脚本**
```bash
./start-workbench.sh http://192.168.2.182 8001
```

**方式二：直接运行**
```bash
python3 workbench/server.py --port 8001 --host 0.0.0.0
```

**方式三：带环境变量**
```bash
ROBOT_BASE_URL=http://192.168.2.182 python3 workbench/server.py --port 8001
```

### 5.3 访问方式

```
http://127.0.0.1:8001/?robot=http://192.168.2.182
```

URL 参数 `robot=` 会自动填充到设置中的 Base URL。

---

## 6. 数据流图

### 6.1 完整请求流程

```
┌─────────┐    拖拽积木     ┌─────────┐    编译     ┌─────────┐
│  用户   │ ─────────────▶ │  工作区  │ ────────▶ │ 指令序列 │
└─────────┘                └─────────┘            └─────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        运行循环                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  for step of steps:                                      │   │
│  │    ├── wait → sleep(ms)                                  │   │
│  │    └── command → POST /api/control                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/control                                              │
│  Body: { "baseUrl": "http://192.168.2.182", "command": "forward" }│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  server.py (代理)                                               │
│  1. 解析 baseUrl 和 command                                     │
│  2. POST http://192.168.2.182/control                          │
│  3. 返回响应                                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  robot_wifi.py (机器人端)                                       │
│  1. 解析 command                                                │
│  2. getattr(robot, command)()                                  │
│  3. 返回 {"status": "200", "msg": "forward"}                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  quad.py (动作执行)                                             │
│  1. 设置振荡器参数                                              │
│  2. 执行步态周期                                                │
│  3. 舵机运动                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 文件结构

```
quad-mpy/
├── workbench/
│   ├── index.html          # 前端主页面（积木编程界面）
│   ├── index-apple.html    # 备用前端页面
│   ├── server.py           # 工作台代理服务
│   └── README.md           # 使用说明
├── quad.py                 # 四足机器人控制类
├── robot.py                # 机器人基类
├── robot_wifi.py           # WiFi 控制和 HTTP 服务
├── oscillator.py           # 舵机振荡器
├── main.py                 # 主程序入口
├── index.html              # 机器人端控制页面
└── start-workbench.sh      # 启动脚本
```

---

## 8. 技术亮点

### 8.1 前端

1. **零依赖**：纯原生实现，无需构建工具
2. **响应式设计**：适配桌面和移动设备
3. **模块化 CSS**：使用 CSS 变量实现主题
4. **优雅的交互**：拖拽反馈、状态指示、日志系统

### 8.2 后端

1. **轻量代理**：仅 130 行代码实现完整代理功能
2. **线程安全**：使用 ThreadingHTTPServer 支持并发
3. **跨域处理**：完整的 CORS 支持
4. **灵活配置**：支持环境变量和命令行参数

### 8.3 机器人端

1. **动态命令**：使用 `getattr` 实现命令动态分发
2. **振荡器模式**：优雅的步态控制算法
3. **双网络模式**：支持 AP 和 STA 两种连接方式

---

## 9. 扩展指南

### 9.1 添加新动作

在 `quad.py` 中添加新方法：

```python
def new_action(self, steps=2, t=1000):
    amplitude = [...]
    offset = [...]
    phase = [...]
    self._execute(amplitude, offset, period, phase, steps)
```

在前端 `BLOCKS` 数组中添加积木定义：

```javascript
{ cat: 'motion', type: 'new_action', title: '新动作', subtitle: '描述', className: 'c-motion', badge: '运动' }
```

### 9.2 添加新积木类型

1. 在 `BLOCKS` 中定义新积木
2. 在 `createInstance()` 中处理特殊 UI（如参数输入）
3. 在 `compileStack()` 中处理编译逻辑

---

## 10. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | - | 初始版本，支持基础积木编程 |
| 1.1 | - | 添加代理服务，解决跨域问题 |
| 1.2 | - | 添加重复积木，支持循环控制 |
