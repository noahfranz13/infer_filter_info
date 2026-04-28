# Infer Filter Information

[![CI](https://github.com/noahfranz13/infer_filter_info/actions/workflows/ci.yml/badge.svg)](https://github.com/noahfranz13/infer_filter_info/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/infer-filter-info/badge/?version=latest)](https://infer-filter-info.readthedocs.io/en/latest/?badge=latest)

This is a minimal python package for inferring the filter effective wavelength and transmission curve based on the filter name and, optionally, 
the telescope and instrument. In the case that just the filter name is provided we have defined defaults that will be correct in a majority of cases.

## Installation

You can install `infer-filter-info` directly from PyPI:

```bash
pip install infer-filter-info
```

## Documentation

Full documentation is available at [https://infer-filter-info.readthedocs.io](https://infer-filter-info.readthedocs.io).

## Development

### Developer Installation

To install the package from source for development:

```bash
git clone https://github.com/noahfranz13/infer_filter_info.git
cd infer_filter_info
pip install -e .[dev,docs]
```

### Semantic Versioning

This project uses [Semantic Versioning](https://semver.org/) and [Conventional Commits](https://www.conventionalcommits.org/). Versions are automatically managed by `python-semantic-release` upon pushing to the `main` branch.

To ensure proper version bumping, please use the following commit message formats:
- `fix: ...` for a patch release (e.g., 0.0.1)
- `feat: ...` for a minor release (e.g., 0.1.0)
- `feat!: ...` or `fix!: ...` (with a `BREAKING CHANGE` footer) for a major release (e.g., 1.0.0)

