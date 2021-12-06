#! /usr/bin/env python3
import sys
sys.path.insert(1, "..") # add package to import path

import random
import unittest

import stellar_sdk as sdk
import sep39


class SanityTest(unittest.TestCase):

    def test_sanity_check(self):
        """ Tests that a random set of bytes encode-decodes correctly
        """
        media_type = ("application/octet-stream", {"n": "random"})
        asset = random.randbytes(int(10e3))

        rows = sep39.encode(asset, media_type)
        medias, binaries = sep39.decode(rows)
        self.assertEqual(len(medias), 1)
        self.assertEqual(len(binaries), 1)
        binary, (mtype, params) = binaries[0], medias[0]

        self.assertEqual(binary, asset)
        self.assertEqual(mtype, media_type[0])
        self.assertEqual(params, media_type[1])

    def test_manage_data(self):
        """ Ensures that the format is compatible with ManageData operations
        """
        data = random.randbytes(random.randint(10e3, 100e3))
        for key, value in sep39.encode(data):
            sdk.ManageData(key, value).to_xdr_object()


class MultipleBuffersTest(unittest.TestCase):

    def test_two_buffers(self):
        """ Tests that two random sets of bytes encode-decode correctly
        """
        first_bin = b"This is a string of bytes that should span over more " + \
            b"than a single row entry, thus checking that these edge cases " + \
            b"are handled correctly."
        first_mt = ("text/plain", {"n": "prefix"})

        second_mt = ("application/octet-stream", {"n": "bytes"})
        second_bin = random.randbytes(int(10e3))

        self.assertRaises(ValueError, sep39.encode, first_bin+second_bin, first_mt, second_mt)
        first_mt[1]["s"] = str(len(first_bin))

        rows = sep39.encode(first_bin + second_bin, first_mt, second_mt)
        medias, binaries = sep39.decode(rows)
        self.assertEqual(len(medias), 2)
        self.assertEqual(len(binaries), 2)

        expected = ((first_bin, first_mt), (second_bin, second_mt))
        for i, (binary, media_type) in enumerate(zip(binaries, medias)):
            self.assertEqual(binary, expected[i][0])
            self.assertEqual(media_type, expected[i][1])


class BenchmarkTestCase(unittest.TestCase):

    def test_encoding_ratio(self):
        """ Benchmarks the encoding ratio at various binary sizes
        """

        # pick random sizes of a particular magnitude within a small margin
        sizes = map(int, (
            base + random.randint(-base // 10, base // 10)
            for base in (
                10,
                1e3,
                50e3,
                112e3,
                # 1e6,
            ) for i in range(5)
        ))

        for size in sizes:
            # print('| %s | %d | %0.1f |' % (
            #     to_human_readable(size),
            #     math.ceil(size / ((64 / 1.15) + 64)),
            #     math.ceil(size / ((64 / 1.15) + 64)) * 0.5))
            with self.subTest(size=size):
                binary = random.randbytes(size)
                encoded = sep39.encode(binary)

                for k, v in encoded:
                    self.assertLessEqual(len(k), 64)
                    self.assertLessEqual(len(v), 64)

                medias, binaries = sep39.decode(encoded)
                self.assertEqual(len(medias), 1)
                self.assertEqual(len(binaries), 1)
                decoded, (media_type, params) = binaries[0], medias[0]

                self.assertEqual(binary, decoded)
                self.assertEqual(media_type, "")
                self.assertEqual(params, {})

                # encoded_size = sum((len(k) + len(v) for k, v in encoded))
                # growth = 100 * ((encoded_size / float(size)) - 1)
                # print("Original size:", to_human_readable(size))
                # print("Encoded size: ", to_human_readable(encoded_size))
                # print(f"  {growth:.2f}% growth")
                # print(f"  {len(encoded)} entries")
                # print("  %d imperfect row(s)" % (len(list(filter(
                #     lambda r: len(r[0]) != 64 or len(r[1]) != 64,
                #     encoded)))))


def read_image(filename):
    return open(filename, "rb").read()

def to_human_readable(size):
    """ A helper to convert byte counts to something human-friendly.
    """
    if size < 1e3: return f"{size:.2f} B"
    if size < 1e6: return f"{size / 1e3:.2f} KB"
    if size < 1e9: return f"{size / 1e6:.2f} MB"
    return f"{size / 1e9} GB"
