# experimental/

Lightweight MITM proxy for degrading modern web content to work on older browsers.

## Requirements

- Python 3.6+
- `openssl` CLI (`apk add openssl` on Alpine/iSH)
- No pip packages — stdlib only

## Usage

```bash
python3 legaproxy.py
```

First run generates a CA certificate at `~/.legaproxy/ca.pem`.
Install this on your device (Settings → General → About → Certificate Trust Settings on iOS).

Then set your device's HTTP proxy to `127.0.0.1:8080` (or the host's IP if running remotely).

## What it does

Intercepts HTTP and HTTPS traffic, transforming responses:

- **CSS:** grid/flex → block, strips custom properties, viewport units → percentages
- **JS:** arrow functions → function expressions, const/let → var, template literals → string concat
- **HTML:** semantic tags → divs, strips `<picture>`/`<source>`, removes module scripts

## Status

This is a skeleton/proof-of-concept. The `degrade_html()` function is where the real work lives and will grow over time as more sites are tested.

Known limitations:
- No chunked transfer encoding support yet
- No gzip/brotli decompression yet
- No connection keep-alive
- JS transformations are regex-based (fragile for complex code)
