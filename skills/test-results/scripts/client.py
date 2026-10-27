#!/usr/bin/env python3
"""通过受管接口读取用例、记录真实测试结果，不直接修改 SQLite。"""
import argparse
import json
import mimetypes
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import urllib.parse
import uuid


class Client:
    def __init__(self, config=None):
        config_path = Path(config or os.environ.get('TEST_RESULTS_CONFIG') or Path.home() / '.config/test-results/client.json')
        self.config = json.loads(config_path.read_text())
        if config_path.stat().st_mode & 0o077:
            raise ValueError('录入配置必须设置为600权限')

    def request(self, method, endpoint, payload=None):
        write = endpoint.startswith('/write/')
        base = self.config['write_url' if write else 'read_url'].rstrip('/')
        headers = {'Accept': 'application/json'}
        if write: headers['Authorization'] = 'Bearer ' + self.config['token']
        if payload is not None: headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(base + endpoint, data=None if payload is None else json.dumps(payload, ensure_ascii=False).encode(), headers=headers, method=method)
        # 本机录入与私网读取直接连接，避免系统代理改变请求目标。
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=30) as response:
            return json.load(response)

    def upload(self, filename):
        file = Path(filename)
        boundary = 'TestResults' + uuid.uuid4().hex
        media_type = mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        safe_name = file.name.replace('"', '_').replace('\r', '_').replace('\n', '_')
        body = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{safe_name}"\r\nContent-Type: {media_type}\r\n\r\n'.encode() + file.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
        request = urllib.request.Request(self.config['write_url'].rstrip('/') + '/write/artifacts', data=body, headers={'Authorization': 'Bearer ' + self.config['token'], 'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=60) as response:
            return json.load(response)

    def download(self, artifact_id, target):
        request = urllib.request.Request(self.config['read_url'].rstrip('/') + '/artifacts/' + urllib.parse.quote(artifact_id, safe=''))
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=60) as response:
            data = response.read()
            with Path(target).open('xb') as file: file.write(data)
            return {'saved_to':str(Path(target).resolve()), 'bytes':len(data), 'media_type':response.headers.get('Content-Type')}

    def link(self, project, run, case=None):
        read_url = self.config['read_url']
        configured = urllib.parse.urlsplit(read_url)
        if configured.scheme not in ('http', 'https') or not configured.netloc:
            raise ValueError('查看服务网址必须是有效的 HTTP(S) 地址')
        if configured.username is not None or configured.password is not None:
            raise ValueError('查看服务网址不能包含账号或密码')
        if '?' in read_url or '#' in read_url:
            raise ValueError('查看服务网址不能包含查询参数或片段')
        path = read_url.rstrip('/') + '/projects/' + urllib.parse.quote(project, safe='')
        path += '/runs/' + urllib.parse.quote(run, safe='')
        if case is not None:
            path += '/cases/' + urllib.parse.quote(case, safe='')
        return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='私有客户端配置；未提供时读取 TEST_RESULTS_CONFIG 或默认 ~/.config/test-results/client.json')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('projects', help='读取项目')
    cases = sub.add_parser('cases', help='读取完整用例定义')
    cases.add_argument('--project', required=True)
    cases.add_argument('--path', help='仅显示目录包含该文字的用例')
    runs = sub.add_parser('runs', help='读取历史测试轮次')
    runs.add_argument('--project', required=True)
    run = sub.add_parser('show', help='读取一轮的范围和结果')
    run.add_argument('--run', required=True)
    history = sub.add_parser('history', help='读取用例历史')
    history.add_argument('--project', required=True)
    history.add_argument('--case', required=True)
    link = sub.add_parser('link', help='生成项目、轮次和可选用例的页面链接')
    link.add_argument('--project', required=True)
    link.add_argument('--run', required=True)
    link.add_argument('--case')
    for command in ['catalog', 'start', 'result']:
        item = sub.add_parser(command, help={'catalog':'录入用例目录','start':'开始一轮测试','result':'记录一条实际结果'}[command])
        item.add_argument('--file', required=True, help='JSON正文文件')
        if command == 'result': item.add_argument('--run', required=True)
    finish = sub.add_parser('finish', help='完成或中断一轮测试')
    finish.add_argument('--run', required=True)
    finish.add_argument('--state', choices=['completed', 'interrupted'], default='completed')
    finish.add_argument('--summary', required=True)
    artifact = sub.add_parser('artifact', help='复制截图或脱敏报告至系统并返回附件编号')
    artifact.add_argument('--file', required=True)
    download = sub.add_parser('download', help='下载已有截图或报告供核对')
    download.add_argument('--artifact', required=True)
    download.add_argument('--output', required=True, help='当前工作区已登记临时目录中的新文件')
    args = parser.parse_args()
    client = Client(args.config)
    command = args.command
    if command == 'projects': value = client.request('GET', '/api/projects')
    elif command == 'cases':
        value = client.request('GET', f'/api/projects/{args.project}/cases')
        if args.path: value = [case for case in value if args.path in '/'.join(case['path'])]
    elif command == 'runs': value = client.request('GET', f'/api/projects/{args.project}/runs')
    elif command == 'show': value = client.request('GET', f'/api/runs/{args.run}')
    elif command == 'history': value = client.request('GET', f'/api/projects/{args.project}/cases/{args.case}')
    elif command == 'link': value = client.link(args.project, args.run, args.case)
    elif command == 'artifact': value = client.upload(args.file)
    elif command == 'download': value = client.download(args.artifact, args.output)
    elif command == 'finish': value = client.request('POST', f'/write/runs/{args.run}/finish', {'state':args.state, 'summary':args.summary})
    else:
        payload = json.loads(Path(args.file).read_text())
        method, endpoint = {'catalog':('PUT','/write/catalog'), 'start':('POST','/write/runs'), 'result':('POST',f'/write/runs/{getattr(args,"run","")}/results')}[command]
        value = client.request(method, endpoint, payload)
    print(value if command == 'link' else json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as error:
        print(f'HTTP {error.code}: {error.read().decode()}', file=sys.stderr)
        raise SystemExit(1)
