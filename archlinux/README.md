# Arch Linux Packaging

This directory contains packaging files for `python-tvheadend`.

## Build Locally

Run from this directory:

```bash
makepkg -si
```

## Refresh .SRCINFO

After editing `PKGBUILD`, regenerate `.SRCINFO`:

```bash
makepkg --printsrcinfo > .SRCINFO
```

## Validate PKGBUILD/.SRCINFO Sync

Use the helper script to verify `.SRCINFO` matches `PKGBUILD`:

```bash
./validate-srcinfo.sh
```

## Typical Update Flow

1. Update `pkgver` / `pkgrel` in `PKGBUILD` as needed.
2. Regenerate `.SRCINFO`.
3. Commit both `PKGBUILD` and `.SRCINFO`.
