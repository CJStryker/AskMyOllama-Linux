#!/usr/bin/env bash

# Wait for X11
while ! xdpyinfo >/dev/null 2>&1; do
  sleep 1
done

# Wait for system tray
sleep 5

exec "$HOME/.local/bin/autonomy-tray.py"
#!/usr/bin/env bash

# Wait for DISPLAY
until [ -n "$DISPLAY" ] && xdpyinfo >/dev/null 2>&1; do
  sleep 1
done

# Wait for DBUS session
until busctl --user status >/dev/null 2>&1; do
  sleep 1
done

# Give LXQt panel time to start
sleep 5

exec "$HOME/.local/bin/autonomy-tray.py"
