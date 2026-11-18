# Step 1: Check your Mac and install the tools

This step installs the basic developer tools and Python 3.12, then downloads the project code. Run all commands in the **Terminal** app (Applications › Utilities › Terminal), one block at a time.

## 1.1 Which kind of Mac do you have?

```bash
uname -m
```

- `arm64` means **Apple Silicon** (M1/M2/M3/M4…). Both tracks work.
- `x86_64` means **Intel Mac**. Track A works. Track B (Docker/OSRM) won't work with the shared map data, which was built for Apple Silicon only. Do Track A and skip step 4.

Also check that you have at least **2 GB free** for Track A plus Track B (about 200 MB for Track A alone):

```bash
df -h ~
```

## 1.2 Apple's command-line tools (gives you `git`)

```bash
xcode-select --install
```

A window appears. Click **Install** and wait. If it says the tools are already installed, that's fine.

✅ **Check**

```bash
git --version
```

Expected: something like `git version 2.x.x`.

## 1.3 Homebrew (a package installer for macOS)

Skip this if `brew --version` already prints a version.

Go to https://brew.sh, copy the install command shown on that page into Terminal, and follow its prompts. It asks for your Mac password. **At the end it prints "Next steps" with two or three commands to add `brew` to your PATH. Run them.**

✅ **Check**

```bash
brew --version
```

Expected: `Homebrew 4.x.x` or newer.

## 1.4 Python 3.12

The project's environment is pinned to **Python 3.12**. Other versions may fail on recent macOS.

```bash
brew install python@3.12
```

✅ **Check**

```bash
python3.12 --version
```

Expected: `Python 3.12.x`. If `python3.12` is "command not found", see [05_troubleshooting.md](05_troubleshooting.md#python312-not-found).

## 1.5 Clone the repository

The repo is private on GitHub. Ask the owner to add you as a collaborator and accept the email invite first.

Pick a folder for it, for example `~/Documents/Git`:

```bash
mkdir -p ~/Documents/Git
```

```bash
cd ~/Documents/Git
```

Clone it. The simplest way is the GitHub CLI or HTTPS. With HTTPS, git asks you to sign in to GitHub in the browser or with a personal access token:

```bash
git clone https://github.com/vrbabu9000/bluejay-night-ride-optimizer.git
```

```bash
cd bluejay-night-ride-optimizer
```

✅ **Check**

```bash
ls
```

Expected: you see `README.md`, `src`, `tests`, `infra`, `docs`, `requirements-lock.txt`. There is **no** `data` folder yet. That's normal, and it comes in step 2.

## 1.6 (Optional) Claude Code

If you want Claude to guide the rest, install Claude Code (https://claude.com/claude-code) and open this folder in it. Then follow "Doing this with Claude Code" in [README.md](README.md).

**Next:** [02_get_the_data.md](02_get_the_data.md)
