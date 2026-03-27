import requests
import yaml
import base64
from datetime import datetime

BASE_URL = "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml"
GITEE_TOKEN = "1b3d7f9a6abdd26e15a44367f8695751"
GITEE_USER = "fwf1222"
GITEE_REPO = "clash-sub"

all_proxies = []
seen_names = set()
name_counter = {}

for i in range(1, 7):
    url = BASE_URL.format(i)
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = yaml.safe_load(resp.text)
            if data and 'proxies' in data:
                for proxy in data['proxies']:
                    name = proxy.get('name', f'node_{len(all_proxies)+1}')
                    final_name = name
                    if final_name in seen_names:
                        if name not in name_counter:
                            name_counter[name] = 1
                        name_counter[name] += 1
                        final_name = f'{name}_{name_counter[name]}'
                    proxy['name'] = final_name
                    seen_names.add(final_name)
                    all_proxies.append(proxy)
    except Exception as e:
        print(f'Error fetching {url}: {e}')

print(f'获取到 {len(all_proxies)} 个节点')

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
