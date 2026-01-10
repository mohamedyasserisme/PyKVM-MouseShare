import socket
import json
from pynput.mouse import Listener as MouseListener
from pynput import keyboard

# ================= CONFIG =================
PORT = 5000
BUFFER_SIZE = 1024
SECRET = "mouse_kvm_secret"
# =========================================

# ===== Sender state =====
ctrl_pressed = False
alt_pressed = False
send_enabled = False
last_x = None
last_y = None


# ================= SENDER =================
def sender_mode():
    global last_x, last_y, send_enabled
    global ctrl_pressed, alt_pressed

    target_ip = input("Enter receiver IP: ")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print("\n[+] Sender running")
    print("[*] Hold CTRL + ALT to control the PC")
    print("[*] Release keys to return control to laptop\n")

    def send_data(data):
        data["token"] = SECRET
        sock.sendto(json.dumps(data).encode(), (target_ip, PORT))

    def on_move(x, y):
        global last_x, last_y

        if not send_enabled:
            last_x, last_y = x, y
            return

        if last_x is None:
            last_x, last_y = x, y
            return

        dx = x - last_x
        dy = y - last_y
        last_x, last_y = x, y

        if dx != 0 or dy != 0:
            send_data({"type": "move", "dx": dx, "dy": dy})

    def on_click(x, y, button, pressed):
        if not send_enabled:
            return
        send_data({
            "type": "click",
            "button": button.name,
            "pressed": pressed
        })

    def on_scroll(x, y, dx, dy):
        if not send_enabled:
            return
        send_data({
            "type": "scroll",
            "dx": dx,
            "dy": dy
        })

    MouseListener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    ).start()

    # 🔑 Keyboard logic (FIXED)
    def on_key_press(key):
        global ctrl_pressed, alt_pressed, send_enabled, last_x, last_y

        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            ctrl_pressed = True
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_pressed = True

        if ctrl_pressed and alt_pressed and not send_enabled:
            send_enabled = True
            last_x = None
            last_y = None
            print("[*] Control → PC")

    def on_key_release(key):
        global ctrl_pressed, alt_pressed, send_enabled

        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            ctrl_pressed = False
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            alt_pressed = False

        if send_enabled and not (ctrl_pressed and alt_pressed):
            send_enabled = False
            print("[*] Control → Laptop")

    with keyboard.Listener(on_press=on_key_press, on_release=on_key_release) as kl:
        kl.join()


# ================= RECEIVER (WIN32) =================
def receiver_mode():
    import win32api
    import win32con

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))

    print("\n[+] Receiver (Win32) running")
    print("[*] Cursor visible / real movement")
    print(f"[*] Listening on port {PORT}\n")

    while True:
        try:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            cmd = json.loads(data.decode())

            if cmd.get("token") != SECRET:
                continue

            if cmd["type"] == "move":
                x, y = win32api.GetCursorPos()
                win32api.SetCursorPos((x + cmd["dx"], y + cmd["dy"]))

            elif cmd["type"] == "click":
                if cmd["button"] == "left":
                    evt = win32con.MOUSEEVENTF_LEFTDOWN if cmd["pressed"] else win32con.MOUSEEVENTF_LEFTUP
                elif cmd["button"] == "right":
                    evt = win32con.MOUSEEVENTF_RIGHTDOWN if cmd["pressed"] else win32con.MOUSEEVENTF_RIGHTUP
                else:
                    continue
                win32api.mouse_event(evt, 0, 0, 0, 0)

            elif cmd["type"] == "scroll":
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_WHEEL,
                    0, 0,
                    cmd["dy"] * 120,
                    0
                )

        except KeyboardInterrupt:
            print("\n[!] Receiver stopped")
            break


# ================= MAIN =================
if __name__ == "__main__":
    print("\n--- Mouse Share (Python KVM – FINAL) ---")
    print("1. Sender (Laptop with mouse)")
    print("2. Receiver (PC to control)")

    choice = input("Choose (1 or 2): ")

    if choice == "1":
        sender_mode()
    elif choice == "2":
        receiver_mode()
    else:
        print("Invalid choice")
