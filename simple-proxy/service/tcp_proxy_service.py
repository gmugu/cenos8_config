#!/usr/bin/python

import os
import socket
import threading
import argparse
import time
from selectors import DefaultSelector, EVENT_READ

# Proxy开放的端口号
LOCAL_PORT = 7088
REMOTE_ADDR = "127.0.0.1"
REMOTE_PORT = 3128

MASK = 0x55

def xor_encode( bstring ):
    ret = bytearray( bstring )
    for i in range(len(ret)):
        ret[i] ^= MASK
    return ret


def proxy_process_encoded( sock1, sock2 ):
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
    print("new connected: %s %s:%s..." % (time.strftime("%Y/%m/%d-%H:%M:%S"), addr[0], addr[1]), flush=True)

    sock_remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_remote.settimeout(15)
    try:
        sock_remote.connect((REMOTE_ADDR, REMOTE_PORT))
    except Exception as e:
        print(e, flush=True)
        print( "Error when connect to", (REMOTE_ADDR, REMOTE_PORT), flush=True )
            
        sock_in.close()
        return

    proxy_process_encoded( sock_in, sock_remote )


def start_server():
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
    parse.add_argument('--port',type=int,default = LOCAL_PORT)
    parse.add_argument('--mask',type=int,default = MASK)
    
    args = parse.parse_args()
    if args.port < 1024 or args.port > 65534:
        quit(f'输入的port不合法,port = {args.port}')
    if args.mask <=0 or args.mask > 255:
        quit(f'输入的mask不合法, mask = {args.mask}')

    LOCAL_PORT = args.port
    MASK = args.mask
    print(f'proxy service param REMOTE_ADDR = {REMOTE_ADDR}, REMOTE_PORT = {REMOTE_PORT}, LOCAL_PORT = {LOCAL_PORT}, mask = {MASK}')

    os.system("iptables -A INPUT -p tcp --sport {} --tcp-flags RST RST -j DROP".format(LOCAL_PORT))
    start_server()