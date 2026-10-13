# HRz Pitstop

Static storefront for HRz motorcycle accessories and riding gear.

## Run locally

The app must be served over HTTP because it loads JSON datasets with `fetch`.

```sh
python3 -m http.server 8000 --directory .
```

Open `http://localhost:8000`.

## Project layout

- `index.html`: storefront entrypoint
- `css/`: application stylesheets
- `js/`: application modules
- `data/`: runtime JSON datasets
- `images/`: curated storefront and bike imagery
- `images_processed/`: product imagery referenced by the catalog
- `tools/`: inventory import, image processing, and verification utilities

There is currently no production deployment configuration or live hostname in this repository. The local HTTP server is the verified host for development.