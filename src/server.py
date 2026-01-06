#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GLM 配额查询 Web 服务器
在浏览器中打开美观的 HTML 页面查看配额
"""

import http.server
import socketserver
import json
import urllib.request
import webbrowser
import socket
from pathlib import Path
from threading import Thread

PORT = 8848
HTML_FILE = Path(__file__).parent / "viewer.html"


def find_free_port(start_port=8848):
    """查找可用端口"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start_port


def get_auth_info():
    """从 settings.json 获取认证信息"""
    settings_file = Path.home() / '.claude' / 'settings.json'

    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            env_vars = settings.get('env', {})
            return (
                env_vars.get('ANTHROPIC_BASE_URL', ''),
                env_vars.get('ANTHROPIC_AUTH_TOKEN', '')
            )
    return '', ''


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.serve_html()
        elif self.path == '/api/config':
            self.serve_config()
        elif self.path.startswith('/api/proxy'):
            self.proxy_api()
        else:
            super().do_GET()

    def serve_html(self):
        if HTML_FILE.exists():
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(HTML_FILE, 'r', encoding='utf-8') as f:
                self.wfile.write(f.read().encode('utf-8'))
        else:
            self.send_error(404, 'HTML file not found')

    def serve_config(self):
        base_url, auth_token = get_auth_info()
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps({
            'hasConfig': bool(base_url and auth_token),
            'platform': 'ZHIPU' if 'bigmodel' in base_url else 'ZAI'
        }, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def proxy_api(self):
        """代理 API 请求"""
        base_url, auth_token = get_auth_info()

        if not auth_token:
            self.send_error(401, 'No auth token found')
            return

        from urllib.parse import urlparse, parse_qs, urlencode
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        base_domain = base_url.split('/api/')[0]

        if '/model-usage' in self.path:
            target_url = f"{base_domain}/api/monitor/usage/model-usage"
        elif '/tool-usage' in self.path:
            target_url = f"{base_domain}/api/monitor/usage/tool-usage"
        elif '/quota-limit' in self.path:
            target_url = f"{base_domain}/api/monitor/usage/quota/limit"
        else:
            self.send_error(400, 'Unknown API endpoint')
            return

        if query:
            target_url += '?' + urlencode({k: v[0] for k, v in query.items()})

        try:
            req = urllib.request.Request(target_url)
            req.add_header('Authorization', auth_token)
            req.add_header('Content-Type', 'application/json')

            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read().decode('utf-8')

            json_data = json.loads(data)
            if isinstance(json_data, dict) and 'data' in json_data:
                json_data = json_data['data']

            # 转换配额限制字段
            if isinstance(json_data, dict) and 'limits' in json_data:
                for limit in json_data['limits']:
                    if limit.get('type') == 'TOKENS_LIMIT':
                        limit['type'] = 'Token使用(5 Hour)'
                    elif limit.get('type') == 'TIME_LIMIT':
                        limit['type'] = 'MCP使用(1 Month)'
                        limit['currentUsage'] = limit.get('currentValue', 0)
                        limit['totol'] = limit.get('usage', 0)

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(json_data, ensure_ascii=False).encode('utf-8'))

        except urllib.error.HTTPError as e:
            error_response = {'error': f'HTTP {e.code}', 'message': e.read().decode('utf-8', errors='ignore')[:500]}
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            error_response = {'error': 'Error', 'message': str(e)}
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        pass  # 静默模式


def main():
    actual_port = find_free_port(PORT)

    base_url, auth_token = get_auth_info()
    if not auth_token:
        print("⚠️  警告: 未找到 API Token")
        print("   请确保 Claude Code 已正确配置")
        print()

    with socketserver.TCPServer(("", actual_port), Handler) as httpd:
        port_msg = f"http://localhost:{actual_port}"
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          🚀 GLM 配额查询服务器已启动！                         ║
║                                                                ║
║          📱 请在浏览器中打开:                                  ║
║          {port_msg}{' ' * (50 - len(port_msg))}║
║                                                                ║
║          按 Ctrl+C 停止服务器                                   ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
        """)

        Thread(target=lambda: webbrowser.open(f'http://localhost:{actual_port}'), daemon=True).start()

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 服务器已停止")


if __name__ == '__main__':
    main()
