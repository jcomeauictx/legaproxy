# Legaproxy

This project stems from my use of older portable devices, which are generally
far cheaper than the latest and greatest pushed by manufacturers. I find it
difficult to impossible to use many webapps and sites due to expired
certificates and use of javascript features that my phones and other devices
don't support.

## Installing MITM certificate

Chrome/Chromium ignores the CA certificate store whose instructions are
provided at http://mitm.it/. Instead, after downloading the .pem file,
type `chrome://certificate-manager` into the address bar, select 
"Local certificates", "Custom", "Installed by you", and import
the certificate into "Trusted Certificates".

Alternatively, the Makefile attempts to install the certificate by utilizing
the `certutil` program. It works on Debian trixie chromium as of 2026-03.

## Testing

Since this is intended to run on the devices themselves, it should be
tested on an Alpine image similar to that which runs under the iOS iSH app.
Clone and cd to my `tk-ish-dev` repo, the `docker` subdirectory, and
`make login`, fixing all problems that arise in the process, until you're
sitting at a prompt under the Docker image. Then
cd to ../../legaproxy and `make`. That installs the current `alpine-ish`
branch of mitmproxy, netlib, and pathod to your python3.9 local library and
runs the nosetest suite. Analyze the `tests.log` errors, edit the
appropriate files, and `make` again to test your changes. If you saved
the previous results as tests.log.1, you can compare using
`diff -y <(grep -v '^DEBUG:' tests.log) <(grep -v '^DEBUG:' tests.log.1)`,
expanding your xterm to full screen for easier viewing.

## Developer notes

* You will need to `usermod -a -G docker $USER`. Do this as root before
  logging in as a user and starting xwindows or you will likely have all
  kinds of random frustrations.
* [Installing sshd](https://www.cyberciti.biz/faq/how-to-install-openssh-server-on-alpine-linux-including-docker/) and [also](https://wiki.alpinelinux.org/wiki/Setting_up_a_SSH_server)
* <https://github.com/gliderlabs/docker-alpine/issues/437#issuecomment-494200575>
* <https://dev.to/kazemmdev/building-cross-browser-compatible-web-apps-with-babel-a-step-by-step-guide-5c5h>
* <https://symfonycasts.com/screencast/webpack-encore/postcss-browsers>
* <https://sgom.es/posts/2019-03-06-supporting-old-browsers-without-hurting-everyone/>
* [Use babel from command line](https://babeljs.io/docs/babel-cli)
* [Differences between ES5 and ES6](https://medium.com/sliit-foss/es5-vs-es6-in-javascript-cb10f5fd600c)
* [Some older Debian docker images](https://github.com/madworx/docker-debian-archive)
* [Needs X socket bind-mounted](https://unix.stackexchange.com/a/317533/2769)
* [Building with files outside the context](https://www.baeldung.com/ops/docker-include-files-outside-build-context)
* [Socat to share socket-bound X over TCP](https://askubuntu.com/a/41788/135108)
* [Debugging with jsconsole.com (doesn't work on iPhone 6+, iOS 12.5.7)](https://www.codeblocq.com/2016/03/Remote-JavaScript-debugging-with-jsconsole/)
* [Understanding `docker run`, `docker exec`, and how to keep container running in background](https://linuxhandbook.com/run-docker-container/)
* [`kex_exchange_identification: Connection closed by remote host`](https://github.com/gliderlabs/docker-alpine/issues/437)
* [CMD vs ENTRYPOINT](https://www.cloudbees.com/blog/understanding-dockers-cmd-and-entrypoint-instructions)
* [Configuring babel to convert arrow notation](https://stackoverflow.com/questions/52821427/javascript-babel-preset-env-not-transpiling-arrow-functions-for-ie11)
* [Simple example of using ANTLR parser with Python3](https://github.com/bentrevett/python-antlr-example)
* [Token stream rewriter](https://www.antlr.org/api/Java/org/antlr/v4/runtime/TokenStreamRewriter.html) for replacing `let` and `const` with `var`, converting arrow functions to old-style, etc.
* [ANTLR 4 Reference PDF](https://dl.icdst.org/pdfs/files3/a91ace57a8c4c8cdd9f1663e1051bf93.pdf)
* antlr4 runs way too slowly for realtime processing of javascript. I will
  have to return unprocessed script at first, and process it in the background,
  to be available on reload. (2024-06-05)
* alternatively, can try [async or concurrent methods](https://docs.mitmproxy.org/stable/addons-examples/#nonblocking), to avoid blocking on one long-running parse.
* Need to change storage of retrieved files to use sha256sums as filenames,
  and have the existing directory structure symlink to these files instead.
  This will allow easier retrieval of cached modified scripts. (2024-06-05)
* Need to change capabilities.html to retrieve a report from the browser via
  an xhr, save that information for the useragent hash, and use it to determine
  which js features need to be translated. (2024-06-05)
* Lexing a large-ish (300kb) blob of minimized js takes over 10 minutes in
  Python, and parsing another minute or more. Using
  [C++](https://www.codeproject.com/Articles/5308882/ANTLR-Parsing-and-Cplusplus-Part-1-Introduction)
  or Java should reduce that time.
* My minimized lexer in JavaScript/Python3 is currently failing on string
  interpolations (the `${...}` syntax) that span multiple template strings.
  My first choice was to process the first-pass lexing in reverse, so as to
  insert the post-processed shards into the token strings list in one pass,
  but this discovery nixes that approach. It will have to be done in forward
  order with a state machine, making a multi-level list, then flatten it when
  done. And probably better to move it from the lexer into the parser, but
  not sure about that.
* Don't use "module: commonjs" in .swcrc files. Using CommonJS will emit
  "Object.defineProperty(exports, ...)" which (exports) is undefined and
  causes the whole file to be ignored. Better yet, remove the "module"
  section altogether (?)
* For installing mitmproxy on older iPhones running iSH with python3.9.16:
  use `pip install mitmproxy==9.0.1`. You will need multiple packages
  installed first, include python3-dev and libffi-dev (`sudo apk add` those).
* On iPhone8, `make` hangs during pip build of `maturin`, right after
  "Updating crates.io index"
* Older versions of swc silently ignore `"externalHelpers": false` in .swcrc
  files. Must clone swc from github and build. version SWC 58.0.0 works.
* There are 3 flavors of `which` I know of: `which` itself, `type -p`, a
  shell builtin, and `command -v`. Usually they all work the same, but on
  alpine:3.14.3, inside a Makefile, `type -p` sends output to stderr,
  making a very confusing situation where you see the result but it doesn't
  get assigned to a variable.
* Problem with alpine-ish branch:
  ```
  1dc0c19dd907:~/src/jcomeauictx/legaproxy$ make async
  mitmdump --anticache -z -b 127.0.0.1 -p 8080 -s async.py 2>&1 | tee async.log &
  sleep 10  # allow mitmproxy to start up
  mitmdump: Traceback (most recent call last):
    File "/home/ishuser/.local/lib/python3.9/site-packages/libmproxy/script.py", line 41, in load
      execfile(path, ns, ns)
    File "/home/ishuser/.local/lib/python3.9/site-packages/libmproxy/script.py", line 9, in execfile
      exec(compile(infile.read(), filepath, 'exec'), _globals, _locals)
    File "async.py", line 8, in <module>
      from mitmproxy import http, ctx
  ModuleNotFoundError: No module named 'mitmproxy'
  ```
 * for Python2, `pip2 install pyasn1==0.1.3`, `pip2 install flask==0.5.2`,
   which latter requires werkzeug==0.6.1. there may be newer versions that
   will install but those worked for me on alpine-ish.
   also, `sudo apk install python2-dev` before attempting
   `pip2 install urwid==1.1`; `pip2 install pillow==2.5.3`;
   `pip2 install lxml==3.8.0` worked on a beefy desktop under the
   alpine-ish-dev container, but I'll maybe need a much older version for
   the iphone under iSH.
   `pip2 install mock==3.0.5`; `pip install six==1.7.3`, since 1.5.2 was
   automatically installed by previous packages and it's not enough for
   nosetests.
 * `make PYTHON=python2` just now had the fllowing nosetests results
   on the iphone 8, and it didn't lock up as it's been doing on
   the iphone 6 and docker image on desktop. progress!
    Ran 88 tests in 33.825s
    FAILED (failures=7)
    Ran 155 tests in 175.204s
    FAILED (errors=11, failures=2)
 * previous results were due to missing `urwid` and `requests` modules.
   now installed, still hanging in tests after SSL handshake failed.
 * two hanging tests on python3 were commented out, now 88 + 244 tests are
   being run.
 * hanging test on python2, `test_server.TestHTTPS.test_clientcert`, was
   found to be using a PEM cert in `/tmp/tmp*/rep` that's identical to
   ../mitmproxy/test/data/dercert, an old (2013 expiration) GitHub cert.
   could that be why some of these tests fail or hang?
 * attempting to figure out handshake errors on python2, at the command line
   `t = TestSNI()`, then `t.test_echo()`, getting
   `TestSNI instance has no attribute port`
 * last night (2026-04-12) Claude and I got it working to the point that
   example.com shows up fine in the alpine firefox browser, but other sites
   pop up an error of one kind or another. One bank causes the browser
   to throw `SSL_ERROR_RX_RECORD_TOO_LONG`, a fix for which was found on
   [reddit](https://www.reddit.com/r/firefox/comments/8rilyj/ssl_error_rx_record_too_long/):
    ```
    DrKangaroo
    •
    8y ago
    • Edited 8y ago

    For me the fix was to disable TLS 1.3 for now.

    You can do it by doing this:

        Write to your address bar: about:config

        Search for: security.tls.version.max

        Change the value from 4 to 3.

    Click ok and you should be good to go! The broken sites should start working instantly!

    4 stands for TLS 1.3 and 3 for TLS 1.2
    ```
   but of course, mitmproxy should be handling this, not the browser.
   and, it must be noted, I was not "good to go" after this. it made 
   no discernable difference whatsoever.
 * firefox no longer goes through proxy 2026-04-13:14:50
   I restarted after changing `$(INSTALLED)` to a directory under `$HOME`,
   and firefox no longer abides by the system proxy settings `http_proxy`
   and `https_proxy`. or perhaps it never did, and I forgot setting the
   proxy up manually.
