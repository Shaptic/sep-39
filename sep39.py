#! /usr/bin/env python3
import math
import string
import zlib

from typing import List, Tuple, Dict, Optional

import base91
import stellar_sdk


__version__ = "1"


def render_media_type(media_type, **params):
    return f"{media_type}{';' if params else ''}" + \
        ';'.join(f'{k}={v}' for k, v in params.items())

def encode(data: bytes, *media_types: List[Tuple[str, Dict[str, str]]]) -> List[Tuple[str, bytes]]:
    """ Performs SEP-39 encoding of the given `data` as the given `media_types`.

    :param media_types  [{str: str}, ...]    a list of pairs in which the first
        item is the media type (e.g. image/png) and the second item is a
        dictionary of media type parameters (e.g. {"name": "picture"}).

    :warning    Media types cannot contain whitespace, so all parameters must
        not contain whitespace. They also cannot contain '=' or ';' characters,
        as those are the separators for parameters.

    :returns [(str, bytes), ...]    a list of row entries compatible with
        Stellar's `ManageData` operation, with the `data` entry encoded in
        SEP-39 format.

    References:
        https://stellar.org/protocol/sep-39
        https://www.iana.org/assignments/media-types/media-types.xhtml
        http://base91.sourceforge.net/
    """
    assert isinstance(data, (bytes, bytearray)), f"invalid data: {type(data)}"

    if len(data) >= 126000:
        raise ValueError(f"{len(data)} is too big for a SEP-39 asset")

    for _, params in media_types[:-1]:
        if 's' not in params:
            raise ValueError("expected size parameter s=... not found")

    metadata = ','.join(map(lambda mt: render_media_type(mt[0], **mt[1]), media_types))
    header = f"{__version__}{str(len(metadata))}{metadata}"
    rows = []

    # First, insert the header as-is.
    for i in range(0, len(header), 62+64):
        idx = _encode_index(i)
        key, value = f"{idx}{header[i:i+62]}", header[i+62:i+62+64]
        rows.append((key, value.encode("ascii")))

    # Then, insert the raw binary data with a BasE91-encoding on keys.

    # top off the last-used row, first
    delta = 0
    key, value = rows[-1]
    append, data, delta = _encode_nearest(data, 64 - len(key))
    value, data = value + data[:64 - len(value)], data[64 - len(value):]
    rows[-1] = (key + append, value)

    # then fill in the rest of the rows
    i = len(rows)
    while data:
        index = _encode_index(i)
        key, data, _ = _encode_nearest(data, 64 - len(index))
        value, data = data[:64], data[64:]
        rows.append((index + key, value))
        i += 1

    return rows

def decode(rows: List[Tuple[str, bytes]]) -> Tuple[
    List[
        Tuple[str, Dict[str, str]]
    ],
    List[bytes]
]:
    """ Decodes the SEP-39 formatted `rows` into media types and binaries.
    """
    key1, value1 = rows[0]
    assert key1.startswith(f"00{__version__}"), "invalid SEP-39 row"

    metadata_len = ""
    for j in range(3, 3+7):
        if not key1[j].isdigit(): break
        metadata_len += key1[j]
        # Edge case: if there's no metadata, we'd otherwise consume binary bytes
        # as the length if it started with digits.
        if j == 3 and key1[j] == '0': break

    try:
        metadata_len = int(metadata_len, 10)
        assert metadata_len < 126000, "length exceeds maximum"

    except (AssertionError, ValueError) as e:
        raise ValueError("invalid metadata length: " + str(e))

    # Consume exactly enough metadata bytes:

    # First, gobble up as much of the first row as necessary.
    metadata = key1[j:][:metadata_len]
    metadata += value1[:metadata_len - len(metadata)].decode("ascii")

    # Then, we know each row gives us exactly 62+64 characters of data. So we
    # now how many rows we can fully consume and how many characters of the last
    # row to consume.
    rem = metadata_len - len(metadata)
    if rem > 0:
        r, c = divmod(rem, 62 + 64)

        # consume full rows
        for key, value in rows[1:1+r]:
            metadata += key + value.decode("ascii")

        # only consume exactly `c` characters of the last row
        key, value = rows[1+r]
        metadata += key[:c] + value[:max(0, c-64)].decode("ascii")

    assert len(metadata) == metadata_len, "parsing metadata failed"

    # Finally, let's turn the rest of the buffer (that is, starting past the
    # header + metadata) into a long bytestring.
    r, c = divmod(len("1") + len(str(metadata_len)) + metadata_len, 62 + 64)
    key, value = rows[r]
    binary = base91.decode(key[2+c:]) + value[max(0, c-62):]
    for key, value in rows[r+1:]:
        binary += base91.decode(key[2:]) + value

    # Turn the metadata string into something palpable:
    #   a list of ("type/subtype", {k1: v1, k2: v2}) tuples.
    media_types = tuple(
        (media[0], dict(param.split('=') for param in media[1:]))
        for media in (media.split(';') for media in metadata.split(','))
    )

    # Split the binary based on sizes and optionally perform checksum
    # verifications. Note that if there's more than one media type,
    # all-but-the-last *must* have size parameters.
    binaries = []
    for i, (media_type, params) in enumerate(media_types):
        s = int(params.get('s', len(binary)))
        binaries.append(binary[:s])
        binary = binary[s:]

        chk = params.get('c', None)
        actual = zlib.crc32(binaries[-1])
        if chk is not None and chk != actual:
            raise ValueError(f"Invalid checksum: expected {chk} got {actual}")

    return media_types, binaries

def _encode_index(i: int) -> str:
    assert i >= 0 and i <= 1295, f"{i} is out of range"
    ALPHABET = string.digits + string.ascii_lowercase
    d, r = divmod(i, len(ALPHABET))
    return ALPHABET[d] + ALPHABET[r]

def _encode_nearest(data: bytes, n: int=64) -> Tuple[str, bytes]:
    """ BasE91-encodes `data` as close to (but not exceeding) `n` as possible.
    """

    # We know that BasE91 will never do better than 10% overhead, so that's a
    # reasonable starting point for trying to get exactly an n-sized chunk
    # encoded.
    for i in range(int(math.ceil(n / 1.10)), 0, -1):
        encoded = base91.encode(data[:i])
        if len(encoded) <= n:
            return encoded, data[i:], i

    return "", data, 0


if __name__ == "__main__":
    import os, sys
    import time

    if len(sys.argv) != 2:
        name = os.path.basename(sys.argv[0])
        print(f"Usage: {name} <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "rb") as f:
        b = f.read()

    media_type = ("image/png", {"n": "CLI", "c": zlib.crc32(b)})

    print(f"Encoding file '{filename}' ...")
    start = time.time()
    rows = encode(b, media_type)
    delta = (time.time() - start) * 1000
    print(f"  done (took {delta:.2f}ms)")

    total_size = sum(map(lambda r: len(r[0]) + len(r[1]), rows))
    print("  checksum:", media_type[1]['c'])
    print("  stats:")
    print(f"   - original size:   {len(b)}")
    print(f"   - ManageData rows: {len(rows)}")
    print(f"   - encoded size:    {total_size}")
    print(f"   - ratio:           {total_size/len(b):.2f}x")
