# Output A

最基本的反向代理：在 nginx 配置的 http 块里写一个 server，用 proxy_pass 把请求转发到后端。示例：server { listen 80; server_name example.com; location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; } }。要点：proxy_pass 末尾带不带斜杠会影响路径拼接；WebSocket 需额外设置 Upgrade/Connection 头并开启 HTTP/1.1；要 HTTPS 就得配证书并把 80 跳转 443；后端若用 Unix socket 则写 proxy_pass http://unix:/路径。改完先 nginx -t 检查语法，再 reload。若涉及负载均衡（upstream 多台后端）、Cookie 域、超时或路径改写等，需要你说清具体场景，我才能给出贴合的配置。
