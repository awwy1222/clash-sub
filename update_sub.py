#!/usr/bin/env python3
import requests
import yaml
import base64
import os
from datetime import datetime

GITEE_TOKEN = "1b3d7f9a6abdd26e15a44367f8695751"
GITEE_USER = "fwf1222"
GITEE_REPO = "clash-sub"
BASE_URL = "https://www.gitlabip.xyz/Alvin9999/PAC/refs/heads/master/backup/img/1/2/ipp/clash.meta2/{}/config.yaml"

def fetch_nodes():
    all_proxies = []
    seen_names = set()
    name_counter = {}
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始获取节点...")
    
    for i in range(1, 7):
        url = BASE_URL.format(i)
        try:
            print(f"  获取第 {i} 个配置...")
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = yaml.safe_load(response.text)
                
                if data and 'proxies' in data and isinstance(data['proxies'], list):
                    for proxy in data['proxies']:
                        original_name = proxy.get('name', f"node_{len(all_proxies)+1}")
                        
                        final_name = original_name
                        if final_name in seen_names:
                            if original_name not in name_counter:
                                name_counter[original_name] = 1
                            name_counter[original_name] += 1
                            final_name = f"{original_name}_{name_counter[original_name]}"
                        
                        proxy['name'] = final_name
                        seen_names.add(final_name)
                        all_proxies.append(proxy)
                    
                    print(f"    -> 获取 {len([p for p in data['proxies']])} 个节点")
                    
        except Exception as e:
            print(f"    -> 失败: {str(e)}")
    
    return all_proxies

def create_config(proxies):
    config = {
        "proxies": proxies,
        "proxy-groups": [
            {
                "name": "🚀 节点选择",
                "type": "select",
                "proxies": [p['name'] for p in proxies]
            },
            {
                "name": "🐢 延迟最低",
                "type": "url-test",
                "proxies": [p['name'] for p in proxies],
                "url": "http://www.gstatic.com/generate_204",
                "interval": 300,
                "tolerance": 50
            }
        ],
        "rules": [
            "MATCH,🚀 节点选择"
        ]
    }
    return yaml.dump(config, allow_unicode=True, sort_keys=False)

def main():
    proxies = fetch_nodes()
    
    if not proxies:
        print("没有获取到任何节点!")
        return
    
    print(f"\n总共获取到 {len(proxies)} 个节点")
    
    # 创建 YAML 配置
    yaml_content = create_config(proxies)
    
    # Base64 订阅内容
    base64_content = base64.b64encode(yaml_content.encode()).decode()
    
    # 写入订阅文件
    sub_content = f"# Clash 订阅 - 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    sub_content += f"# 节点数: {len(proxies)}\n\n"
    sub_content += yaml_content
    
    with open('sub.yaml', 'w', encoding='utf-8') as f:
        f.write(sub_content)
    
    print(f"订阅文件已生成: sub.yaml")
    
    # 上传到 Gitee
    print("上传到 Gitee...")
    upload_to_gitee(sub_content)
    
    print("\n完成!")

def upload_to_gitee(content):
    import json
    
    # 读取现有文件 SHA
    get_url = f"https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml?access_token={GITEE_TOKEN}"
    get_resp = requests.get(get_url)
    sha = None
    if get_resp.status_code == 200:
        data = get_resp.json()
        if isinstance(data, dict):
            sha = data.get('sha')
        elif isinstance(data, list) and len(data) > 0:
            sha = data[0].get('sha')
    
    # 上传/更新文件
    put_url = f"https://gitee.com/api/v5/repos/{GITEE_USER}/{GITEE_REPO}/contents/sub.yaml"
    data = {
        "access_token": GITEE_TOKEN,
        "content": base64.b64encode(content.encode()).decode(),
        "message": f"自动更新订阅 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    }
    if sha:
        data["sha"] = sha
    
    resp = requests.post(put_url, json=data)
    print(f"  -> Gitee API 响应: {resp.status_code}")
    if resp.status_code == 201:
        print("  -> Gitee 更新成功!")
    else:
        print(f"  -> Gitee 更新失败: {resp.text}")

if __name__ == "__main__":
    main()
