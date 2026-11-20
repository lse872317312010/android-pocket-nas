#!/usr/bin/env python3
"""Exercise two private Syncthing v1 daemons, using loopback and disposable data."""

import hashlib
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET


def reserve_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    return sock


def wait_until(description, check, processes):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if any(proc.poll() is not None for proc in processes):
            raise RuntimeError(f"Syncthing exited while waiting for {description}")
        if check():
            return
        time.sleep(0.25)
    raise TimeoutError(description)


def matches(path, expected):
    try:
        return path.read_bytes() == expected
    except FileNotFoundError:
        return False


def prepare(node):
    node.mkdir()
    subprocess.run(["syncthing", "generate", "--home", str(node / "config")],
                   check=True, stdout=subprocess.DEVNULL)
    return ET.parse(node / "config/config.xml")


def configure(node, tree, peer_id, sync_port, peer_port, gui_port, primary):
    root = tree.getroot()
    own_id = root.find("device").get("id")
    for old in root.findall("folder"):
        root.remove(old)
    peer = ET.SubElement(root, "device", id=peer_id)
    ET.SubElement(peer, "address").text = f"tcp://127.0.0.1:{peer_port}"
    for name in ("hot", "camera"):
        folder_type = "sendreceive" if name == "hot" else (
            "sendonly" if primary else "receiveonly")
        directory = node / name
        directory.mkdir()
        (directory / ".stfolder").mkdir()
        folder = ET.SubElement(root, "folder", id=name, label=name, path=str(directory),
                               type=folder_type, rescanIntervalS="1", fsWatcherEnabled="false")
        for device in (own_id, peer_id):
            ET.SubElement(folder, "device", id=device)
    gui = root.find("gui")
    gui.find("address").text = f"127.0.0.1:{gui_port}"
    opts = root.find("options")
    for key, value in {
        "listenAddress": f"tcp://127.0.0.1:{sync_port}",
        "globalAnnounceEnabled": "false", "localAnnounceEnabled": "false",
        "relaysEnabled": "false", "natEnabled": "false", "startBrowser": "false",
        "urAccepted": "-1", "crashReportingEnabled": "false",
        "autoUpgradeIntervalH": "0",
    }.items():
        for old in opts.findall(key):
            opts.remove(old)
        ET.SubElement(opts, key).text = value
    tree.write(node / "config/config.xml", encoding="utf-8", xml_declaration=True)


def stop(proc):
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def simulate(base):
    home, primary = base / "home", base / "primary"
    nodes = [home, primary]
    configs = [prepare(node) for node in nodes]
    ids = [tree.getroot().find("device").get("id") for tree in configs]
    sockets = [reserve_port() for _ in range(4)]
    try:
        ports = [sock.getsockname()[1] for sock in sockets]
        for i, node in enumerate(nodes):
            configure(node, configs[i], ids[1-i], ports[i], ports[1-i], ports[2+i], i == 1)
    finally:
        for sock in sockets:
            sock.close()

    processes = []
    logs = []

    def start(node):
        log = (node / "daemon.log").open("ab")
        logs.append(log)
        proc = subprocess.Popen(["syncthing", "serve", "--home", str(node / "config"),
                                 "--no-browser", "--no-restart"], stdout=log,
                                stderr=subprocess.STDOUT, env={**os.environ, "STNOUPGRADE": "1"})
        processes.append(proc)
        return proc

    try:
        home_proc = start(home)
        primary_proc = start(primary)
        photo = os.urandom(65536)
        document = os.urandom(8192)
        source = primary / "camera/sample.bin"
        received = home / "camera/sample.bin"
        source.write_bytes(photo)
        (home / "hot/document.bin").write_bytes(document)
        offline = primary / "hot/document.bin"
        wait_until("camera upload and hot-file download",
                   lambda: matches(received, photo) and matches(offline, document),
                   [home_proc, primary_proc])
        vault = base / "independent-backup"
        vault.mkdir()
        backup = [sys.executable, Path(__file__).with_name("backup_camera.py"), received.parent, vault]
        subprocess.run(backup, check=True)
        captures = []
        middle = b"B" * len(photo)
        final = b"C" * len(photo)
        for index, revision in enumerate((middle, final), start=1):
            source.write_bytes(revision)
            # Distinct mtimes allow Syncthing to discover equal-size revisions.
            stamp = int(time.time()) + 10 * index
            os.utime(source, (stamp, stamp))
            wait_until("same-name camera overwrite", lambda: matches(received, revision),
                       [home_proc, primary_proc])
            result = subprocess.run(backup, check=True, capture_output=True, text=True)
            captures.append(Path(result.stdout.strip()) / source.name)
        assert matches(vault / "current" / source.name, final)
        assert matches(captures[0], photo)
        assert matches(captures[1], middle)
        stop(home_proc)
        assert matches(offline, document), "Offline hot file unavailable"
        source.unlink()
        home_proc = start(home)
        wait_until("camera deletion propagation after reconnect",
                   lambda: not received.exists(), [home_proc, primary_proc])
        subprocess.run(backup, check=True)
        assert matches(vault / "current" / source.name, final)
        assert len(list((vault / "history").iterdir())) == 2
        restored = base / "recovery/sample.bin"
        restored.parent.mkdir()
        shutil.copyfile(captures[1], restored)
        if hashlib.sha256(restored.read_bytes()).digest() != hashlib.sha256(middle).digest():
            raise RuntimeError("Recovered photo differs from original")
        print("PASS three camera versions, offline hot read, propagated deletion and middle-version restore")
        print("Recovered SHA-256:", hashlib.sha256(restored.read_bytes()).hexdigest())
    except BaseException:
        for node in nodes:
            log = node / "daemon.log"
            if log.exists():
                print(log.read_text(errors="replace")[-4000:])
        raise
    finally:
        for proc in processes:
            stop(proc)
        for log in logs:
            log.close()


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="pocket-nas-sync-") as directory:
        simulate(Path(directory))
