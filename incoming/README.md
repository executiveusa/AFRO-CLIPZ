# Asset Upload Staging Directory

This directory is the **staging area** for assets that need to be uploaded from local machines.

## Why This Directory Exists

CloudCo/Claude Code **cannot read local Windows paths** like:
- `E:\ACTIVE PROJECTS-PIPELINE\AFROMATIONS\...`
- `C:\Users\...\Documents\...`

All assets must be uploaded to this directory before they can be processed.

---

## How to Upload Assets

### Method 1: Git (Recommended for Small Files)

```bash
# Copy file to incoming directory
cp /path/to/your/file.gif ./incoming/

# Stage and commit
git add incoming/
git commit -m "Add asset: file.gif"
git push
```

### Method 2: Git LFS (For Large Files >10MB)

```bash
# Track large files with LFS
git lfs track "*.mp4"
git lfs track "*.mov"
git add .gitattributes

# Then add the file
cp /path/to/large-video.mp4 ./incoming/
git add incoming/large-video.mp4
git commit -m "Add large asset: large-video.mp4"
git push
```

### Method 3: Direct Upload via IDE

Most IDEs support drag-and-drop into the file tree. Simply drag files into this `incoming/` folder.

---

## Required Assets (Pending Upload)

The following assets are referenced in the spec but not yet uploaded:

| Asset | Purpose | Original Path | Status |
|-------|---------|---------------|--------|
| `afromations_flag_pick.gif` | Hero section background | `E:\ACTIVE PROJECTS-PIPELINE\AFROMATIONS\Website\` | **PENDING** |

---

## After Uploading

Once assets are in this directory, run the organizer script:

```bash
python tools/organize_assets.py \
  --input ./incoming \
  --output ./assets \
  --manifest ./assets/manifest.json
```

This will:
1. Compute content hashes for deduplication
2. Categorize assets by type
3. Move files to appropriate `/assets/` subdirectories
4. Update the manifest

---

## Directory Rules

- This directory is **git-ignored** (except this README and `.gitkeep`)
- Uploaded files are temporary until organized
- After organization, originals are removed from here
- Large binary files should use Git LFS

---

## Supported File Types

| Category | Extensions |
|----------|------------|
| Images | `.gif`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.svg` |
| Videos | `.mp4`, `.mov`, `.avi`, `.webm`, `.mkv` |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg` |
| Documents | `.pdf`, `.txt`, `.md` |
| Fonts | `.ttf`, `.otf`, `.woff`, `.woff2` |
| Design | `.psd`, `.ai`, `.sketch`, `.fig` |

---

## Questions?

See [/docs/PATH_CONSTRAINTS.md](../docs/PATH_CONSTRAINTS.md) for full documentation on path constraints and asset management.
