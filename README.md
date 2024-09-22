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

## Dependencies

Just make a virtual environment and install from `requirements.txt`.

```
python -m venv venv
./venv/bin/activate
pip3 install -r requirements.txt
```

## Configuration

1. Create a build directory somewhere. Change to it as your working directory.
2. Copy `config.example.ini` from the source directory to `config.ini` in the
   build directory and edit it.
3. Run `grant.py` and log in through your browser, if you have not provided
   application consent via Microsoft Entra ID.

## Running

Note that you are expected to be in the build directory when running.

- `generate` builds and sends tomorrow's bulletin
- `generate <YYYY-MM-DD>` builds and sends the bulletin for the specified day

## Maintainers

* Runxi Yu
* Wilson Shu

## Mirrors

* <https://git.runxiyu.org/ykps/sjdb-src.git/>
* <https://git.sr.ht/~runxiyu/sjdb-src/>
* <https://github.com/runxiyu/sjdb-src/>
