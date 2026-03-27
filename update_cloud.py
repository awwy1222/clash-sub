import requests
import yaml
import base64
import socket
import concurrent.futures
from datetime import datetime

GITEE_TOKEN = "1b3d7f9a6abdd26e15a44367f8695751"
GITEE_USER = "fwf1222"
GITEE_REPO = "clash-sub"

CLASH_SOURCES = {
    'clash': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml',
    'hysteria': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/hysteria/{}/config.json',
    'hysteria2': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/hysteria2/{}/config.json',
}

PUBLIC_SUBS = [
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml',
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/clash.yml',
    'https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml',
]

TEST_TIMEOUT = 5

all_proxies = []
seen_names = set()
name_counter = {}

def parse_hysteria(config):
    proxies = []
    try:
        if isinstance(config, dict) and 'server' in config:
            server = config.get('server', '')
            if ':' in server:
                host, port = server.split(':', 1)
                proxies.append({
                    'name': f"hysteria_{host}",
                    'type': 'hysteria',
                    'server': host,
                    'port': int(port),
                    'up': config.get('up_mbps', 10),
                    'down': config.get('down_mbps', 50),
                    'auth-str': config.get('auth_str', ''),
                    'obfs': config.get('obfs', ''),
                    'sni': config.get('server_name', ''),
                    'skip-cert-verify': config.get('insecure', True),
                })
    except:
        pass
    return proxies

def parse_hysteria2(config):
    proxies = []
    try:
        if isinstance(config, dict) and 'server' in config:
            proxies.append({
                'name': f"hysteria2_{config.get('server', '')}",
                'type': 'hysteria2',
                'server': config.get('server', ''),
                'port': config.get('server_port', 443),
                'password': config.get('password', ''),
                'sni': config.get('server_name', ''),
                'skip-cert-verify': config.get('insecure', False),
            })
    except:
        pass
    return proxies

def test_tcp_connect(proxy):
    """TCP 端口连接测试"""
    try:
        server = proxy.get('server', '')
        port = proxy.get('port', 0)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TEST_TIMEOUT)
        result = sock.connect_ex((server, port))
        sock.close()
        return result == 0
    except:
        return False

def fetch_nodes():
    global all_proxies, seen_names, name_counter
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取节点...")
    
    # Clash 节点
    for i in range(1, 7):
        url = CLASH_SOURCES['clash'].format(i)
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                data = yaml.safe_load(resp.text)
                if data and 'proxies' in data:
                    for proxy in data['proxies']:
                        pname = proxy.get('name', f"node_{len(all_proxies)+1}")
                        final_name = pname
                        if final_name in seen_names:
                            if pname not in name_counter:
                                name_counter[pname] = 1
                            name_counter[pname] += 1
                            final_name = f"{pname}_{name_counter[pname]}"
                        proxy['name'] = final_name
                        seen_names.add(final_name)
                        all_proxies.append(proxy)
                    print(f"  Clash/{i}: {len(data['proxies'])} 个")
        except:
            pass
    
    # Hysteria 节点
    for i in range(1, 5):
        url = CLASH_SOURCES['hysteria'].format(i)
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                proxies = parse_hysteria(resp.json())
                for proxy in proxies:
                    pname = proxy.get('name', f"hys_{len(all_proxies)+1}")
                    final_name = pname
                    if final_name in seen_names:
                        if pname not in name_counter:
                            name_counter[pname] = 1
                        name_counter[pname] += 1
                        final_name = f"{pname}_{name_counter[pname]}"
                    proxy['name'] = final_name
                    seen_names.add(final_name)
                    all_proxies.append(proxy)
                if proxies:
                    print(f"  Hysteria/{i}: {len(proxies)} 个")
        except:
            pass
    
    # Hysteria2 节点
    for i in range(1, 5):
        url = CLASH_SOURCES['hysteria2'].format(i)
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                proxies = parse_hysteria2(resp.json())
                for proxy in proxies:
                    pname = proxy.get('name', f"hys2_{len(all_proxies)+1}")
                    final_name = pname
                    if final_name in seen_names:
                        if pname not in name_counter:
                            name_counter[pname] = 1
                        name_counter[pname] += 1
                        final_name = f"{pname}_{name_counter[pname]}"
                    proxy['name'] = final_name
                    seen_names.add(final_name)
                    all_proxies.append(proxy)
                if proxies:
                    print(f"  Hysteria2/{i}: {len(proxies)} 个")
        except:
            pass
    
    # 公共订阅
    for sub_url in PUBLIC_SUBS:
        try:
            resp = requests.get(sub_url, timeout=15)
            if resp.status_code == 200:
                data = yaml.safe_load(resp.text)
                if data and 'proxies' in data:
                    for proxy in data['proxies']:
                        pname = proxy.get('name', f"pub_{len(all_proxies)+1}")
                        final_name = pname
                        if final_name in seen_names:
                            if pname not in name_counter:
                                name_counter[pname] = 1
                            name_counter[pname] += 1
                            final_name = f"{pname}_{name_counter[pname]}"
                        proxy['name'] = final_name
                        seen_names.add(final_name)
                        all_proxies.append(proxy)
                    print(f"  公共订阅: {len(data['proxies'])} 个")
        except:
            pass
    
    print(f"\n获取到 {len(all_proxies)} 个节点")
    return all_proxies

def verify_nodes(proxies):
    """验证节点 - 使用并行测试"""
    print("正在验证节点连通性...")
    valid = []
    invalid = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(test_tcp_connect, p): p for p in proxies}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if future.result():
                valid.append(futures[future])
            else:
                invalid += 1
            if (i + 1) % 10 == 0:
                print(f"  已验证 {i+1}/{len(proxies)}")
    
    print(f"验证完成: {len(valid)} 个可用, {invalid} 个不可用")
    return valid

def main():
    proxies = fetch_nodes()
    
    if not proxies:
        print("没有获取到任何节点!")
        return
    
    valid_proxies = proxies
    print("\n跳过节点验证（免费节点需要代理才能测试）")
    
    config = {
        'proxies': valid_proxies,
        'proxy-groups': [
            {'name': '🚀 节点选择', 'type': 'select', 'proxies': [p['name'] for p in valid_proxies]},
            {'name': '🐢 延迟最低', 'type': 'url-test', 'proxies': [p['name'] for p in valid_proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50}
        ],
        'rules': ['MATCH,🚀 节点选择']
    }
    
    yaml_content = yaml.dump(config, allow_unicode=True, sort_keys=False)
    sub_content = f'# Clash 订阅 - 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n# 节点数: {len(valid_proxies)}\n\n' + yaml_content
    
    with open('sub.yaml', 'w', encoding='utf-8') as f:
        f.write(sub_content)
    
    print(f"\n订阅文件已生成: sub.yaml")
    print(f"请手动提交到 Gitee: cd /d/脚本/clash-sub && git add . && git commit -m '更新' && git push")
    print("\n完成!")

def upload_to_gitee(content):
    get_resp = requests.get(f'https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml?access_token={GITEE_TOKEN}')
    sha = None
    if get_resp.status_code == 200:
        data = get_resp.json()
        if isinstance(data, dict):
            sha = data.get('sha')
    
    put_data = {
        'access_token': GITEE_TOKEN,
        'content': base64.b64encode(content.encode()).decode(),
        'message': f'自动更新订阅 - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    }
    if sha:
        put_data['sha'] = sha
    
    resp = requests.post(f'https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml', json=put_data)
    if resp.status_code == 201:
        print("  Gitee 上传成功!")
    else:
        print(f"  Gitee 上传失败: {resp.status_code}")

if __name__ == "__main__":
    main()
