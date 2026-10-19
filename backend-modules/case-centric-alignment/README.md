# ocelescope-module-case-centric-alignments

An [Ocelescope](https://www.ocelescope.org) backend module that computes
case-centric alignments for object-centric event logs.

For a selected object type, the log is aligned against a Petri net resource,
or against a model discovered with Alpha+++ if none is given.

## Installation

```sh
pip install ocelescope-module-alignments
```

Install it next to `ocelescope-backend`. The module is picked up automatically
and served under `/modules/alignments/v1`.
