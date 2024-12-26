import requests
import re
import netmiko
from netmiko import ConnectHandler
import os

url = 'https://reestr.rublacklist.net/api/v3/ips/'
regex = r'\d+\.\d+\.\d+\.'
ip_list = requests.request(url=url, method='GET').json()

commands = []
for ip in ip_list:
    match = re.match(regex, ip)
    if match:
        ipv4_net = match.group() + '0/24'
        command = f'/ip/firewall/address-list/add address={ipv4_net} list=FUCK_RKN'
        commands.append(command)

commands = list(set(commands))

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