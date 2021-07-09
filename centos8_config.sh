#!/usr/bin/env bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

sh_ver="0.0.1"

Green_font_prefix="\033[32m" && Red_font_prefix="\033[31m" && Green_background_prefix="\033[42;37m" && Red_background_prefix="\033[41;37m" && Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[信息]${Font_color_suffix}"
Error="${Red_font_prefix}[错误]${Font_color_suffix}"
Tip="${Green_font_prefix}[注意]${Font_color_suffix}"

check_bbr_status(){
    kernel_version=`uname -r | awk -F "-" '{print $1}'`
	if [[ `echo ${kernel_version} | awk -F'.' '{print $1}'` == "4" ]] && [[ `echo ${kernel_version} | awk -F'.' '{print $2}'` -ge 9 ]] || [[ `echo ${kernel_version} | awk -F'.' '{print $1}'` == "5" ]]; then
		kernel_status="BBR"
    else
        kernel_status="noinstall"
    fi

    if [[ ${kernel_status} == "BBR" ]]; then
		run_status=`grep "net.ipv4.tcp_congestion_control" /etc/sysctl.conf | awk -F "=" '{print $2}'`
		if [[ ${run_status} == "bbr" ]]; then
			run_status=`lsmod | grep "bbr" | awk '{print $1}'`
			if [[ ${run_status} == "tcp_bbr" ]]; then
				run_status="BBR启动成功"
			else 
				run_status="BBR启动失败"
			fi
        fi
    fi

    
}

echo_bbr_status(){
    check_bbr_status
    if [[ ${kernel_status} == "noinstall" ]]; then
        echo -e " 当前状态: ${Green_font_prefix}未安装${Font_color_suffix} 加速内核 ${Red_font_prefix}请先安装内核${Font_color_suffix}"
    else
        echo -e " 当前状态: ${Green_font_prefix}已安装${Font_color_suffix} ${_font_prefix}${kernel_status}${Font_color_suffix} 加速内核 , ${Green_font_prefix}${run_status}${Font_color_suffix}"
    fi
}

#启用BBR
startbbr(){
    check_bbr_status

    if [[ ${kernel_status} == "noinstall" ]]; then
        echo -e "${Error},当前操作系统 ${Green_font_prefix}未安装${Font_color_suffix} 加速内核"
    else
        sed -i '/net.core.default_qdisc/d' /etc/sysctl.conf
        sed -i '/net.ipv4.tcp_congestion_control/d' /etc/sysctl.conf
        sleep 1s
        echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
        echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
        sysctl -p
        echo -e "${Info}BBR启动成功！"
    fi
}

install_run_test_squid(){
    echo -e "${Info}开始安装代理！"
    yum install -y squid*
    echo -e "${Info}安装代理成功！"
    squid
    echo -e "${Info}启动代理，在本地端口3128"

    echo -e "${Info}测试代理！"
    curl -x 127.0.0.1:3128 google.com

}

run_simpleproxy(){
    read -p " 请输入port:" port
    read -p " 请输入mask:" mask

    chmod a+x ./service/tcp_proxy_service.py --port=$port --mask=$mask
    # nohup ./service/tcp_proxy_service.py > /dev/null 2>&1 &                      #什么日志都不记录
    # nohup ./service/tcp_proxy_service.py > /dev/null 2>tcp_proxy_service.error & #只记录错误日志
    nohup ./service/tcp_proxy_service.py > tcp_proxy_service.log 2>&1 &          #记录所有日志
    echo -e "${Info}开启simple_proxy成功！"
}

test_net_speed(){
    wget http://cachefly.cachefly.net/100mb.test
}

test_squid_speed(){
    echo -e "${Info}测试代理网速！"
    wget http://cachefly.cachefly.net/100mb.test -e http_proxy=127.0.0.1:3128
}

test_simple_http_speed(){
    wget http://cachefly.cachefly.net/100mb.test
}


#开始菜单
start_menu(){
    echo && echo -e "一键安装管理脚本 ${Red_font_prefix}[v${sh_ver}]${Font_color_suffix}
    
    ${Green_font_prefix}0.${Font_color_suffix} 检查BBR加速状态
    ${Green_font_prefix}1.${Font_color_suffix} 使用BBR加速
    ${Green_font_prefix}2.${Font_color_suffix} 安装运行squid
    ${Green_font_prefix}3.${Font_color_suffix} 安装运行simple_proxy
    ${Green_font_prefix}4.${Font_color_suffix} 测试网络下行速度
    ${Green_font_prefix}5.${Font_color_suffix} 测试squid网络下行速度
    ${Green_font_prefix}6.${Font_color_suffix} 测试simple_proxy网络下行速度

    ${Green_font_prefix}11.${Font_color_suffix} 退出脚本
    ————————————————————————————————" && echo

    echo
    read -p " 请输入数字 [0-11]:" num
    case "$num" in
        0)
        echo_bbr_status
        ;;
        1)
        startbbrmod
        ;;
        2)
        install_run_test_squid
        ;;
        3)
        run_simpleproxy
        ;;
        4)
        test_net_speed
        ;;
        5)
        test_squid_speed
        ;;
        6)
        test_simple_http_speed
        ;;
        
        11)
        exit 1
        ;;
        *)
        clear
        echo -e "${Error}:请输入正确数字 [0-11]"
        sleep 5s
        clear
        start_menu
        ;;
    esac
    start_menu
}
clear
start_menu
