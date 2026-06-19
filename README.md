# 📹 P2P Video Call App

A simple peer-to-peer video calling application built with Python. No servers, no accounts — just two machines talking directly to each other over TCP.

Built as a Computer Networks class project.

---

## 📸 Screenshots

<p align="center">
  <img src="screenshots/1.png" width="32%" />
  <img src="screenshots/2.png" width="32%" />
  <img src="screenshots/3.png" width="32%" />
</p>

---

## ✨ Features

- 🎥 **Live video** — see both yourself and your peer in real time
- 🎙 **Two-way audio** — full-duplex voice transmission
- 🔇 **Mute button** — silence your mic without ending the call
- 🌐 **Works over the internet** via [Tailscale](https://tailscale.com) VPN
- 🖥 **Dark UI** — clean, minimal interface built with Tkinter

---

## 🛠 Tech Stack

| Layer     | Technology |
|-----------|------------|
| Transport | **TCP** sockets (raw Python `socket`) |
| Video     | **OpenCV** capture → JPEG encoding → TCP stream |
| Audio     | **sounddevice** (PortAudio) PCM stream over TCP |
| UI        | **Tkinter** + **Pillow** for frame rendering |
| Framing   | 4-byte length prefix before each video/audio chunk |

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

> **macOS only:** if `pyaudio` fails to build, run `bash setup.sh` first — it compiles PortAudio from source.

---

## 🚀 Usage

Both users run the **same** `main.py`. One acts as **Host**, the other as **Guest**.

### Host (the one who receives the incoming connection)
1. Check **"I'm host"**
2. Click **📞 Call**
3. Share your IP with your peer

### Guest (the one who connects)
1. Enter the host's IP address
2. Click **📞 Call**

> To call over the internet, both users need [Tailscale](https://tailscale.com) installed and connected to the same network. Use the `100.x.x.x` Tailscale IP.


## 🔌 How It Works

```
Host                          Guest
 |                              |
 |-- listens on TCP :9999 ----->|-- connects to host:9999 (video)
 |-- listens on TCP :8888 ----->|-- connects to host:8888 (audio)
 |                              |
 |<======= video frames =======>|
 |<======= audio chunks =======>|
```

Each frame/chunk is prefixed with a **4-byte big-endian length** so the receiver knows exactly how many bytes to read from the TCP stream.

---

## 📁 Project Structure

```
main.py          # main application (run this)
main2.py         # identical copy (for local testing — run both)
requirements.txt # Python dependencies
setup.sh         # macOS PortAudio build script
```

---

## 🧪 Local Testing

Run `main.py` and `main2.py` simultaneously on the same machine:

- `main.py` → check **"I'm host"** → Click Call
- `main2.py` → enter `127.0.0.1` → Click Call

---

## Requirements

```
opencv-python
pillow
sounddevice
numpy
```
