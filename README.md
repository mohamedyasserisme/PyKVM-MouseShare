## PyKVM-MouseShare 

A lightweight Python-based KVM-style mouse sharing tool.

### Overview
This project allows controlling a remote Windows PC mouse
from another machine using Python sockets.

### How it works
- Sender captures mouse & keyboard events
- Sends relative mouse movement (dx, dy) over UDP
- Receiver applies real cursor movement using Win32 API

⚠️ Design Note:
The mouse cursor does NOT move on the sender device by design.
Only relative movement data is transmitted.
The real cursor is visible and moves normally on the receiver PC.

This avoids cursor desync and keeps the tool lightweight.

### Features
- Real-time mouse movement, click, and scroll
- Hotkey-based control switching (CTRL + ALT)
- Token-based validation
- No GUI – low latency
