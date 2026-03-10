#!/usr/bin/env python3
'''
legaproxy - degrade modern web for old browsers

Minimal MITM proxy that intercepts HTTP/HTTPS traffic and transforms
modern HTML/CSS/JS into something older browsers can render.

Dependencies: Python 3.6+, openssl CLI (apk add openssl on Alpine/iSH)
No pip packages required — stdlib only.
'''

import socket
import ssl
import subprocess
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

CA_DIR = os.path.expanduser("~/.legaproxy")
CA_KEY = os.path.join(CA_DIR, "ca.key")
CA_CERT = os.path.join(CA_DIR, "ca.pem")
CERT_CACHE = os.path.join(CA_DIR, "certs")

PROXY_PORT = 8080


def setup_ca():
    '''
    Generate CA cert if it doesn't exist (one-time setup).
    '''
    os.makedirs(CERT_CACHE, exist_ok=True)
    if not os.path.exists(CA_KEY):
        subprocess.run([
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", CA_KEY, "-out", CA_CERT,
            "-days", "3650", "-nodes",
            "-subj", "/CN=LegaProxy CA"
        ], check=True)
        print(f"CA cert created: {CA_CERT}")
        print("Install this on your device to trust HTTPS interception.")


def get_cert_for_host(hostname):
    '''
    Generate and cache a cert for a hostname, signed by our CA.
    '''
    cert_path = os.path.join(CERT_CACHE, f"{hostname}.pem")
    key_path = os.path.join(CERT_CACHE, f"{hostname}.key")
    if not os.path.exists(cert_path):
        # Generate key
        subprocess.run([
            "openssl", "genrsa", "-out", key_path, "2048"
        ], capture_output=True, check=True)

        # Generate CSR
        csr_path = os.path.join(CERT_CACHE, f"{hostname}.csr")
        subprocess.run([
            "openssl", "req", "-new", "-key", key_path,
            "-subj", f"/CN={hostname}", "-out", csr_path
        ], capture_output=True, check=True)

        # Sign with CA, include SAN
        ext = f"subjectAltName=DNS:{hostname}"
        subprocess.run([
            "openssl", "x509", "-req", "-in", csr_path,
            "-CA", CA_CERT, "-CAkey", CA_KEY, "-CAcreateserial",
            "-out", cert_path, "-days", "365",
            "-extfile", "/dev/stdin"
        ], input=ext.encode(), capture_output=True, check=True)
        os.unlink(csr_path)
    return cert_path, key_path


# --- Content transformation ---

def degrade_html(html, content_type=""):
    '''
    Rewrite modern HTML/CSS/JS to something older browsers can handle.
    '''
    text = html
    if isinstance(text, bytes):
        encoding = "utf-8"
        # Try to detect from content-type
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].strip()
        try:
            text = html.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = html.decode("utf-8", errors="replace")

    # --- CSS downgrades ---
    # Replace CSS Grid with block display
    text = re.sub(r'display\s*:\s*grid', 'display: block', text)
    text = re.sub(r'display\s*:\s*flex', 'display: block', text)

    # Remove CSS custom properties (var(--x) -> inherit as fallback)
    text = re.sub(r'var\(--[^)]+\)', 'inherit', text)

    # Strip CSS grid/flex properties
    for prop in ['grid-template-columns', 'grid-template-rows', 'grid-gap',
                 'grid-area', 'grid-column', 'grid-row',
                 'flex-direction', 'flex-wrap', 'justify-content',
                 'align-items', 'flex-grow', 'flex-shrink', 'flex-basis']:
        text = re.sub(rf'{prop}\s*:[^;]+;', '', text)

    # Remove viewport units (vw/vh/vmin/vmax -> approximate)
    text = re.sub(r'(\d+)vw', r'\1%', text)
    text = re.sub(r'(\d+)vh', r'auto', text)

    # --- JS downgrades ---
    # Arrow functions -> function expressions (simple cases)
    # (args) => expr  ->  function(args) { return expr; }
    text = re.sub(
        r'\(([^)]*)\)\s*=>\s*([^{][^;\n,}]+)',
        r'function(\1) { return \2; }',
        text
    )
    # No-paren arrow: x => expr
    text = re.sub(
        r'(?<![.\w])(\w+)\s*=>\s*([^{][^;\n,}]+)',
        r'function(\1) { return \2; }',
        text
    )

    # const/let -> var
    text = re.sub(r'\b(const|let)\s+', 'var ', text)

    # Template literals -> string concat (basic cases)
    def replace_template(m):
        s = m.group(0)[1:-1]  # strip backticks
        parts = re.split(r'\$\{([^}]+)\}', s)
        result = []
        for i, part in enumerate(parts):
            if i % 2 == 0:
                result.append(f'"{part}"')
            else:
                result.append(part)
        return " + ".join(result)

    text = re.sub(r'`[^`]*`', replace_template, text)

    # --- HTML downgrades ---
    # <nav>, <section>, <article>, <main>, <header>, <footer> -> <div>
    for tag in ['nav', 'section', 'article', 'main', 'header', 'footer',
                'aside', 'figure', 'figcaption']:
        text = re.sub(rf'<{tag}(\s|>)', rf'<div\1', text, flags=re.I)
        text = re.sub(rf'</{tag}>', '</div>', text, flags=re.I)

    # Remove <picture>/<source>, keep <img>
    text = re.sub(r'<picture[^>]*>', '', text, flags=re.I)
    text = re.sub(r'</picture>', '', text, flags=re.I)
    text = re.sub(r'<source[^>]*/?>', '', text, flags=re.I)

    # Strip module scripts, keep regular ones
    text = re.sub(r'<script[^>]*type=["\']module["\'][^>]*>.*?</script>',
                  '', text, flags=re.I | re.DOTALL)

    if isinstance(html, bytes):
        return text.encode(encoding, errors="replace")
    return text


# --- Proxy handler ---

class ProxyHandler(BaseHTTPRequestHandler):

    def do_CONNECT(self):
        '''
        Handle HTTPS CONNECT tunneling with MITM.
        '''
        host, port = self.path.split(":")
        port = int(port)

        # Tell client tunnel is established
        self.send_response(200, "Connection Established")
        self.end_headers()

        # Generate cert for this host
        cert_path, key_path = get_cert_for_host(host)

        # Wrap client connection with our fake cert
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert_path, key_path)

        try:
            client_ssl = ctx.wrap_socket(self.connection, server_side=True)
        except ssl.SSLError:
            return

        # Now read the actual HTTP request from the TLS stream
        self._handle_mitm(client_ssl, host, port)

    def _handle_mitm(self, client_sock, host, port):
        '''
        Read request from MITM'd connection, fetch upstream, transform.
        '''
        try:
            data = client_sock.recv(65536)
            if not data:
                return

            # Connect to real server
            upstream = socket.create_connection((host, port))
            ctx = ssl.create_default_context()
            upstream_ssl = ctx.wrap_socket(upstream, server_hostname=host)

            # Forward request
            upstream_ssl.sendall(data)

            # Read response
            response = b""
            while True:
                chunk = upstream_ssl.recv(65536)
                if not chunk:
                    break
                response += chunk
            upstream_ssl.close()

            # Split headers and body
            if b"\r\n\r\n" in response:
                head, body = response.split(b"\r\n\r\n", 1)
                content_type = ""
                for line in head.split(b"\r\n"):
                    if line.lower().startswith(b"content-type:"):
                        content_type = line.decode("utf-8", errors="replace")

                # Transform if HTML/CSS/JS
                if any(t in content_type.lower() for t in
                       ["text/html", "text/css", "javascript"]):
                    body = degrade_html(body, content_type)
                    # Fix content-length
                    head = re.sub(
                        rb'(?i)content-length:\s*\d+',
                        f'Content-Length: {len(body)}'.encode(),
                        head
                    )

                client_sock.sendall(head + b"\r\n\r\n" + body)
            else:
                client_sock.sendall(response)

        except Exception as e:
            print(f"MITM error: {e}")
        finally:
            client_sock.close()

    def do_GET(self):
        '''
        Handle plain HTTP proxy requests.
        '''
        self._proxy_request("GET")

    def do_POST(self):
        self._proxy_request("POST")

    def _proxy_request(self, method):
        '''
        Fetch upstream HTTP, transform, return.
        '''
        url = urlparse(self.path)
        try:
            upstream = socket.create_connection((url.hostname, url.port or 80))

            # Reconstruct request
            path = url.path or "/"
            if url.query:
                path += "?" + url.query
            req = f"{method} {path} HTTP/1.1\r\nHost: {url.hostname}\r\n"

            # Forward headers (skip proxy ones)
            for key, val in self.headers.items():
                if key.lower() not in ('proxy-connection',
                                       'proxy-authorization'):
                    req += f"{key}: {val}\r\n"
            req += "\r\n"

            # Forward body if present
            upstream.sendall(req.encode())
            if 'Content-Length' in self.headers:
                body_len = int(self.headers['Content-Length'])
                upstream.sendall(self.rfile.read(body_len))

            # Read response
            response = b""
            while True:
                chunk = upstream.recv(65536)
                if not chunk:
                    break
                response += chunk
            upstream.close()

            # Transform and forward
            if b"\r\n\r\n" in response:
                head, body = response.split(b"\r\n\r\n", 1)
                content_type = ""
                for line in head.split(b"\r\n"):
                    if line.lower().startswith(b"content-type:"):
                        content_type = line.decode("utf-8", errors="replace")

                if any(t in content_type.lower() for t in
                       ["text/html", "text/css", "javascript"]):
                    body = degrade_html(body, content_type)
                    head = re.sub(
                        rb'(?i)content-length:\s*\d+',
                        f'Content-Length: {len(body)}'.encode(),
                        head
                    )

                self.wfile.write(head + b"\r\n\r\n" + body)
            else:
                self.wfile.write(response)

        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

    def log_message(self, format, *args):
        print(f"[proxy] {args[0]}")


if __name__ == "__main__":
    setup_ca()
    print(f"LegaProxy starting on :{PROXY_PORT}")
    print(f"Install CA cert from: {CA_CERT}")
    server = HTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    server.serve_forever()
