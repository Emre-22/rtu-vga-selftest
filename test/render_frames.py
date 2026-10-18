#!/usr/bin/env python3
"""Convert the simulator's actual raster PPMs to PNG using only stdlib."""
from pathlib import Path
import struct
import zlib


def chunk(kind, data):
    return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))


for source in sorted(Path('test/output').glob('frame_*.ppm')):
    tokens = source.read_text().split()
    assert tokens[:4] == ['P3', '640', '480', '255'], source
    width, height = map(int, tokens[1:3])
    pixels = bytes(map(int, tokens[4:]))
    assert len(pixels) == width * height * 3, source
    raster = b''.join(b'\0' + pixels[y*width*3:(y+1)*width*3] for y in range(height))
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raster, 9)) + chunk(b'IEND', b'')
    target = source.with_suffix('.png')
    target.write_bytes(png)
    print(f'RTL raster: {target}')
