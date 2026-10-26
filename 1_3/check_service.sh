#!/bin/bash
# 接受一个端口号作为参数：
  #
  #用 lsof -i : 端口号 检查该端口是否有进程在监听
  #如果有 → 打印 “服务运行中，PID: xxx”
  #如果没有 → 打印 “端口未使用”
  #如果端口不存在 → 打印错误信息
function check_service() {
  if [ $# -eq 1 ]; then
    if [[ $1 =~ ^[0-9]+$ ]]; then
      if lsof -i :$1 > /dev/null; then
        echo "服务运行中，PID: $(lsof -i :$1 | awk 'NR==2 {print $2}')"
      else
        echo "端口未使用"
      fi
    else
      echo "错误：端口号必须是数字"
    fi
  else
    echo "错误：请提供一个端口号作为参数"
  fi
}

check_service $1
