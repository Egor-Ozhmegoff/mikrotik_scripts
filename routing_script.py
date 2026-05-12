import requests
import re
import os
import sys

from netmiko import ConnectHandler
from netaddr import IPNetwork, cidr_merge

def download_file(url, output_filename="youtube_networks"):
    try:
        # Выполняем GET-запрос с потоковой загрузкой
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Проверяем статус код (если не 200, выбросит исключение)

        # Открываем файл в бинарном режиме для записи
        with open(output_filename, 'wb') as file:
            # Записываем содержимое порциями для экономии памяти
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

        print(f"Файл успешно сохранён как {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании файла: {e}")
        sys.exit(1)
    except IOError as e:
        print(f"Ошибка при записи файла: {e}")
        sys.exit(1)

def get_blocked_ips():
    blocked_ips = []
    ipv4_list = []
    blocked_files = [i for i in next(os.walk('./networks'))[2]]
    for blocked_file in blocked_files:
        with open (f'networks/{blocked_file}', 'r') as file:
            for line in file.readlines():
                if '/' in line:
                    ipv4_list.append(IPNetwork(line.strip('\n')))
                else:
                    ipv4_list.append(IPNetwork(line.strip('\n').replace(' ', '') + '/32'))
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
    download_file('https://raw.githubusercontent.com/touhidurrr/iplist-youtube/refs/heads/main/lists/cidr4.txt', 'networks/youtube.txt')
    download_file('https://raw.githubusercontent.com/FabrizioCafolla/openai-crawlers-ip-ranges/refs/heads/main/openai/openai-cidr-ranges-all.txt', 'chat_gpt.txt')
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
            deleted = ssh.send_config_set(delete_commands)
        if add_commands:
            added = ssh.send_config_set(add_commands)
    else:
        exit(0)