"""Configuration file loading."""

import os


def load_config():
    """Load config from .lf-verify.yaml in cwd or home directory."""
    for d in [os.getcwd(), os.path.expanduser("~")]:
        path = os.path.join(d, ".lf-verify.yaml")
        if not os.path.isfile(path):
            continue
        with open(path) as f:
            text = f.read()
        try:
            import yaml
            data = yaml.safe_load(text) or {}
        except ImportError:
            data = {}
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    data[k.strip()] = v.strip()
        allowed = {"region", "profile", "catalog_id", "sso_instance_id"}
        return {k.replace("-", "_"): v for k, v in data.items() if k.replace("-", "_") in allowed and v}
    return {}
