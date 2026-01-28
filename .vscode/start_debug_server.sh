#!/bin/bash

PYTHON_PATH="$1"
SCRIPT_PATH="$2"
PORT=5678

find_graphical_session() {
    for display_num in 0 1 2; do
        if [ -S "/tmp/.X11-unix/X${display_num}" ]; then
            XUSER=$(who | grep "(:${display_num})" | awk '{print $1}' | head -n 1)
            
            if [ -n "$XUSER" ]; then
                SESSION_TYPE="x11"
                DISPLAY=":${display_num}"
                USER_UID=$(id -u "$XUSER")
                XAUTHORITY="/home/$XUSER/.Xauthority"
                XDG_CURRENT_DESKTOP=$(sudo -u "$XUSER" bash -c 'echo $XDG_CURRENT_DESKTOP')
                echo "Found X11 session: DISPLAY=$DISPLAY, USER=$XUSER"
                return 0
            fi
        fi
    done
    
    # Try Wayland
    for runtime_dir in /run/user/*; do
        if [ -S "$runtime_dir/wayland-0" ]; then
            UID_NUM=$(basename "$runtime_dir")
            XUSER=$(id -un "$UID_NUM" 2>/dev/null)
            
            if [ -n "$XUSER" ]; then
                SESSION_TYPE="wayland"
                USER_UID="$UID_NUM"
                
                # Get XDG_CURRENT_DESKTOP from the user's graphical session processes
                XDG_CURRENT_DESKTOP=$(grep -z '^XDG_CURRENT_DESKTOP=' /proc/$(pgrep -u "$XUSER" gnome-shell | head -n 1)/environ 2>/dev/null | cut -d= -f2 | tr -d '\0')
                
                # Fallback: try other common desktop processes
                if [ -z "$XDG_CURRENT_DESKTOP" ]; then
                    for process in kwin_wayland plasmashell mutter sway; do
                        PID=$(pgrep -u "$XUSER" "$process" | head -n 1)
                        if [ -n "$PID" ]; then
                            XDG_CURRENT_DESKTOP=$(grep -z '^XDG_CURRENT_DESKTOP=' /proc/$PID/environ 2>/dev/null | cut -d= -f2 | tr -d '\0')
                            [ -n "$XDG_CURRENT_DESKTOP" ] && break
                        fi
                    done
                fi
                
                # Another fallback: check systemd user environment
                if [ -z "$XDG_CURRENT_DESKTOP" ]; then
                    XDG_CURRENT_DESKTOP=$(systemctl --user -M "$XUSER@" show-environment 2>/dev/null | grep '^XDG_CURRENT_DESKTOP=' | cut -d= -f2)
                fi
                
                # Find the actual XWayland display for this user
                DISPLAY=$(ps aux | grep -E "Xwayland.*:([0-9]+)" | grep "$XUSER" | grep -oP ":\d+" | head -n 1)
                
                # Fallback: check /tmp/.X11-unix sockets owned by this user
                if [ -z "$DISPLAY" ]; then
                    for display_num in 0 1 2; do
                        if [ -S "/tmp/.X11-unix/X${display_num}" ]; then
                            SOCKET_OWNER=$(stat -c '%U' "/tmp/.X11-unix/X${display_num}" 2>/dev/null)
                            if [ "$SOCKET_OWNER" = "$XUSER" ]; then
                                DISPLAY=":${display_num}"
                                break
                            fi
                        fi
                    done
                fi
                
                # Last fallback
                if [ -z "$DISPLAY" ]; then
                    DISPLAY=":0"
                fi
                
                XAUTHORITY=$(find "$runtime_dir" -name ".mutter-Xwaylandauth*" 2>/dev/null | head -n 1)
                echo "Found Wayland session: USER=$XUSER, DISPLAY=$DISPLAY"
                return 0
            fi
        fi
    done
    
    return 1
}

# Kill any existing debug server
pkill -f "debugpy.*--listen.*:$PORT" 2>/dev/null
sleep 1

if ! find_graphical_session; then
    echo "ERROR: No graphical session found"
    exit 1
fi

echo "Starting debug server on port $PORT"
echo "Python: $PYTHON_PATH"
echo "Script: $SCRIPT_PATH"
echo "Session type: $SESSION_TYPE"
echo "DISPLAY=$DISPLAY"
echo "XAUTHORITY=$XAUTHORITY"
echo "XDG_CURRENT_DESKTOP=$XDG_CURRENT_DESKTOP"

export XDG_CURRENT_DESKTOP="$XDG_CURRENT_DESKTOP"
export DISPLAY="$DISPLAY"
export XAUTHORITY="$XAUTHORITY"

cd "$(dirname "$SCRIPT_PATH")"

nohup "$PYTHON_PATH" -m debugpy --listen 0.0.0.0:$PORT --wait-for-client "$SCRIPT_PATH" > /tmp/debugpy.log 2>&1 &
DEBUG_PID=$!

echo "Debug server PID: $DEBUG_PID"

SERVER_READY=false
for i in {1..20}; do
    if netstat -tuln 2>/dev/null | grep -q ":$PORT " || ss -tuln 2>/dev/null | grep -q ":$PORT "; then
        echo "Debug server is listening on port $PORT"
        SERVER_READY=true
        break
    fi
    
    if ! kill -0 $DEBUG_PID 2>/dev/null; then
        echo "ERROR: Debug server process died"
        if [ -f /tmp/debugpy.log ]; then
            echo "=== Debug log ==="
            cat /tmp/debugpy.log
        fi
        exit 1
    fi
    
    sleep 0.5
done

if [ "$SERVER_READY" = false ]; then
    echo "ERROR: Debug server did not start listening within 10 seconds"
    if [ -f /tmp/debugpy.log ]; then
        echo "=== Debug log ==="
        cat /tmp/debugpy.log
    fi
    exit 1
fi

if [ -f /tmp/debugpy.log ]; then
    echo "=== Debug log ==="
    tail -20 /tmp/debugpy.log
fi

echo "Ready to attach debugger"

wait $DEBUG_PID