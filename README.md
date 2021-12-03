A reference implementation of the in-draft SEP-39, [here](https://github.com/stellar/stellar-protocol/pull/1090). It is accurate up to commit [b274d9c9](https://github.com/stellar/stellar-protocol/pull/1090/commits/b274d9c96036c575815c4e51c1362d253051b45e] on the pull request.

To build and run the code:

```bash
    pip install base91 stellar_sdk
    python -m unittest discover
```

You can also run it on a specific file to see how it encodes:

    $ python sep39.py sep39.py
    Encoding file 'sep39.py' ...
      done (took 31.89ms)
      checksum: 2296490166
      stats:
       - original size:   6799
       - ManageData rows: 60
       - encoded size:    7659
       - ratio:           1.13x

