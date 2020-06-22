import os, cgi
import sys
import subprocess
import random

import schedule  # pip install schedule
import time

from threading import Thread

import ipaddress

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

subnet_netmasks_ = ['000.000.000.000',
                    '128.000.000.000',
                    '192.000.000.000',
                    '224.000.000.000',
                    '240.000.000.000',
                    '248.000.000.000',
                    '252.000.000.000',
                    '254.000.000.000',
                    '255.000.000.000',
                    '255.128.000.000',
                    '255.192.000.000',
                    '255.224.000.000',
                    '255.240.000.000',
                    '255.248.000.000',
                    '255.252.000.000',
                    '255.254.000.000',
                    '255.255.000.000',
                    '255.255.128.000',
                    '255.255.192.000',
                    '255.255.224.000',
                    '255.255.240.000',
                    '255.255.248.000',
                    '255.255.252.000',
                    '255.255.254.000',
                    '255.255.255.000',
                    '255.255.255.128',
                    '255.255.255.192',
                    '255.255.255.224',
                    '255.255.255.240',
                    '255.255.255.248',
                    '255.255.255.252',
                    '255.255.255.254',
                    '255.255.255.255']
subnet_netmasks_ranges = [8, 28]
ip_range_lr = [ipaddress.ip_address('192.168.12.1'), ipaddress.ip_address('192.168.12.230')]

# текущее состояние сети
NetMask_global = 24
users_mac_addr = ['78:7E:61:9B:C3:19',
                  '72:4F:56:9B:C3:19',
                  '6C:FA:A7:8E:A7:38',
                  '72:4F:56:97:65:A7',
                  '72:4F:56:84:E0:E1',
                  '70:5A:0F:E3:06:85',
                  '94:65:2D:84:E0:E1',
                  '4C:D1:A1:52:40:1B',
                  '72:4F:56:46:18:7D',
                  '72:4F:56:52:40:1B',
                  '44:8A:5B:A4:85:DB',
                  '72:4F:56:BD:49:87',
                  '72:4F:56:CC:B9:1C',
                  '80:35:C1:46:18:7D']


def create_config(path):
    """
    Create a config file
    """
    config = configparser.ConfigParser()

    config.add_section("RANGE_SET")
    config.set("RANGE_SET", "HDCPRange", "192.168.12.1-192.168.12.230")

    config.add_section("GLOBAL_OPTIONS")
    config.set("GLOBAL_OPTIONS", "SubNetMask", "255.255.255.0")
    config.set("GLOBAL_OPTIONS", "DomainServer", "192.168.1.1, 192.168.1.2")
    config.set("GLOBAL_OPTIONS", "AddressTime", "36000")

    config.add_section("HTTP_INTERFACE")
    config.set("HTTP_INTERFACE", "HTTPServer", "127.0.0.1:6789")

    with open(path, "w") as config_file:
        config.write(config_file)


def get_config(path):
    """
    Returns the config object
    """
    if not os.path.exists(path):
        create_config(path)

    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_setting(path, section, setting):
    """
    Print out a setting
    """
    config = get_config(path)
    value = config.get(section, setting)
    """
    msg = "{section} {setting} is {value}".format(
        section=section, setting=setting, value=value
    )
    print(msg)
    """
    return value


def update_setting(path, section, setting, value):
    """
    Update a setting
    """
    config = get_config(path)
    config.set(section, setting, value)
    with open(path, "w") as config_file:
        config.write(config_file)


def delete_setting(path, section, setting):
    """
    Delete a setting
    """
    config = get_config(path)
    config.remove_option(section, setting)
    with open(path, "w") as config_file:
        config.write(config_file)


def what_main_configs(path):
    HDCPRange = get_setting(path, 'RANGE_SET', 'HDCPRange')

    SubNetMask = get_setting(path, 'GLOBAL_OPTIONS', 'SubNetMask')
    DomainServer = get_setting(path, 'GLOBAL_OPTIONS', 'DomainServer')
    AddressTime = get_setting(path, 'GLOBAL_OPTIONS', 'AddressTime')

    HTTPServer = get_setting(path, 'HTTP_INTERFACE', 'HTTPServer')

    print(HDCPRange)

    print(SubNetMask)
    print(DomainServer)
    print(AddressTime)

    print(HTTPServer)


# меняем настройки для всех пользователей на одну
def change_setting_in_ini_to_all_users(path, setting, new_value, users_mac_addr):
    if users_mac_addr:
        for elem in users_mac_addr:
            update_setting(path, elem, setting, new_value)


# меняем маску подсети
def change_netmask_global(path, new_value):
    update_setting(path, "GLOBAL_OPTIONS", "SubNetMask", subnet_netmasks_[new_value])


# меняем маску подсети для пользоватлей в зависимости от выбора:
# mode_mask = random - раздаем случайные IP
# mode_mask = linear - раздаем IP по порядку
# mode_mask = function - раздача по своей функции
def change_netmask_for_users(path, mode_mask, NetMask_global, func):
    if mode_mask == "random":  # раздаем NetMask в случайном порядке
        NetMask_global = random.randrange(subnet_netmasks_ranges[0], subnet_netmasks_ranges[1], 5)
        change_netmask_global(path, NetMask_global)

    if mode_mask == "linear":  # Раздаем IP последовательно
        if NetMask_global + 1 > subnet_netmasks_ranges[1]:
            if subnet_netmasks_ranges[0] >= 0:
                NetMask_global = subnet_netmasks_ranges[0]
        else:
            NetMask_global = NetMask_global + 1

        change_netmask_global(path, NetMask_global)

    if mode_mask == "function":

        if '+' in func:
            delta = int(func.rpartition('+')[1])

        if NetMask_global + delta > subnet_netmasks_ranges[1]:  # постчет маски по заданной функции
            if (delta + NetMask_global - subnet_netmasks_ranges[1]) % (
                    subnet_netmasks_ranges[1] - subnet_netmasks_ranges[0] + 1) == 0:
                NetMask_global = subnet_netmasks_ranges[1]
            else:
                NetMask_global = subnet_netmasks_ranges[0] - 1 + (
                        delta + NetMask_global - subnet_netmasks_ranges[1]) % (
                                         subnet_netmasks_ranges[1] - subnet_netmasks_ranges[0] + 1)
        else:
            NetMask_global = NetMask_global + delta

        change_netmask_global(path, NetMask_global)


# выдаем лист доступных IP для данного диапазона
def list_of_available_ip_to_this_range(ip_range_lr, NetMask_global):
    list_of_all_available_ip_to_this_mask = list(ipaddress.ip_network(
        str(ip_range_lr[0]).rpartition('.')[0] + ".0/" + str(
            NetMask_global)).hosts())  # получаем все доступные хостя для данной подсети
    list_of_available_ip = []  # список доступных IP для нашего диапазона

    ip_iter = ip_range_lr[0]

    while ip_iter <= ip_range_lr[1]:
        if ip_iter in list_of_all_available_ip_to_this_mask:  # проверка на вхождение элемента в доступынй диапазон
            list_of_available_ip.append(ip_iter)
        ip_iter = ip_iter + 1

    return list_of_available_ip


# меняем IP пользователей в зависимости от выбора:
# mode_ip = random - раздаем случайные IP
# mode_ip = linear - раздаем IP по порядку
# mode_ip = function - раздача по своей функции
def change_users_ip(path, mode_ip, users_mac_addr, ip_range_lr, func):
    list_of_available_ip_ = list_of_available_ip_to_this_range(ip_range_lr, NetMask_global)

    if len(users_mac_addr) <= len(list_of_available_ip_):  # если пользователей больше чем доступных адресов

        if mode_ip == "random":  # раздаем ip в случайном порядке
            for elem in users_mac_addr:
                temp_ip = random.choice(list_of_available_ip_)
                list_of_available_ip_.remove(temp_ip)
                update_setting(path, elem, "IP", str(temp_ip))

        if mode_ip == "linear":  # Раздаем IP последовательно
            max_ip_addr_of_user = list_of_available_ip_[0]  # адрес начала раздачи IP

            for elem in users_mac_addr:
                if (elem > max_ip_addr_of_user and elem <= list_of_available_ip_[
                    -1]):  # поиск самого большого текущего IP
                    max_ip_addr_of_user = elem

            iter_of_ip = max_ip_addr_of_user

            for numb_user in range(len(users_mac_addr)):

                iter_of_ip = iter_of_ip + 1
                if (iter_of_ip > list_of_available_ip_[-1]):
                    iter_of_ip = list_of_available_ip_[0]

                update_setting(path, numb_user, "IP", str(iter_of_ip))

        if mode_ip == "function":

            temp_list_of_available_ip_ = list_of_available_ip_

            max_ip_addr_of_user = temp_list_of_available_ip_[0]  # адрес начала раздачи IP

            for elem in users_mac_addr:
                if (elem > max_ip_addr_of_user and elem <= temp_list_of_available_ip_[
                    -1]):  # поиск самого большого текущего IP
                    max_ip_addr_of_user = elem

            iter_of_ip = max_ip_addr_of_user

            if '+' in func:
                delta = int(func.rpartition('+')[1])

            if delta:
                for numb_user in range(len(users_mac_addr)):  # распределяем IP по функции
                    if (delta > len(temp_list_of_available_ip_) and delta > 1):
                        delta = delta // 2

                    if (iter_of_ip + delta > temp_list_of_available_ip_[1]):
                        iter_of_ip = temp_list_of_available_ip_[0]
                    else:
                        iter_of_ip = iter_of_ip + int(delta)

                update_setting(path, numb_user, "IP", str(iter_of_ip))
                temp_list_of_available_ip_.remove(iter_of_ip)


###нужно создать функцию обновления параметров IP и маски сети, которая перед изменениями завершает работу сервера, а после запускает
def change_users_ip_and_mask(path, mode_ip, mode_mask, users_mac_addr, ip_range_lr, NetMask_global, func_ip, funk_mask):
    ### выключаем DHCP сервер
    change_netmask_for_users(path, mode_mask, NetMask_global, funk_mask)
    change_users_ip(path, mode_ip, users_mac_addr, ip_range_lr, func_ip)
    # включаем DHCP сервер


###функция мониторинга злоумышленника, при обнаружении - таймер меняется на 1 минуту

# запускаем изменения
def trigger(path, mode_trigger, mode_ip, mode_mask, users_mac_addr, ip_range_lr, minutes_or_days, time_, func_ip,
            funk_mask):
    if mode_trigger == "auto":
        # выставляем рассписание на изменение IP и маски пользователей
        if minutes_or_days == "minutes":
            schedule.every(time_).minutes.do(
                change_users_ip_and_mask(path, mode_ip, mode_mask, users_mac_addr, ip_range_lr, NetMask_global, func_ip,
                                         funk_mask))  # ставим изменение раз в time_ минут
        if minutes_or_days == "days":
            schedule.every(time_).minutes.do(
                change_users_ip_and_mask(path, mode_ip, mode_mask, users_mac_addr, ip_range_lr, NetMask_global, func_ip,
                                         funk_mask))  # ставим изменение раз в time_ дней

    if mode_trigger == "manually":
        change_users_ip_and_mask(path, mode_ip, mode_mask, users_mac_addr, ip_range_lr, NetMask_global, func_ip,
                                 funk_mask)

    if mode_trigger == "hacking":
        schedule.every(2).minutes.do(
            change_users_ip_and_mask(path, mode_ip, mode_mask, users_mac_addr, ip_range_lr, NetMask_global, func_ip,
                                     funk_mask))


if __name__ == "__main__":
    path = "settings.ini"
    what_main_configs(path)

    # users_mac_addr = ['1230', '123']
