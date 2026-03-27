import requests
import yaml
from datetime import datetime

gitlabip_proxies = []
public_proxies = []
seen_names = set()
name_counter = {}

EDGEGO_SOURCES = {
    'clash.meta2': {
        'url': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml',
        'pages': range(1, 7),
        'type': 'yaml'
    },
    'hysteria': {
        'url': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/hysteria/{}/config.json',
        'pages': range(1, 5),
        'type': 'json'
    },
    'hysteria2': {
        'url': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/hysteria2/{}/config.json',
        'pages': range(1, 5),
        'type': 'json'
    },
}

PUBLIC_SUBS = [
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml',
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/clash.yml',
    'https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml',
]

RULES = """# 本地网络
- DOMAIN-SUFFIX,local,DIRECT
- IP-CIDR,127.0.0.0/8,DIRECT
- IP-CIDR,10.0.0.0/8,DIRECT
- IP-CIDR,172.16.0.0/12,DIRECT
- IP-CIDR,192.168.0.0/16,DIRECT
- IP-CIDR,224.0.0.0/4,DIRECT
- IP-CIDR,255.255.255.255/32,DIRECT
- GEOIP,CN,DIRECT

# Tailscale 虚拟网络
- IP-CIDR,100.64.0.0/10,DIRECT
- IP-CIDR,100.0.0.0/8,DIRECT

# 广告
- DOMAIN-SUFFIX,ad.zanox.com,REJECT
- DOMAIN-SUFFIX,adcolony.com,REJECT
- DOMAIN-SUFFIX,admob.com,REJECT
- DOMAIN-SUFFIX,ads.twitter.com,REJECT
- DOMAIN-SUFFIX,advertising.com,REJECT
- DOMAIN-SUFFIX,doubleclick.net,REJECT
- DOMAIN-SUFFIX,googlesyndication.com,REJECT

# 国内常见网站直连
- DOMAIN-SUFFIX,cn,DIRECT
- DOMAIN-SUFFIX,baidu.com,DIRECT
- DOMAIN-SUFFIX,qq.com,DIRECT
- DOMAIN-SUFFIX,weixin.com,DIRECT
- DOMAIN-SUFFIX,taobao.com,DIRECT
- DOMAIN-SUFFIX,tmall.com,DIRECT
- DOMAIN-SUFFIX,jd.com,DIRECT
- DOMAIN-SUFFIX,alipay.com,DIRECT
- DOMAIN-SUFFIX,163.com,DIRECT
- DOMAIN-SUFFIX,bilibili.com,DIRECT
- DOMAIN-SUFFIX,tencent.com,DIRECT
- DOMAIN-SUFFIX,weibo.com,DIRECT
- DOMAIN-SUFFIX,csdn.net,DIRECT
- DOMAIN-SUFFIX,ithome.com,DIRECT
- DOMAIN-SUFFIX,netease.com,DIRECT

# Microsoft
- DOMAIN-SUFFIX,microsoft.com,DIRECT
- DOMAIN-SUFFIX,office.com,DIRECT
- DOMAIN-KEYWORD,microsoft,DIRECT
- DOMAIN-KEYWORD,azure,DIRECT
- DOMAIN-KEYWORD,githubusercontent,DIRECT

# Apple
- DOMAIN-SUFFIX,apple.com,DIRECT
- DOMAIN-SUFFIX,icloud.com,DIRECT

# Steam
- DOMAIN-SUFFIX,steamcontent.com,DIRECT
- DOMAIN-KEYWORD,steamcommunity,DIRECT
- DOMAIN-KEYWORD,steammobile,DIRECT

# 默认规则
- MATCH,🚀 节点选择
"""

def sanitize_name(name):
    import re
    if not name or not isinstance(name, str):
        return f"node_{len(seen_names) + 1}"
    if name.startswith('http'):
        return f"node_{len(seen_names) + 1}"
    name = re.sub(r'[^\w\u4e00-\u9fff\-_ ]', '', name)
    if len(name) > 50:
        name = name[:50]
    return name if name.strip() else f"node_{len(seen_names) + 1}"

def add_proxy(proxy, source):
    global seen_names, name_counter
    
    name = proxy.get('name', f"node_{len(gitlabip_proxies) + len(public_proxies) + 1}")
    name = sanitize_name(name)
    final_name = name
    if final_name in seen_names:
        if name not in name_counter:
            name_counter[name] = 1
        name_counter[name] += 1
        final_name = f"{name}_{name_counter[name]}"
    
    proxy['name'] = final_name
    seen_names.add(final_name)
    
    if source == 'gitlabip':
        gitlabip_proxies.append(proxy)
    else:
        public_proxies.append(proxy)

def parse_clash_yaml(data):
    proxies = []
    if data and 'proxies' in data:
        for p in data['proxies']:
            ptype = p.get('type', '')
            if ptype not in ['select', 'fallback', 'url-test']:
                proxies.append(p)
    return proxies

def parse_hysteria_json(config):
    proxies = []
    try:
        if isinstance(config, dict) and 'server' in config:
            server = config.get('server', '')
            if ':' in server:
                host, port = server.split(':', 1)
                up = config.get('up_mbps', 10)
                down = config.get('down_mbps', 50)
                if isinstance(up, str):
                    up = int(up.split()[0]) if up.split() else 10
                if isinstance(down, str):
                    down = int(down.split()[0]) if down.split() else 50
                proxies.append({
                    'name': f"hysteria_{host}",
                    'type': 'hysteria',
                    'server': host,
                    'port': int(port),
                    'up': up,
                    'down': down,
                    'auth-str': config.get('auth_str', ''),
                    'obfs': config.get('obfs', ''),
                    'sni': config.get('server_name', ''),
                    'skip-cert-verify': config.get('insecure', True),
                })
    except:
        pass
    return proxies

def parse_hysteria2_json(config):
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

def fetch_edgego():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取 EdgeGo 节点...")
    
    for source_name, config in EDGEGO_SOURCES.items():
        for page in config['pages']:
            try:
                url = config['url'].format(page)
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200:
                    proxies = []
                    if config['type'] == 'yaml':
                        data = yaml.safe_load(resp.text)
                        proxies = parse_clash_yaml(data)
                    elif source_name == 'hysteria':
                        proxies = parse_hysteria_json(resp.json())
                    elif source_name == 'hysteria2':
                        proxies = parse_hysteria2_json(resp.json())
                    
                    for p in proxies:
                        add_proxy(p, 'gitlabip')
                    
                    if proxies:
                        print(f"  {source_name}/{page}: +{len(proxies)}")
            except Exception as e:
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
                    count = 0
                    for p in data['proxies']:
                        if p.get('type') not in ['select', 'fallback', 'url-test']:
                            add_proxy(p, 'public')
                            count += 1
                    if count > 0:
                        print(f"  {sub_url.split('/')[-2]}: +{count}")
        except:
            pass
    
    print(f"  公共节点: {len(public_proxies)} 个")

def main():
    fetch_edgego()
    fetch_public()
    
    print(f"\n总计: EdgeGo {len(gitlabip_proxies)} 个, 公共 {len(public_proxies)} 个")
    
    all_proxies = gitlabip_proxies + public_proxies
    
    if not all_proxies:
        print("没有获取到任何节点!")
        return
    
    gitlabip_names = [p['name'] for p in gitlabip_proxies] if gitlabip_proxies else ['DIRECT']
    public_names = [p['name'] for p in public_proxies] if public_proxies else ['DIRECT']
    
    rules_list = [
        'DOMAIN-SUFFIX,local,DIRECT',
        'IP-CIDR,127.0.0.0/8,DIRECT',
        'IP-CIDR,10.0.0.0/8,DIRECT',
        'IP-CIDR,172.16.0.0/12,DIRECT',
        'IP-CIDR,192.168.0.0/16,DIRECT',
        'IP-CIDR,224.0.0.0/4,DIRECT',
        'IP-CIDR,255.255.255.255/32,DIRECT',
        'GEOIP,CN,DIRECT',
        'IP-CIDR,100.64.0.0/10,DIRECT',
        'IP-CIDR,100.0.0.0/8,DIRECT',
        'DOMAIN-SUFFIX,cn,DIRECT',
        'DOMAIN-SUFFIX,baidu.com,DIRECT',
        'DOMAIN-SUFFIX,qq.com,DIRECT',
        'DOMAIN-SUFFIX,weixin.com,DIRECT',
        'DOMAIN-SUFFIX,taobao.com,DIRECT',
        'DOMAIN-SUFFIX,tmall.com,DIRECT',
        'DOMAIN-SUFFIX,jd.com,DIRECT',
        'DOMAIN-SUFFIX,alipay.com,DIRECT',
        'DOMAIN-SUFFIX,163.com,DIRECT',
        'DOMAIN-SUFFIX,bilibili.com,DIRECT',
        'DOMAIN-SUFFIX,tencent.com,DIRECT',
        'DOMAIN-SUFFIX,weibo.com,DIRECT',
        'DOMAIN-SUFFIX,csdn.net,DIRECT',
        'DOMAIN-SUFFIX,ithome.com,DIRECT',
        'DOMAIN-SUFFIX,netease.com,DIRECT',
        'DOMAIN-SUFFIX,microsoft.com,DIRECT',
        'DOMAIN-SUFFIX,office.com,DIRECT',
        'DOMAIN-SUFFIX,apple.com,DIRECT',
        'DOMAIN-SUFFIX,icloud.com,DIRECT',
        'DOMAIN-SUFFIX,steamcontent.com,DIRECT',
        'MATCH,🚀 节点选择',
    ]
    
    config = {
        'proxies': all_proxies,
        'proxy-groups': [
            {'name': '🚀 节点选择', 'type': 'select', 'proxies': ['EdgeGo节点', '公共节点', '🐢 延迟最低']},
            {'name': 'EdgeGo节点', 'type': 'select', 'proxies': gitlabip_names},
            {'name': '公共节点', 'type': 'select', 'proxies': public_names},
            {'name': '🐢 延迟最低', 'type': 'url-test', 'proxies': [p['name'] for p in all_proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50}
        ],
        'rules': rules_list,
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
