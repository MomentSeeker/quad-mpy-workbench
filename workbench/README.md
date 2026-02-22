# 机器人积木编程工作台（独立部署）

## 1. 启动工作台服务（带代理，推荐）

在项目根目录执行：

```bash
python3 workbench/server.py --port 8001
```

打开：

- `http://127.0.0.1:8001/?robot=http://192.168.2.182`

其中 `robot=` 用来预填机器人地址。

## 2. 为什么需要代理

机器人端接口保持不变且不加 CORS 头时，浏览器从“独立域名/端口”的网页直接请求 `http://机器人IP/control` 会被跨域拦截。

工作台服务提供 `/api/control` 作为同域转发：

- 浏览器 → `POST /api/control`（同域，不跨域）
- 工作台服务 → `POST http://机器人IP/control`（服务端转发，不受浏览器 CORS 限制）

