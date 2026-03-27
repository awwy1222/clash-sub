import requests
import yaml
import socket
import concurrent.futures
from datetime import datetime

TEST_TIMEOUT = 4

gitlabip_proxies = []
public_proxies = []
seen_names = set()
name_counter = {}

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
            server = config.get('server', '')
            if ':' in server:
                host = server.split(':')[0]
                try:
                    port = int(server.split(':')[1].split(',')[0])
                except:
                    port = 443
                proxies.append({
                    'name': f"hysteria2_{host}",
                    'type': 'hysteria2',
                    'server': host,
                    'port': port,
                    'password': config.get('auth', ''),
                    'sni': config.get('tls', {}).get('sni', ''),
                    'skip-cert-verify': config.get('tls', {}).get('insecure', False),
                })
    except:
        pass
    return proxies

def add_proxy(proxy, source):
    global seen_names, name_counter
    pname = proxy.get('name', f"node_{len(gitlabip_proxies) + len(public_proxies) + 1}")
    final_name = pname
    if final_name in seen_names:
        if pname not in name_counter:
            name_counter[pname] = 1
        name_counter[pname] += 1
        final_name = f"{pname}_{name_counter[pname]}"
    
    proxy['name'] = final_name
    seen_names.add(final_name)
    
    if source == 'gitlabip':
        gitlabip_proxies.append(proxy)
    else:
        public_proxies.append(proxy)

def fetch_gitlabip():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取 EdgeGo 节点...")
    
    for i in range(1, 7):
        try:
            resp = requests.get(CLASH_SOURCES['clash'].format(i), timeout=15)
            if resp.status_code == 200:
                data = yaml.safe_load(resp.text)
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        add_proxy(p, 'gitlabip')
                    print(f"  Clash/{i}: +{len(data['proxies'])}")
        except:
            pass
    
    for i in range(1, 5):
        try:
            resp = requests.get(CLASH_SOURCES['hysteria'].format(i), timeout=15)
            if resp.status_code == 200:
                proxies = parse_hysteria(resp.json())
                for p in proxies:
                    add_proxy(p, 'gitlabip')
                if proxies:
                    print(f"  Hysteria/{i}: +{len(proxies)}")
        except:
            pass
    
    for i in range(1, 5):
        try:
            resp = requests.get(CLASH_SOURCES['hysteria2'].format(i), timeout=15)
            if resp.status_code == 200:
                proxies = parse_hysteria2(resp.json())
                for p in proxies:
                    add_proxy(p, 'gitlabip')
                if proxies:
                    print(f"  Hysteria2/{i}: +{len(proxies)}")
        except:
            pass
    
    print(f"  EdgeGo 节点: {len(gitlabip_proxies)} 个")

def fetch_public():
    print(f"\n获取公共订阅节点...")
    
    for sub_url in PUBLIC_SUBS:
        try:
            resp = requests.get(sub_url, timeout=30)
            if resp.status_code == 200:
                data = yaml.safe_load(resp.text)
                if data and 'proxies' in data:
                    for p in data['proxies']:
                        add_proxy(p, 'public')
                    print(f"  {sub_url.split('/')[-2]}: +{len(data['proxies'])}")
        except Exception as e:
            print(f"  {sub_url.split('/')[-2]}: 获取失败")

def main():
    fetch_gitlabip()
    fetch_public()
    
    print(f"\n总计: EdgeGo {len(gitlabip_proxies)} 个, 公共 {len(public_proxies)} 个")
    
    all_proxies = gitlabip_proxies + public_proxies
    
    if not all_proxies:
        print("没有获取到任何节点!")
        return
    
    gitlabip_names = [p['name'] for p in gitlabip_proxies] if gitlabip_proxies else ['DIRECT']
    public_names = [p['name'] for p in public_proxies] if public_proxies else ['DIRECT']
    
    config = {
        'proxies': all_proxies,
        'proxy-groups': [
            {'name': '🚀 节点选择', 'type': 'select', 'proxies': ['EdgeGo节点', '公共节点', '🐢 延迟最低']},
            {'name': 'EdgeGo节点', 'type': 'select', 'proxies': gitlabip_names},
            {'name': '公共节点', 'type': 'select', 'proxies': public_names},
            {'name': '🐢 延迟最低', 'type': 'url-test', 'proxies': all_proxies, 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50}
        ],
        'rules': ['MATCH,🚀 节点选择']
    }
    
    yaml_content = yaml.dump(config, allow_unicode=True, sort_keys=False)
    sub_content = f'# Clash 订阅 - 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n# EdgeGo: {len(gitlabip_proxies)} 个, 公共: {len(public_proxies)} 个\n\n' + yaml_content
    
    with open('sub.yaml', 'w', encoding='utf-8') as f:
        f.write(sub_content)
    
    print(f"\n订阅文件已生成: sub.yaml")
    print(f"  - EdgeGo 节点: {len(gitlabip_proxies)} 个")
    print(f"  - 公共节点: {len(public_proxies)} 个")

if __name__ == "__main__":
    main()
