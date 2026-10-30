# Mounting a Google Drive Folder

Used in Phase 1 (Step 0c) when the user gives a Google Drive folder URL instead of a local path.
rclone mounts the folder as a local read-only filesystem, so files are streamed on demand and the
inspection and conversion code treats them as local files.

## Detect the folder ID

Match any of these URL patterns, with or without query parameters (`?usp=sharing`,
`?resourcekey=...`):
- `https://drive.google.com/drive/folders/<folder_id>`
- `https://drive.google.com/drive/u/<N>/folders/<folder_id>`

The folder ID is the string after `/folders/`.

## Step 1: Install rclone

```bash
which rclone
```

If it is missing:
- macOS: install the precompiled binary from rclone.org. The Homebrew build of rclone does not
  support mounting on macOS (it is fine for `ls`, `copy`, `config` and other commands).
  ```bash
  ARCH=$(uname -m | sed 's/x86_64/amd64/')
  DOWNLOAD_DIR=$(mktemp -d)
  curl -L -o "$DOWNLOAD_DIR/rclone.zip" "https://downloads.rclone.org/rclone-current-osx-${ARCH}.zip"
  unzip -o "$DOWNLOAD_DIR/rclone.zip" -d "$DOWNLOAD_DIR"
  mkdir -p ~/.local/bin
  cp "$DOWNLOAD_DIR"/rclone-*-osx-${ARCH}/rclone ~/.local/bin/rclone
  chmod +x ~/.local/bin/rclone
  ```
  If a Homebrew `rclone` is also installed, call `~/.local/bin/rclone` by its full path for the
  mount command, or put `~/.local/bin` first on `PATH`.
- Linux: `sudo -v ; curl https://rclone.org/install.sh | sudo bash`, or `sudo apt install rclone`.

## Step 2: FUSE (Linux only)

On Linux, `rclone mount` needs FUSE. Check with `which fusermount3 || which fusermount`; if neither
exists, `sudo apt install fuse3`. On macOS, use `rclone nfsmount` (Step 4), which runs its own NFS
server and needs no FUSE.

## Step 3: Configure the Google Drive remote

```bash
rclone listremotes
```

If there is no Drive remote, create one named `gdrive`:
```bash
rclone config create gdrive drive
```

This opens a browser for Google sign-in. Tell the user:
> A browser window will open for you to authorize rclone to access your Google
> Drive. Please sign in with the Google account that has access to the data folder
> and grant permission.

On a machine without a browser, the user runs `rclone config` there, answers `n` when asked
whether to use a web browser, runs `rclone authorize "drive"` on a machine that has a browser,
and pastes the printed token at the `config_token>` prompt.

Check the remote works:
```bash
rclone about gdrive:
```

## Step 4: Mount the folder

Mount outside the conversion repo; source data never goes in the repo. The mount point must be an
empty directory.

```bash
FOLDER_ID="<folder_id from the URL>"
MOUNT_POINT="$HOME/source_data"
mkdir -p "$MOUNT_POINT"

# macOS
rclone nfsmount "gdrive:" "$MOUNT_POINT" \
  --drive-root-folder-id="$FOLDER_ID" \
  --read-only \
  --vfs-cache-mode full \
  --daemon

# Linux
rclone mount "gdrive:" "$MOUNT_POINT" \
  --drive-root-folder-id="$FOLDER_ID" \
  --read-only \
  --vfs-cache-mode full \
  --daemon
```

- `--drive-root-folder-id`: use the shared folder as the root of the remote
- `--read-only`: prevent writes to Google Drive
- `--vfs-cache-mode full`: cache file contents on local disk as they are read, so repeated reads
  during inspection and conversion do not refetch them and readers that seek work normally
- `--daemon`: run in the background

## Step 5: Verify and record the path

```bash
ls "$MOUNT_POINT"
mount | grep "$MOUNT_POINT"
```

Report what is visible:
> I've mounted your Google Drive folder at `~/source_data/`. Here's what I see:
> [file listing]

If the mount is empty or fails, check the folder ID, that the authorized Google account can open
the folder, and that `mount | grep "$MOUNT_POINT"` lists the mount.

Use the absolute mount path (for example `/home/user/source_data`) as the data directory in every
later phase. Generated scripts reference that path or take it as an argument, never the Drive URL.

Record it in `conversion_notes.md`:
```
- Data source: Google Drive (<original_url>) → mounted at <absolute mount path>
```

## Unmounting

Keep the mount until every session is converted and uploaded (end of Phase 9; the batch conversion
can run there together with the upload). Then unmount:
```bash
# macOS (nfsmount)
umount "$HOME/source_data"

# Linux
fusermount3 -u "$HOME/source_data"   # or fusermount -u on systems with FUSE 2
```
