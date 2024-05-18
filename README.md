# The YK Pao School Songjiang Campus Daily Bulletin

Daily Bulletins are bulletin boards for students and staff at the
Songjiang campus of [YK Pao School](https://ykpaoschool.cn), which are
delivered by email every school day. They contain information such as
itineraries notices, Daily Inspirations, exam schedules (if there are
exam sessions ongoing), the daily menu, etc.

This repository contains the source code of the modern Daily Bulletin's
build system.

- [User-facing web page](https://ykps.runxiyu.org/sjdb/)
- [Canonical code repository](https://git.runxiyu.org/ykps/current/sjdb-src.git/)
  ([sr.ht mirror](https://git.sr.ht/~runxiyu/sjdb-src))
- [Legacy repository](https://git.runxiyu.org/ykps/current/sjdb-legacy.git/)
  ([sr.ht mirror](https://git.sr.ht/~runxiyu/sjdb-legacy))
- [Issue tracker](https://todo.sr.ht/~runxiyu/sjdb)
- [Public mailing list](https://lists.sr.ht/~runxiyu/sjdb)
  for discussions
- [Private support mailing list](mailto:sjdb@runxiyu.org)

## Installation
The `python-pptx` is not in the Fedora/Asahi repository. It is therefore recommended to install and run the project in a virtual environment, though because `python-pptx` doesn't have very strange dependencies, I'd simply use a virtual environment that inherits system site packages:
```sh
sudo dnf install python3-flask python3-jinja2 python3-jinja2-cli python3-msal python3-requests
python3 -m venv venv --system-site-packages
. ./venv/bin/activate  # every time you run, of course
pip3 install -r requirements.txt
```

Or simply install it into your user directory with `pip`, although this is considered back practice:
```sh
pip3 install python-pptx --break-system-packages --user
```



## GitHub Mirror

Because many contributors use GitHub, there is a
[GitHub mirror](https://github.com/runxiyu/sjdb-src)
**which may lag behind the other repositories a little**.
You are advised to send patches to the
[public mailing list](https://lists.sr.ht/~runxiyu/sjdb)
whenever possible, but if you must use GitHub, you could submit a pull
request, and it will be reviewed (although it would be faster if you
just email the patch properly).
