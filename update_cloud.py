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

# 广告拦截列表
AD_DOMAINS = [
    'ad.zanox.com', 'adcolony.com', 'admob.com', 'ads.twitter.com',
    'advertising.com', 'doubleclick.net', 'googlesyndication.com',
    'googleadservices.com', 'adnxs.com', 'adsrvr.org', 'criteo.com',
    'applovin.com', 'unityads.unity3d.com', 'supersonic.com',
    'umeng.com', 'cnzz.com',
]

# 常用国内域名(直连兜底,GEOSITE,CN 之外的保险)
CN_DOMAINS = [
    'cn', 'baidu.com', 'qq.com', 'weixin.com', 'weixin.qq.com', 'wechat.com',
    'taobao.com', 'tmall.com', 'jd.com', 'alipay.com', 'aliyun.com',
    'alibaba.com', '163.com', '126.com', 'netease.com', 'bilibili.com',
    'biliapi.net', 'hdslb.com', 'tencent.com', 'weibo.com', 'weibo.cn',
    'csdn.net', 'ithome.com', 'zhihu.com', 'douban.com', 'xiaohongshu.com',
    'bytedance.com', 'douyin.com', 'douyinpic.com', 'kuaishou.com',
    'mi.com', 'xiaomi.com', 'miui.com', '12306.cn', '12306.com',
    'meituan.com', 'dianping.com', 'ele.me', 'ctrip.com', 'qunar.com',
    'sogou.com', 'so.com', '360.cn', '360.com', 'gitee.com', 'juejin.cn',
    'oschina.net', 'jianshu.com', 'iqiyi.com', 'youku.com', 'v.qq.com',
    'gtimg.com', 'qpic.cn', 'alicdn.com', 'taobaocdn.com', 'bdstatic.com',
    'bdimg.com', 'bytecdn.cn', 'pstatp.com', 'snssdk.com', 'zjcdn.com',
]

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

def is_valid_proxy(proxy):
    server = proxy.get('server', '')
    if not server:
        return False
    if server.startswith('[') and not server.endswith(']'):
        return False
    if len(server) < 3:
        return False
    # 过滤新版 VLESS 后量子加密节点(mlkem768x25519plus 等),
    # 旧内核客户端无法解析,会导致整个订阅加载失败
    if str(proxy.get('type', '')).lower() == 'vless':
        enc = proxy.get('encryption')
        if enc and str(enc).strip().lower() not in ('none', ''):
            return False
    return True

def add_proxy(proxy, source):
    global seen_names, name_counter
    
    if not is_valid_proxy(proxy):
        return
    
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
    
    # ===== 规则:国内全直连,其余全走代理 =====
    rules_list = []
    # 1. 局域网 / 私有地址直连
    rules_list += [
        'DOMAIN-SUFFIX,local,DIRECT',
        'DOMAIN-SUFFIX,lan,DIRECT',
        'IP-CIDR,127.0.0.0/8,DIRECT,no-resolve',
        'IP-CIDR,10.0.0.0/8,DIRECT,no-resolve',
        'IP-CIDR,172.16.0.0/12,DIRECT,no-resolve',
        'IP-CIDR,192.168.0.0/16,DIRECT,no-resolve',
        'IP-CIDR,100.64.0.0/10,DIRECT,no-resolve',
        'IP-CIDR,224.0.0.0/4,DIRECT,no-resolve',
        'IP-CIDR,255.255.255.255/32,DIRECT,no-resolve',
    ]
    # 2. 广告拦截
    rules_list += [f'DOMAIN-SUFFIX,{d},REJECT' for d in AD_DOMAINS]
    # 3. 拦截 QUIC(UDP 443),让谷歌/YouTube 流量稳定走代理
    rules_list.append('AND,((NETWORK,UDP),(DST-PORT,443)),REJECT')
    # 4. 常用国内域名直连(快速路径)
    rules_list += [f'DOMAIN-SUFFIX,{d},DIRECT' for d in CN_DOMAINS]
    # 5. GEOSITE 国内域名大库直连(数万条国内域名,覆盖面广)
    rules_list.append('GEOSITE,CN,DIRECT')
    # 6. 国内 IP 直连
    rules_list.append('GEOIP,CN,DIRECT')
    # 7. 其余(国外)全部走代理
    rules_list.append('MATCH,🚀 节点选择')

    # ===== 全局配置 + DNS(国内域名用国内 DNS,国外走 fallback) =====
    dns_config = {
        'enable': True,
        'listen': '0.0.0.0:1053',
        'ipv6': False,
        'enhanced-mode': 'fake-ip',
        'fake-ip-range': '198.18.0.1/16',
        'fake-ip-filter': [
            '+.lan', '+.local',
            '+.msftconnecttest.com', '+.msftncsi.com', 'dns.msftncsi.com',
            '+.stun.*.*', '+.stun.*.*.*',
            'time.*.com', 'time.*.gov', 'time.*.edu.cn', '+.time.edu.cn',
            '+.ntp.org', '+.pool.ntp.org', 'time1.cloud.tencent.com',
            '+.qq.com', '+.wechat.com', '+.weixin.qq.com',
            '+.market.xiaomi.com',
        ],
        'default-nameserver': ['223.5.5.5', '119.29.29.29'],
        'nameserver': ['https://223.5.5.5/dns-query', 'https://doh.pub/dns-query'],
        'fallback': ['https://dns.cloudflare.com/dns-query', 'https://dns.google/dns-query', 'tcp://1.1.1.1:53'],
        'fallback-filter': {
            'geoip': True,
            'geoip-code': 'CN',
            'ipcidr': ['240.0.0.0/4'],
        },
    }

    config = {
        'mixed-port': 7897,
        'allow-lan': False,
        'mode': 'rule',
        'log-level': 'info',
        'unified-delay': True,
        'tcp-concurrent': True,
        'global-client-fingerprint': 'chrome',
        'proxies': all_proxies,
        'proxy-groups': [
            {'name': '🚀 节点选择', 'type': 'select', 'proxies': ['♻️ 自动选择', 'EdgeGo节点', '公共节点', '🐢 延迟最低']},
            {'name': '♻️ 自动选择', 'type': 'url-test', 'proxies': [p['name'] for p in all_proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50},
            {'name': 'EdgeGo节点', 'type': 'select', 'proxies': gitlabip_names},
            {'name': '公共节点', 'type': 'select', 'proxies': public_names},
            {'name': '🐢 延迟最低', 'type': 'url-test', 'proxies': [p['name'] for p in all_proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50}
        ],
        'rules': rules_list,
        'dns': dns_config,
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
