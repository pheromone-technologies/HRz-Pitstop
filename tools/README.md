# HRz Pitstop tools

These scripts support inventory imports, image processing, catalog generation, and verification. They are not loaded by the storefront.

Run commands from the repository root so their existing relative paths resolve correctly, for example:

```sh
python3 tools/export_excel_to_json.py
```

Keep generated exports and temporary source files under `tools/output/` and `tools/source/`; both directories are ignored by Git.