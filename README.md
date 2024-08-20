# The Songjiang Daily Bulletin Build System

[Daily Bulletin Home Page](https://sj.ykps.net/sjdb/)

**Please note that any code presented herein, or any information present on the
Daily Buletin, does not represent the school in its official capacity.
Information provided herein are provided on a best-effort basis by students who
are otherwise unaffiliated with the school administration (and also have a very
busy academic life).**

Daily Bulletins are bulletin boards for students and staff at the
Songjiang campus of [YK Pao School](https://ykpaoschool.cn), which are
delivered by email every school day. They contain information such as
itineraries notices, Daily Inspirations, exam schedules (if there are
exam sessions ongoing), the daily menu, etc.

This repository contains the source code of the modern Daily Bulletin's
build system. It does not contain the actual Daily Bulletins.

## Installation

### Standard GNU/Linux systems

The `python-pptx` is not in the Fedora/Debian repository. It is
therefore recommended to install and run the project in a virtual
environment. It is safer to purely use a virtual environment, but since
I use some packages in other projects too, I prefer using my system
package manager whenever possible:

```sh
sudo apt/dnf install python3-flask python3-jinja2 python3-msal python3-requests
python3 -m venv venv --system-site-packages
. ./venv/bin/activate  # every time you run, of course
pip3 install -r requirements.txt
```

Or simply install it into your user directory with `pip`, although this
is considered bad practice (see
[PEP 0668](https://peps.python.org/pep-0668/)):

```sh
pip3 install --break-system-packages --user python-pptx
```

If you use Guix/NixOS or other "less standard" systems, you are on your
own.

### macOS

macOS is not yet supported but it should work:

If you use a manually-installed Python interpreter, using
`pip install --user -r requirements.txt` should be safe. I am unsure
about how Homebrew manages Python packages or how the Python interpreter
preinstalled with the system works. If in doubt, use a virtual
environment.

## Configuration

1. Copy `config.example.ini` to `config.ini` and edit it.
2. Create a build directory and specify it in `general.build_path`.
3. Create a web token in the daily inspiration web backend and put the
   token in `web_service.token`.
4. Set `credentials.username` and `credentials.password`.
5. Make sure all other configuration options are correct. For example,
   set `general.soffice` to a program that could open PowerPoint files
   and blocks until they are saved and closed.
6. Run `grant.py` and log in through your browser.

## Running

### Running individual scripts

- Every weekend, after *The Week Ahead* has been published, run
  `weekly.py`. This should generate a `week-%s.json` file where `%s` is
  the first school day of next week in `YYYYMMDD`.
- Run `daily.py` a day before each day a bulletin needs to be published.
  This should generate a `day-%s.json` file where `%s` is the next day.
- Run `pack.py` after `daily.py`. This should generate a `sjdb-%s.html`
  file where `%s` is the next day.
- Run `sendmail.py`.

### Running automatically

- `make` builds and sends tomorrow's bulletin
- `make <YYYY-MM-DD>` builds and sends the bulletin for the specified day
- Note that the build script only runs `weekly.py` if the target day is a Monday

## GitHub Mirror

Because many contributors use GitHub, there is a
[GitHub mirror](https://github.com/runxiyu/sjdb-src)
**which may lag behind the other repositories a little**.
You are advised to send patches to the
[public mailing list](https://lists.sr.ht/~runxiyu/sjdb)
to
[submit patches](https://git-send-email.io)
whenever possible, but if you must use GitHub, you could submit a pull
request, and it will be automatically converted and sent to the mailing
list as a patch, by a [Webhook](https://git.runxiyu.org/runxiyu/current/hybrid.git/tree/hybrid.py).
