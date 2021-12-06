A reference implementation of the in-draft SEP-39, [here](https://github.com/stellar/stellar-protocol/pull/1090). It is accurate up to commit [0ad251d](https://github.com/stellar/stellar-protocol/pull/1090/commits/0ad251d19330f8b035f9da232fb20e444f2e2209] on the pull request.

To build and run the code:

```bash
    pip install base91 stellar_sdk
    python -m unittest discover
```

You can also run it on a specific file to see how it encodes:

    $ python sep39.py sep39.py
    Encoding file 'sep39.py' ...
      done (took 11.42ms)
      checksum: 333028532
      stats:
       - original size:   7529
       - ManageData rows: 67
       - encoded size:    8482
       - ratio:           1.13x
