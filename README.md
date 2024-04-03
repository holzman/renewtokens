# renewtokens

This is a server extension that regularly fetches the oAuth tokens available from the JupyterHub auth_state and
stores them in the file pointed to by BEARER_TOKEN_FILE.

This code was taken from https://github.com/swan-cern/jupyter-extensions/SwanOAuthRenew and modified to work for
a general JHub installation.

## Install

```bash
pip install git+https://github.com/holzman/renewtokens
```

## Usage

Configure the server extension to load when the notebook server starts

```bash
 jupyter serverextension enable --py --user renewtokens
```

