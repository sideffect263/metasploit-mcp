#!/bin/bash

# Metasploit MCP Server Management Script
# Usage: ./manage.sh {start|stop|restart|status|logs|update}

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="metasploit-mcp"
NGINX_SERVICE="nginx"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

show_status() {
    print_status "Checking service status..."
    echo
    
    # Check MCP server
    echo "🔧 Metasploit MCP Server:"
    if systemctl is-active --quiet $SERVICE_NAME; then
        print_success "Running"
    else
        print_error "Not running"
    fi
    
    # Check nginx
    echo "🌐 Nginx Web Server:"
    if systemctl is-active --quiet $NGINX_SERVICE; then
        print_success "Running"
    else
        print_error "Not running"
    fi
    
    # Check MSF RPC
    echo "🛡️ Metasploit RPC:"
    if pgrep -f msfrpcd > /dev/null; then
        print_success "Running"
    else
        print_error "Not running"
    fi
    
    # Show listening ports
    echo
    print_status "Listening ports:"
    ss -tulpn | grep -E ':80|:443|:55553' || echo "No services listening on expected ports"
    
    # Show disk usage
    echo
    print_status "Disk usage:"
    df -h / | grep -v Filesystem
    
    # Show memory usage
    echo
    print_status "Memory usage:"
    free -h | grep -E 'Mem:|Swap:'
}

start_services() {
    print_status "Starting services..."
    
    # Start MSF RPC if not running
    if ! pgrep -f msfrpcd > /dev/null; then
        print_status "Starting Metasploit RPC..."
        cd /opt/metasploit-mcp
        bash start_msfrpcd.sh &
        sleep 3
    fi
    
    # Start MCP server
    systemctl start $SERVICE_NAME
    print_success "MCP server started"
    
    # Start nginx
    systemctl start $NGINX_SERVICE
    print_success "Nginx started"
    
    show_status
}

stop_services() {
    print_status "Stopping services..."
    
    # Stop MCP server
    systemctl stop $SERVICE_NAME
    print_success "MCP server stopped"
    
    # Stop nginx (optional)
    read -p "Stop nginx web server too? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        systemctl stop $NGINX_SERVICE
        print_success "Nginx stopped"
    fi
    
    # Stop MSF RPC
    if pgrep -f msfrpcd > /dev/null; then
        print_status "Stopping Metasploit RPC..."
        pkill -f msfrpcd
        print_success "MSF RPC stopped"
    fi
}

restart_services() {
    print_status "Restarting services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    echo "Select logs to view:"
    echo "1) MCP Server logs"
    echo "2) Nginx access logs"
    echo "3) Nginx error logs"
    echo "4) System logs"
    echo "5) All logs (tail -f)"
    
    read -p "Enter choice (1-5): " choice
    
    case $choice in
        1)
            print_status "Showing MCP server logs..."
            journalctl -u $SERVICE_NAME -f
            ;;
        2)
            print_status "Showing Nginx access logs..."
            tail -f /var/log/nginx/access.log
            ;;
        3)
            print_status "Showing Nginx error logs..."
            tail -f /var/log/nginx/error.log
            ;;
        4)
            print_status "Showing system logs..."
            journalctl -f
            ;;
        5)
            print_status "Showing all logs..."
            multitail /var/log/nginx/access.log /var/log/nginx/error.log <(journalctl -u $SERVICE_NAME -f)
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
}

update_deployment() {
    print_status "Updating deployment..."
    
    # Backup current config
    cp /etc/nginx/sites-available/metasploit-mcp /etc/nginx/sites-available/metasploit-mcp.backup.$(date +%Y%m%d_%H%M%S)
    
    # Copy new files
    cp nginx.conf /etc/nginx/sites-available/metasploit-mcp
    cp metasploit-mcp.service /etc/systemd/system/
    cp index.html /var/www/metasploit-mcp/
    cp metasploit_mcp_server.py /opt/metasploit-mcp/
    
    # Reload systemd and restart services
    systemctl daemon-reload
    nginx -t && systemctl reload nginx
    systemctl restart $SERVICE_NAME
    
    print_success "Deployment updated successfully"
}

show_usage() {
    echo "Metasploit MCP Server Management Script"
    echo
    echo "Usage: $0 {start|stop|restart|status|logs|update|help}"
    echo
    echo "Commands:"
    echo "  start    - Start all services"
    echo "  stop     - Stop all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show service status and system info"
    echo "  logs     - View service logs"
    echo "  update   - Update deployment files"
    echo "  help     - Show this help message"
    echo
}

# Main script
case "${1:-}" in
    start)
        check_root
        start_services
        ;;
    stop)
        check_root
        stop_services
        ;;
    restart)
        check_root
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    update)
        check_root
        update_deployment
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Invalid command: ${1:-}"
        echo
        show_usage
        exit 1
        ;;
esac 