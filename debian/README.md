# Debian Packaging

This directory documents a minimal `dh-python`/`debuild` workflow for `python-tvheadend`.

## Install Packaging Tooling

```bash
sudo apt update
sudo apt install -y debhelper dh-python devscripts python3-all python3-build python3-installer
```

## Included Packaging Skeleton

This repository now includes these files under `debian/`:

- `control`
- `changelog`
- `rules`
- `source/format`

### debian/control

```debcontrol
Source: python-tvheadend
Section: python
Priority: optional
Maintainer: Chris Allison <chris.charles.allison+tvheadend@gmail.com>
Build-Depends: debhelper-compat (= 13), dh-python, python3-all, python3-build, python3-installer
Standards-Version: 4.7.0
Rules-Requires-Root: no

Package: python3-tvheadend
Architecture: all
Depends: ${misc:Depends}, ${python3:Depends}, python3-requests
Description: Remote access helpers for TVHeadend
 Typed helpers and API wrappers for remote TVHeadend access.
```

### debian/changelog

```changelog
python-tvheadend (0.1.0-1) unstable; urgency=medium

  * Initial Debian package.

 -- Chris Allison <chris.charles.allison+tvheadend@gmail.com>  Sat, 22 Mar 2026 12:00:00 +0000
```

### debian/source/format

```text
3.0 (native)
```

### debian/rules

```make
#!/usr/bin/make -f

%:
	dh $@ --with python3 --buildsystem=pybuild
```

`debian/rules` should be executable (already set in this repo).

## Build The Package

From the project root:

```bash
debuild -us -uc
```

This will produce `.deb` artifacts in the parent directory.
