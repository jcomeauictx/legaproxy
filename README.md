# Legaproxy

This project stems from my use of older portable devices, which are generally
far cheaper than the latest and greatest pushed by manufacturers. I find it
difficult to impossible to use many webapps and sites due to expired
certificates and use of javascript features that my phones and other devices
don't support.

This application was based on the getting started guide at
<https://docs.docker.com/get-started/>, tutorial at
<https://github.com/docker/getting-started>, and sample app source at
<https://github.com/docker/getting-started-app>, because originally I
thought Babel was my best potential solution to the javascript problem,
and, not wanting to pollute my dev machine with npm ever again, was going
to run it in a Docker image. I'm glad I did, because I learned a lot about
Docker, but decided to code my own JavaScript translator after finding the
ANTLR4 parser project.

## Installing MITM certificate

Chrome/Chromium ignores the CA certificate store whose instructions are
provided at http://mitm.it/. Instead, after downloading the .pem file,
type `chrome://certificate-manager` into the address bar, select 
"Local certificates", "Custom", "Installed by you", and import
the certificate into "Trusted Certificates".

Alternatively, the Makefile attempts to install the certificate by utilizing
the `certutil` program. It works on Debian trixie chromium as of 2026-03.

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
 * for Python2, `pip2 install pyasn1==0.1.3`
