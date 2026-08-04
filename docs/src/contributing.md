# How to contribute

## Using the issue tracker

You can suggest features, enhancements, or report bugs on our [issue tracker](https://github.com/k-tech-italy/bitcaster-django/issues).

You can also use the issue tracker to find an open issue for you to work on. Please mention in the issue that you are working on it.

## Changing the codebase

You should fork this project, make changes in your own fork, then submit a pull request.

To start working on this project:

* Install [uv](https://docs.astral.sh/uv)
* Clone the repository:

```bash
# using HTTPS
git clone https://github.com/k-tech-italy/bitcaster-django.git

# using SSH
git clone git@github.com:k-tech-italy/bitcaster-django.git
```

* If you use [direnv](https://direnv.net/), copy the `.envrc.example` file as follows, otherwise skip this step:

```bash
cp .envrc.example .envrc
```

* Create a virtual environment for the project using uv. Make sure you use the earliest supported Python version:

```bash
uv venv --python 3.10

# if you're not using direnv, you need to manually activate the virtual environment
source .venv/bin/activate
```

* Install the project's dependencies:

```bash
uv sync
```

* Install the [pre-commit](https://pre-commit.com/) hooks:

```bash
pre-commit install
```

**You must make sure that your changes are covered by unit and integration tests, and that it follows the project's stylistic guidelines.** In the absence of the latter, you should mimic the style and patterns in the existing codebase.

### Running tests

You should ensure that all tests are passing. We use `pytest` to write and run tests.
```bash
pytest tests
```

You should also make sure that your changes work with all supported versions of Python and Django. For that, we are using `tox`:
```bash
tox
```

### Formatting and linting

This project uses `ruff` to format and lint code.

Run the lints using `tox`:
```bash
tox -e lint
```

Format the code using `ruff`:
```bash
ruff check --fix
ruff format
```

## Release

Releases are driven by git tags: the package version is derived from the tag
name (via vcs-versioning, no `v` prefix), and pushing a tag triggers the
[release workflow](https://github.com/k-tech-italy/bitcaster-django/blob/master/.github/workflows/release.yml),
which builds the distribution and publishes it to TestPyPI and
[PyPI](https://pypi.org/p/bitcaster-django) using trusted publishing.

To release a new version:

* Make sure the CI is green on `develop`.
* Fast-forward `master` to `develop`:

```bash
git checkout master
git merge --ff-only develop
```

* Tag with the new version number and push:

```bash
git tag <version>  # e.g. git tag 0.4.2
git push origin master <version>
```

* Check that the [release workflow run](https://github.com/k-tech-italy/bitcaster-django/actions/workflows/release.yml)
  completes and that the new version shows up on
  [PyPI](https://pypi.org/p/bitcaster-django).
