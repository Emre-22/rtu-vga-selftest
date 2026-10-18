"""Verified, content-addressed ETR bitstream transfer; no startup/firmware edits.

python fpga/upload.py --port COM3 --bin build/tt_um_emre_vga_selftest.bin --start
Requires the official mpremote command installed on the host.
"""

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import tempfile

PREFIX = "tt_um_emre_vga_selftest"
MARKER = "RTU_FILECHECK "
RESERVE = 4096


class Board:
    def __init__(self, port):
        self.port = port

    def command(self, *args, timeout=90):
        result = subprocess.run(["mpremote", "connect", self.port, *args],
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError("mpremote failed: " + (result.stderr or result.stdout).strip())
        return result.stdout

    def inspect(self, path):
        # Read-only preflight/hash, in bounded chunks suitable for MicroPython.
        code = """import os, hashlib, binascii, json
v=os.statvfs('/')
r={'free':(v[1] or v[0])*v[4], 'size':None, 'sha256':None}
try:
 f=open(%r,'rb')
except OSError:
 f=None
if f is not None:
 h=hashlib.sha256()
 n=0
 while True:
  b=f.read(512)
  if not b: break
  h.update(b)
  n+=len(b)
 f.close()
 r['size']=n
 r['sha256']=binascii.hexlify(h.digest()).decode()
print(%r+json.dumps(r))
""" % (path, MARKER)
        output = self.command("exec", code)
        lines = [line[len(MARKER):] for line in output.splitlines() if line.startswith(MARKER)]
        if len(lines) != 1:
            raise RuntimeError("Board did not return exactly one verified file report")
        return json.loads(lines[0])


def upload(board, binary):
    binary = Path(binary)
    payload = binary.read_bytes()
    if not payload:
        raise RuntimeError("Empty bitstream refused")
    digest = hashlib.sha256(payload).hexdigest()
    name = PREFIX + "_" + digest[:12]
    final = "/bitstreams/" + name + ".bin"
    report = board.inspect(final)
    if report["size"] is not None:
        if report["size"] != len(payload) or report["sha256"] != digest:
            raise RuntimeError("Existing content-addressed filename differs; refusing overwrite")
        return name, digest, len(payload)
    if report["free"] < len(payload) + RESERVE:
        raise RuntimeError("Insufficient board flash: %d free, need at least %d; no files changed" %
                           (report["free"], len(payload) + RESERVE))
    staged = "/bitstreams/.rtu_vga_" + secrets.token_hex(8) + ".upload"
    if board.inspect(staged)["size"] is not None:
        raise RuntimeError("Staging name exists; refusing overwrite")
    board.command("exec", "import os\ntry: os.mkdir('/bitstreams')\nexcept OSError: pass")
    try:
        board.command("fs", "cp", str(binary), ":" + staged)
        report = board.inspect(staged)
        if report["size"] != len(payload) or report["sha256"] != digest:
            raise RuntimeError("Transferred size or SHA-256 mismatch; FPGA not selected")
        # The final filename was absent during preflight. No existing project is removed.
        board.command("exec", "import os\nos.rename(%r,%r)" % (staged, final))
        report = board.inspect(final)
        if report["size"] != len(payload) or report["sha256"] != digest:
            raise RuntimeError("Final size or SHA-256 mismatch; FPGA not selected")
    except Exception:
        # Only our randomly named temporary file from this invocation is eligible.
        try:
            board.command("exec", "import os\ntry: os.remove(%r)\nexcept OSError: pass" % staged)
        except Exception:
            print("Could not clean our staging file: " + staged)
        raise
    return name, digest, len(payload)


def start(board, project):
    source = Path(__file__).with_name("start_test.py").read_text(encoding="utf-8")
    source = source.replace('PROJECT = "' + PREFIX + '"', 'PROJECT = "' + project + '"', 1)
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8", delete=False) as stream:
            stream.write(source)
            path = Path(stream.name)
        print(board.command("run", str(path)), end="")
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--bin", required=True, type=Path)
    parser.add_argument("--start", action="store_true", help="Select verified image and start PWM temporarily")
    args = parser.parse_args(argv)
    board = Board(args.port)
    project, digest, size = upload(board, args.bin)
    print("Verified %d bytes SHA-256 %s" % (size, digest))
    print("Stored project: " + project)
    if args.start:
        start(board, project)
    else:
        print('To select temporarily, rerun: python fpga/upload.py --port "%s" --bin "%s" --start' %
              (args.port, args.bin))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        raise SystemExit(str(error))
