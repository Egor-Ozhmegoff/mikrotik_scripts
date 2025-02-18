import requests
import re
import netmiko
import os

from netmiko import ConnectHandler
from netaddr import IPNetwork, cidr_merge

url = 'https://reestr.rublacklist.net/api/v3/ips/'
regex = r'\d+\.\d+\.\d+\.'
mask_regex = r'\/2[5-9]|3[0-2]'
ip_list = requests.request(url=url, method='GET').json()

youtube_networks = [
    '8.8.4.0/24', '8.8.8.0/24', '8.34.208.0/20', '8.35.192.0/20', '23.236.48.0/20', '23.251.128.0/19', '34.0.0.0/15',
    '34.2.0.0/16', '34.3.0.0/23', '34.3.3.0/24', '34.3.4.0/24', '34.3.8.0/21', '34.3.16.0/20', '34.3.32.0/19',
    '34.3.64.0/18', '34.4.0.0/14', '34.8.0.0/13', '34.16.0.0/12', '34.32.0.0/11', '34.64.0.0/10', '34.128.0.0/10',
    '35.184.0.0/13', '35.192.0.0/14', '35.196.0.0/15', '35.198.0.0/16', '35.199.0.0/17', '35.199.128.0/18',
    '35.200.0.0/13', '35.208.0.0/12', '35.224.0.0/12', '35.240.0.0/13', '57.140.192.0/18', '64.15.112.0/20',
    '64.233.160.0/19', '66.22.228.0/23', '66.102.0.0/20', '66.249.64.0/19', '70.32.128.0/19', '72.14.192.0/18',
    '74.125.0.0/16', '104.154.0.0/15', '104.196.0.0/14', '104.237.160.0/19', '107.167.160.0/19', '107.178.192.0/18',
    '108.59.80.0/20', '108.170.192.0/18', '108.177.0.0/17', '130.211.0.0/16', '136.22.160.0/20', '136.22.176.0/21',
    '136.22.184.0/23', '136.22.186.0/24', '136.124.0.0/15', '142.250.0.0/15', '146.148.0.0/17', '152.65.208.0/22',
    '152.65.214.0/23', '152.65.218.0/23', '152.65.222.0/23', '152.65.224.0/19', '162.120.128.0/17', '162.216.148.0/22',
    '162.222.176.0/21', '172.110.32.0/21', '172.217.0.0/16', '172.253.0.0/16', '173.194.0.0/16', '173.255.112.0/20',
    '192.158.28.0/22', '192.178.0.0/15', '193.186.4.0/24', '199.36.154.0/23', '199.36.156.0/24', '199.192.112.0/22',
    '199.223.232.0/21', '207.223.160.0/20', '208.65.152.0/22', '208.68.108.0/22', '208.81.188.0/22', '208.117.224.0/19',
    '209.85.128.0/17', '216.58.192.0/19', '216.73.80.0/20', '216.239.32.0/19'
    ]

ipv4_list = []
commands = []

for ip in ip_list:
    match = re.match(regex, ip)
    if match:
        if '/' in ip:
            mask_match = re.match(mask_regex, ip)
            if mask_match:
                ipv4_list.append(IPNetwork(match.group() + '0/24'))
            else:
                ipv4_list.append(IPNetwork(ip))
        else:
            ipv4_list.append(IPNetwork(match.group() + '0/24'))

for yt_net in youtube_networks:
    ipv4_list.append(IPNetwork(yt_net))

ipv4_list = list(set(ipv4_list))
merged_list = cidr_merge(ipv4_list)

for net in merged_list:
    command = f'/ip/firewall/address-list/add address={str(net)} list=FUCK_RKN'
    commands.append(command)

mikrotik = {
    'device_type': 'mikrotik_routeros',
    'host': '192.168.88.1',
    'port': '22',
    'username': os.environ['USER'],
    'use_keys': True,
    'key_file': '~/.ssh/id_ed25519',
    'allow_agent': True,
}

ssh = ConnectHandler(**mikrotik)
result = ssh.send_config_set(commands)