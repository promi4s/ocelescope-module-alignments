# Case-Centric Alignments

case-centric Alignments

An [Ocelescope](https://www.ocelescope.org) backend module. It is a FastAPI app
that `ocelescope-backend` discovers through the `ocelescope_backend.modules`
entry point in `pyproject.toml` and serves under `/modules/caseCentricAlignments/v1`.

- `src/ocelescope_module_case_centric_alignments/module.py` — module class `CaseCentricAlignments` (key `caseCentricAlignments`)
- `src/ocelescope_module_case_centric_alignments/routes.py` — API routes

Install it next to `ocelescope-backend` (e.g. as a uv workspace member of an
Ocelescope module project) and run `ocelescope-backend serve`.

## Updating from the template

This module was generated with [Copier](https://copier.readthedocs.io). To pull
in later changes from the template, commit your work and run in this folder:

```sh
uvx copier update
```
