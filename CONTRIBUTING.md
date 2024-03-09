# Contributing

Assuming you have cloned this repository to your local machine, you can follow these guidelines to make contributions.

Use `pyenv install`, `brew`, or package manager of your choice to install a version of python. The minimum python version is noted in the `pyproject.toml` file.

## Use a virtual environment

```sh
python -m venv .venv
```

This will create a directory `.venv` with python binaries and then you will be able to install packages for that isolated environment.

Next, activate the environment.

```sh
source .venv/bin/activate
```

To check that it worked correctly;

```sh
which python pip
```

You should see paths that use the `.venv/bin` in your current working directory.

## Installing dependencies

Install dependencies.

```sh
pip install -e '.[dev]'
```

Now, you can run `inv -l` to list available tasks. Run `inv all` to make sure you're ready to start developing.
