#!/usr/bin/env python3

import os
import json
import socket
import threading
import argparse
import time
from selectors import DefaultSelector, EVENT_READ

# Proxy开放的端口号
LOCAL_PORT = 7088
# REMOTE_ADDR = "104.168.211.94"
REMOTE_ADDR = "hachinasp.duckdns.org"
REMOTE_PORT = 7088

MASK = 0x55

def xor_encode( bstring ):
    """一个简单编码：两次编码后与原值相同"""
    ret = bytearray( bstring )
    for i in range(len(ret)):
        ret[i] ^= MASK
    return ret


def proxy_process_encoded( sock1, sock2 ):
    """在两个sockek之间转发数据：任何一个收到的，编码后转发到另一个"""
    sel = DefaultSelector()
    sel.register(sock1, EVENT_READ)
    sel.register(sock2, EVENT_READ)

    while True:
        events = sel.select()
        for (key,ev) in events:
            try:
                data_in = key.fileobj.recv(8192)
            except ConnectionResetError as e:
                print(key.fileobj, "\nreset receive!")
                sock1.close()
                sock2.close()
                return
            if data_in:
                if key.fileobj==sock1:
                    sock2.send(xor_encode(data_in))
                else:
                    sock1.send(xor_encode(data_in))
            else:
                sock1.close()
                sock2.close()
                return

def tcp_proxy(sock_in, addr):
    """新的代理请求连接时，进行相关处理"""
    print("新的连接: %s:%s..." % addr, flush=True)

    # 建立远程连接
    sock_remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_remote.settimeout(15)
    try:
        sock_remote.connect((REMOTE_ADDR, REMOTE_PORT))
    except Exception as e:
        print(e, flush=True)
        print( "Error when connect to", (REMOTE_ADDR, REMOTE_PORT), flush=True )
            
        sock_in.close()
        return

    # 在本地连接与远程连接间转发数据
    proxy_process_encoded( sock_in, sock_remote )


def start_server():
    """主服务函数"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", LOCAL_PORT))
    s.listen()
    print("等待客户端连接...", flush=True)

    while True:
        sock, addr = s.accept()
        t = threading.Thread(target=tcp_proxy, args=(sock, addr))
        t.start()


if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument('--host',type=str,default = REMOTE_ADDR)
    parse.add_argument('--remote-port',type=int,default = REMOTE_PORT)
    parse.add_argument('--local-port',type=int,default = LOCAL_PORT)
    parse.add_argument('--mask',type=int,default = MASK)
    args = parse.parse_args()

    if args.remote_port < 1024 or args.remote_port > 65534:
        quit(f'输入的remote_port不合法,remote_port = {args.remote_port}')
    if args.local_port < 1024 or args.local_port > 65534:
        quit(f'输入的local_port不合法,local_port = {args.local_port}')
    if args.mask <=0 or args.mask > 255:
        quit(f'输入的mask不合法, mask = {args.mask}')

    REMOTE_ADDR = args.host
    REMOTE_PORT = args.remote_port
    LOCAL_PORT = args.local_port
    MASK = args.mask
    print(f'client param REMOTE_ADDR = {REMOTE_ADDR}, REMOTE_PORT = {REMOTE_PORT}, LOCAL_PORT = {LOCAL_PORT}, mask = {MASK}')

    os.system("iptables -A INPUT -p tcp --sport {} --tcp-flags RST RST -j DROP".format(REMOTE_PORT))
    start_server()