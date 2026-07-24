#!/bin/bash

# ==============================================================================
# JobHunter 服务启停管理脚本 (Shell Control Script)
# 支持命令: start | stop | restart | status
# ==============================================================================

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 运行依赖配置
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SERVER_SCRIPT="$PROJECT_DIR/src/server.py"
PID_FILE="$PROJECT_DIR/data/server.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
PORT=8000

# 确保必要的目录存在
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$LOG_DIR"

# 获取服务当前 PID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "$PID"
            return
        fi
    fi

    # 通过端口查询活动进程 PID (备用检查)
    PID_ON_PORT=$(lsof -t -i:$PORT 2>/dev/null)
    if [ -n "$PID_ON_PORT" ]; then
        echo "$PID_ON_PORT"
        return
    fi

    echo ""
}

# 1. 启动服务
start_service() {
    PID=$(get_pid)
    if [ -n "$PID" ]; then
        echo -e "\031[33m⚠️  JobHunter API 服务已经在运行中 (PID: $PID, 端口: $PORT)\033[0m"
        echo -e "👉 浏览器打开体验: \033[36mhttp://127.0.0.1:$PORT\033[0m"
        return 0
    fi

    if [ ! -f "$VENV_PYTHON" ]; then
        echo -e "\033[31m❌ 错误: 未找到虚拟环境 Python: $VENV_PYTHON\033[0m"
        echo "请先在项目根目录运行: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
        exit 1
    fi

    echo -e "🚀 正在启动 JobHunter API 服务 (端口: $PORT)..."
    PYTHONPATH="$PROJECT_DIR" nohup "$VENV_PYTHON" "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    
    # 写入 PID 文件
    echo "$NEW_PID" > "$PID_FILE"
    
    sleep 2

    if ps -p "$NEW_PID" > /dev/null 2>&1; then
        echo -e "\033[32m✅ 服务启动成功！(PID: $NEW_PID)\033[0m"
        echo -e "📄 运行日志路径: \033[34m$LOG_FILE\033[0m"
        echo -e "🌐 访问地址: \033[36mhttp://127.0.0.1:$PORT\033[0m"
    else
        echo -e "\033[31m❌ 启动失败，请查看日志: $LOG_FILE\033[0m"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 2. 停止服务
stop_service() {
    PID=$(get_pid)
    if [ -z "$PID" ]; then
        echo -e "\033[33m⚠️  JobHunter API 服务当前未在运行\033[0m"
        rm -f "$PID_FILE"
        return 0
    fi

    echo -e "🛑 正在停止 JobHunter API 服务 (PID: $PID)..."
    kill "$PID" 2>/dev/null

    # 循环等待进程退出
    for i in {1..5}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "\033[32m✅ 服务已安全停止！\033[0m"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # 强制杀死
    echo -e "\033[33m⚠️ 尝试强行终止进程 (kill -9)... \033[0m"
    kill -9 "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo -e "\033[32m✅ 服务已被强行终止！\033[0m"
}

# 3. 检查运行状态
status_service() {
    PID=$(get_pid)
    if [ -n "$PID" ]; then
        echo -e "\033[32m🟢 JobHunter API 服务正在运行 (PID: $PID, 监听端口: $PORT)\033[0m"
        echo -e "🌐 浏览器访问: \033[36mhttp://127.0.0.1:$PORT\033[0m"
    else
        echo -e "\033[31m🔴 JobHunter API 服务未运行\033[0m"
    fi
}

# 命令分流处理
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 1
        start_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "=================================================="
        echo " 🛠️  JobHunter 服务启停管理脚本"
        echo "=================================================="
        echo " 用法: $0 {start|stop|restart|status}"
        echo "   start   : 启动后台 HTTP API 服务"
        echo "   stop    : 停止后台 HTTP API 服务"
        echo "   restart : 重启 HTTP API 服务"
        echo "   status  : 查看服务当前运行状态"
        echo "=================================================="
        exit 1
        ;;
esac
