import requests
import re
import os

from netmiko import ConnectHandler
from netaddr import IPNetwork, cidr_merge

def get_blocked_ips():
    url = 'https://reestr.rublacklist.net/api/v3/ips/'
    regex = r'\d+\.\d+\.\d+\.'
    mask_regex = r'\/2[5-9]|3[0-2]'
    data = requests.request(url=url, method='GET').content
    ip_list = [ net.replace('"', '').lstrip(' ') for net in str(data).split(',') ]
    ipv4_list = []
    blocked_ips = []

    with open ('youtube_networks.txt', 'r') as file:
        youtube_networks = [line.strip('\n') for line in file.readlines()]
    # youtube_networks = [
    #     '8.8.4.0/24', '8.8.8.0/24', '8.34.208.0/20', '8.35.192.0/20', '23.236.48.0/20', '23.251.128.0/19', '34.0.0.0/15',
    #     '34.2.0.0/16', '34.3.0.0/23', '34.3.3.0/24', '34.3.4.0/24', '34.3.8.0/21', '34.3.16.0/20', '34.3.32.0/19',
    #     '34.3.64.0/18', '34.4.0.0/14', '34.8.0.0/13', '34.16.0.0/12', '34.32.0.0/11', '34.64.0.0/10', '34.128.0.0/10',
    #     '35.184.0.0/13', '35.192.0.0/14', '35.196.0.0/15', '35.198.0.0/16', '35.199.0.0/17', '35.199.128.0/18',
    #     '35.200.0.0/13', '35.208.0.0/12', '35.224.0.0/12', '35.240.0.0/13', '57.140.192.0/18', '64.15.112.0/20',
    #     '64.233.160.0/19', '66.22.228.0/23', '66.102.0.0/20', '66.249.64.0/19', '70.32.128.0/19', '72.14.192.0/18',
    #     '74.125.0.0/16', '104.154.0.0/15', '104.196.0.0/14', '104.237.160.0/19', '107.167.160.0/19', '107.178.192.0/18',
    #     '108.59.80.0/20', '108.170.192.0/18', '108.177.0.0/17', '130.211.0.0/16', '136.22.160.0/20', '136.22.176.0/21',
    #     '136.22.184.0/23', '136.22.186.0/24', '136.124.0.0/15', '142.250.0.0/15', '146.148.0.0/17', '152.65.208.0/22',
    #     '152.65.214.0/23', '152.65.218.0/23', '152.65.222.0/23', '152.65.224.0/19', '162.120.128.0/17', '162.216.148.0/22',
    #     '162.222.176.0/21', '172.110.32.0/21', '172.217.0.0/16', '172.253.0.0/16', '173.194.0.0/16', '173.255.112.0/20',
    #     '192.158.28.0/22', '192.178.0.0/15', '193.186.4.0/24', '199.36.154.0/23', '199.36.156.0/24', '199.192.112.0/22',
    #     '199.223.232.0/21', '207.223.160.0/20', '208.65.152.0/22', '208.68.108.0/22', '208.81.188.0/22', '208.117.224.0/19',
    #     '209.85.128.0/17', '216.58.192.0/19', '216.73.80.0/20', '216.239.32.0/19'
    #     ]

    jetbrains_networks = ['3.160.212.0/24', '108.138.199.0/24', '108.157.188.0/24']
    instagram_networks = [
        '147.75.208.0/20', '185.89.216.0/22', '31.13.24.0/21', '31.13.64.0/19', '31.13.96.0/19', '45.64.40.0/22',
        '66.220.144.0/20', '69.63.176.0/20', '69.171.224.0/19', '74.119.76.0/22','102.132.96.0/20', '103.4.96.0/22',
        '129.134.0.0/16', '157.240.0.0/16', '173.252.64.0/18', '179.60.192.0/22', '185.60.216.0/22', '204.15.20.0/22',
        '163.70.151.0/24', '163.70.147.0/24'
        ]
    discord = ['34.0.0.0/15', '34.3.2.0/24','34.2.0.0/16','34.3.0.0/23', '35.192.0.0/12', '35.240.0.0/13',
               '35.224.0.0/12', '35.208.0.0/12', '5.200.14.128/25', '34.64.0.0/16', '66.22.192.0/18']
    services = youtube_networks + jetbrains_networks + instagram_networks + discord

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
    for service in services:
        ipv4_list.append(IPNetwork(service))
    ipv4_list = cidr_merge(list(set(ipv4_list)))
    for ip in ipv4_list:
        blocked_ips.append(str(ip))
    return blocked_ips

def ssh():
    mikrotik = {
        'device_type': 'mikrotik_routeros',
        'host': '192.168.88.1',
        'port': '22',
        'username': os.environ['USER'],
        'use_keys': True,
        'key_file': '~/.ssh/id_ed25519',
        'allow_agent': True,
    }
    return ConnectHandler(**mikrotik)

def get_ips_form_router(ssh):
    regex_net = r'\d+\.\d+\.\d+\.\d+\/\d+'
    mikrot_output = ssh.send_command("ip firewall address-list print without-paging", read_timeout=60).split('\n')
    current_addr_list = []
    for line in mikrot_output:
        net = re.search(regex_net, line)
        if net:
            current_addr_list.append(net.group())
    return current_addr_list

if __name__ == '__main__':
    ssh = ssh()
    blocked_ips = get_blocked_ips()
    mikrotik_ips = get_ips_form_router(ssh)
    diff_delete = list(set(mikrotik_ips) - set(blocked_ips))
    diff_add = list(set(blocked_ips) - set(mikrotik_ips))
    add_commands = []
    delete_commands = []
    for net in diff_add:
        command = f'/ip/firewall/address-list/add address={str(net)} list=FUCK_RKN'
        add_commands.append(command)
    for net in diff_delete:
        command = f'/ip firewall address-list remove [find where address={str(net)} list=FUCK_RKN]'
        delete_commands.append(command)

    if diff_add:
        print(f"Routes to add {diff_add} ")
    else:
        print('No routes to add')

    if diff_delete:
        print(f"Routes to delete {diff_delete} ")
    else:
        print('No routes to delete')

    while True:
        answer = input('Apply patch? (y/n) ').lower()
        if answer in ['y', 'n']:
            break
        print('Invalid input. Please try again...')

    if answer == 'y':
        if delete_commands:
            ssh.send_config_set(delete_commands)
        if add_commands:
            ssh.send_config_set(add_commands)
    else:
        exit(0)