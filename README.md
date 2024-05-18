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

### Standard GNU/Linux systems
The `python-pptx` is not in the Fedora/Debian repository. It is therefore recommended to install and run the project in a virtual environment. It is safer to purely use a virtual environment, but since I use some packages in other projects too, I prefer using my system package manager whenever possible:
```sh
sudo apt/dnf install python3-flask python3-jinja2 python3-msal python3-requests
python3 -m venv venv --system-site-packages
. ./venv/bin/activate  # every time you run, of course
pip3 install -r requirements.txt
```

Or simply install it into your user directory with `pip`, although this is considered bad practice (see [PEP 0668](https://peps.python.org/pep-0668/)):
```sh
pip3 install --break-system-packages --user python-pptx
```

If you use Guix/NixOS or other "less standard" systems, you are on your own.

### macOS
macOS is not yet supported as the main developer ([Runxi Yu](https://runxiyu.org/)) uses [Asahi Linux](https://asahilinux.org/) and [Debian](https://www.debian.org/).

If you use a manually-installed Python interpreter, using `pip install --user -r requirements.txt` should be safe. I am unsure about how Homebrew manages Python packages or how the Python interpreter preinstalled with the system works. If in doubt, use a virtual environment.

## GitHub Mirror

Because many contributors use GitHub, there is a
[GitHub mirror](https://github.com/runxiyu/sjdb-src)
**which may lag behind the other repositories a little**.
You are advised to send patches to the
[public mailing list](https://lists.sr.ht/~runxiyu/sjdb)
to
[submit patches](https://git-send-email.io)
whenever possible, but if you must use GitHub, you could submit a pull
request, and it will be reviewed sometime.
