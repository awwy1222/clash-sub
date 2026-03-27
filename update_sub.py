import requests
import yaml
import base64
from datetime import datetime

GITEE_TOKEN = "1b3d7f9a6abdd26e15a44367f8695751"
GITEE_USER = "fwf1222"
GITEE_REPO = "clash-sub"

# Clash 兼容的来源
CLASH_SOURCES = {
    'clash_1': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml',
    'clash_2': 'https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml',
}

# 公共订阅源（可能有免费节点）
PUBLIC_SUBS = [
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.yml',
    'https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/clash.yml',
    'https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/clash.yml',
]

all_proxies = []
seen_names = set()
name_counter = {}

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取节点...")

# 获取 Clash 节点
for name, template in CLASH_SOURCES.items():
    max_page = 6 if 'clash' in name else 6
    for i in range(1, max_page + 1):
        url = template.format(i)
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
                    print(f"  {name}/{i}: {len(data['proxies'])} 个节点")
        except Exception as e:
            pass

# 尝试公共订阅
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
                print(f"  公共订阅: {len(data['proxies'])} 个节点")
    except:
        pass

print(f"\n总计获取 {len(all_proxies)} 个节点")

config = {
    'proxies': all_proxies,
    'proxy-groups': [
        {'name': '🚀 节点选择', 'type': 'select', 'proxies': [p['name'] for p in all_proxies]},
        {'name': '🐢 延迟最低', 'type': 'url-test', 'proxies': [p['name'] for p in all_proxies], 'url': 'http://www.gstatic.com/generate_204', 'interval': 300, 'tolerance': 50}
    ],
    'rules': ['MATCH,🚀 节点选择']
}

yaml_content = yaml.dump(config, allow_unicode=True, sort_keys=False)
sub_content = f'# Clash 订阅 - 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n# 节点数: {len(all_proxies)}\n\n' + yaml_content

# 获取文件SHA
get_resp = requests.get(f'https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml?access_token={GITEE_TOKEN}')
sha = None
if get_resp.status_code == 200:
    data = get_resp.json()
    if isinstance(data, dict):
        sha = data.get('sha')
    elif isinstance(data, list) and len(data) > 0:
        sha = data[0].get('sha')

# 上传
put_data = {
    'access_token': GITEE_TOKEN,
    'content': base64.b64encode(sub_content.encode()).decode(),
    'message': f'自动更新订阅 - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
}
if sha:
    put_data['sha'] = sha

put_resp = requests.post(f'https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml', json=put_data)
print(f'上传状态: {put_resp.status_code}')
