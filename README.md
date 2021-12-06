A reference implementation of the in-draft SEP-39, [here](https://github.com/stellar/stellar-protocol/pull/1090). It is accurate up to commit [1afb31e8](https://github.com/stellar/stellar-protocol/pull/1090/commits/1afb31e88b3379a38a156e2b200d9e2c5ecc5708) on the standard's pull request.

To build and run the code:

```bash
    pip install base91 stellar_sdk
    python -m unittest discover
```

You can also run it on a specific file to see how it encodes:

    $ python sep39.py sep39.py
    Encoding file 'sep39.py' ...
      done (took 10.34ms)
      checksum: 1156454214
      stats:
       - original size:   7170
       - ManageData rows: 64
       - encoded size:    8071
       - ratio:           1.13x
