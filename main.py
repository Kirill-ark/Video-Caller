import tkinter as tk
from tkinter import Label
import socket, threading, struct, time, cv2, numpy as np, sounddevice as sd
from PIL import Image, ImageTk

VP, AP = 9999, 8888  # video port, audio port
RATE, CH, DTYPE, CHUNK = 44100, 1, 'int16', 1024
VW, VH = 480, 360  # video size
running = False
muted = False

# print local IP on startup
try:
    local_ip = socket.gethostbyname(socket.gethostname())
except:
    local_ip = '0.0.0.0'
print(f"Your IP: {local_ip}")


def pack(sock, data):
    sock.sendall(struct.pack('>I', len(data)) + data)


def unpack(sock):
    n = struct.unpack('>I', recvn(sock, 4))[0];
    return recvn(sock, n)


def recvn(sock, n):
    buf = b''
    while len(buf) < n:
        c = sock.recv(n - len(buf))
        if not c: raise ConnectionError
        buf += c
    return buf


def camera():
    for i in range(5):
        cap = cv2.VideoCapture(i)
        for _ in range(30):
            ret, f = cap.read()
            if ret: return cap
            time.sleep(0.1)
        cap.release()


def fit(frame, w, h):
    fh, fw = frame.shape[:2]
    scale = min(w / fw, h / fh)
    nw, nh = int(fw * scale), int(fh * scale)
    return cv2.resize(frame, (nw, nh))


def show(lbl, frame):
    img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    lbl.config(image=img);
    lbl.image = img


def rx_video(sock):  # Получает сжатые JPEG-байты, декодирует их в кадр (imdecode), показывает в окне "Remote".
    while running:
        try:
            f = cv2.imdecode(np.frombuffer(unpack(sock), np.uint8), cv2.IMREAD_COLOR)
            if f is not None: show(remote_lbl, fit(f, VW, VH))
        except:
            break


def tx_video(
        sock):  # Захватывает кадр с камеры → показывает в своём окошке → сжимает в JPEG (качество 60%) → отправляет собеседнику.
    cap = camera()
    while running:
        ret, f = cap.read()
        if not ret: break
        show(local_lbl, fit(f, VW // 2, VH // 2))
        _, buf = cv2.imencode('.jpg', cv2.resize(f, (VW, VH)), [cv2.IMWRITE_JPEG_QUALITY, 60])
        try:
            pack(sock, buf.tobytes())
        except:
            break
    cap.release()


def rx_audio(
        sock):  # Открывает поток воспроизведения. Получает аудиобайты → конвертирует в массив NumPy → отправляет в динамики.
    out = sd.OutputStream(samplerate=RATE, channels=CH, dtype=DTYPE)
    out.start()
    while running:
        try:
            out.write(np.frombuffer(unpack(sock), dtype=DTYPE))
        except:
            break
    out.stop()


def tx_audio(sock):
    def cb(d, f, t, s):
        if running:
            pack(sock, (np.zeros_like(d) if muted else d).tobytes())

    with sd.InputStream(samplerate=RATE, channels=CH, dtype=DTYPE, blocksize=CHUNK, callback=cb):
        while running: sd.sleep(100)


def toggle_mute():
    global muted
    muted = not muted
    mute_btn.config(text="🎙 Unmute" if muted else "🔇 Mute",
                    bg="#FF6D00" if muted else "#7C4DFF")


def connect():
    global running;
    running = True
    st.config(text="Connecting...", fg="#FFA500")

    def run():
        try:
            if host.get():
                def srv(port, box):
                    s = socket.socket();
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind(('', port));
                    s.listen(1);
                    c, a = s.accept();
                    s.close()
                    print(f"Connected: {a} on port {port}");
                    box.append(c)

                st.config(text="Waiting for guest...", fg="#FFA500")
                vb, ab = [], []
                t1 = threading.Thread(target=srv, args=(VP, vb), daemon=True)
                t2 = threading.Thread(target=srv, args=(AP, ab), daemon=True)
                t1.start();
                t2.start();
                t1.join();
                t2.join()
            else:
                ip = entry.get().strip()

                def try_conn(port, box):
                    for _ in range(15):
                        try:
                            box.append(socket.create_connection((ip, port), timeout=2)); return
                        except:
                            time.sleep(1)

                vb, ab = [], []
                t1 = threading.Thread(target=try_conn, args=(VP, vb), daemon=True)
                t2 = threading.Thread(target=try_conn, args=(AP, ab), daemon=True)
                t1.start();
                t2.start();
                t1.join();
                t2.join()
                if not vb or not ab: raise ConnectionError("Could not connect")
            vs, as_ = vb[0], ab[0]
            st.config(text="● Call active", fg="#00C853")
            for fn, sk in [(rx_video, vs), (tx_video, vs), (rx_audio, as_), (tx_audio, as_)]:
                threading.Thread(target=fn, args=(sk,), daemon=True).start()
        except Exception as e:
            st.config(text=f"Error: {e}", fg="red")

    threading.Thread(target=run, daemon=True).start()


def disconnect():
    global running;
    running = False
    st.config(text="Disconnected", fg="#888")
    remote_lbl.config(image="");
    local_lbl.config(image="")


# ── GUI ────────────────────────────────────────────────────────
win = tk.Tk();
win.title("Video Call");
win.configure(bg="#1e1e2e");
win.resizable(False, False)

top = tk.Frame(win, bg="#1e1e2e");
top.pack(pady=10)
host = tk.BooleanVar()
tk.Checkbutton(top, text="I'm host", variable=host,
               bg="#1e1e2e", fg="white", selectcolor="#313244",
               activebackground="#1e1e2e", activeforeground="white").pack(side=tk.LEFT, padx=5)
entry = tk.Entry(top, width=22, bg="#313244", fg="white",
                 insertbackground="white", relief=tk.FLAT)
entry.pack(side=tk.LEFT, padx=5);
entry.insert(0, "Host IP")

vrow = tk.Frame(win, bg="#1e1e2e");
vrow.pack(pady=5)


def vcell(parent, title, w, h):
    f = tk.Frame(parent, bg="#1e1e2e");
    f.pack(side=tk.LEFT, padx=5)
    tk.Label(f, text=title, bg="#1e1e2e", fg="#888", font=("Arial", 9)).pack()
    c = tk.Canvas(f, width=w, height=h, bg="#111", highlightthickness=0);
    c.pack()
    lbl = Label(c, bg="#111");
    c.create_window(w // 2, h // 2, window=lbl)
    return lbl


remote_lbl = vcell(vrow, "Remote", VW, VH)
local_lbl = vcell(vrow, "You", VW // 2, VH // 2)

st = tk.Label(win, text="Ready", fg="#888", bg="#1e1e2e", font=("Arial", 10));
st.pack()

brow = tk.Frame(win, bg="#1e1e2e");
brow.pack(pady=10)
tk.Button(brow, text="📞 Call", width=12, bg="#00C853", fg="black",
          relief=tk.FLAT, font=("Arial", 11, "bold"), command=connect).pack(side=tk.LEFT, padx=5)
mute_btn = tk.Button(brow, text="🔇 Mute", width=12, bg="#7C4DFF", fg="black",
                     relief=tk.FLAT, font=("Arial", 11, "bold"), command=toggle_mute)
mute_btn.pack(side=tk.LEFT, padx=5)
tk.Button(brow, text="✖ End call", width=12, bg="#FF1744", fg="black",
          relief=tk.FLAT, font=("Arial", 11, "bold"), command=disconnect).pack(side=tk.LEFT, padx=5)

win.mainloop()
