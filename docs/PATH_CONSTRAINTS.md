# Path Constraints and Asset Management

> **CRITICAL**: This document defines the operating constraints for CloudCo/Claude Code when building AfroMations.

## Non-Negotiable Constraint

**CloudCo/Claude Code cannot read local Windows paths** such as:
- `E:\...`
- `C:\Users\...`
- `D:\PROJECTS\...`
- Any path not present within the repository workspace

This is a fundamental architectural constraint, not a bug.

---

## Why This Constraint Exists

1. **Security**: Build agents should not have access to arbitrary filesystem locations
2. **Reproducibility**: Builds must be deterministic and work from any environment
3. **CI/CD Compatibility**: Automated pipelines cannot access developer workstations
4. **Multi-platform**: The build must work on Linux containers, macOS, and Windows

---

## The Solution: Repository-Based Asset Management

All assets must be uploaded into the repository (or mounted into the build container) before they can be processed.

### Asset Upload Flow

```
Developer Workstation          Repository                    CloudCo/Builder
─────────────────────         ──────────                    ───────────────
E:\AFROMATIONS\Website\
  afromations_flag_pick.gif
         │
         ├─── upload ──────►  /incoming/
                                 afromations_flag_pick.gif
                                        │
                                        ├─── organize ────►  python tools/organize_assets.py
                                        │                           │
                                        │                           ▼
                              /assets/                       /assets/manifest.json
                                 hero/                       (content-addressable)
                                   afromations_flag_pick.gif
```

### Directory Structure

```
/incoming/          # Raw uploads from developers (git-ignored large files)
/assets/            # Organized, versioned assets
  manifest.json     # Content-addressable asset registry
  hero/             # Hero section assets
  brand/            # Brand assets (logos, colors)
  icons/            # Icon assets
  fonts/            # Typography assets
/tools/
  organize_assets.py  # Asset ingestion and organization script
```

---

## Working with Assets

### Step 1: Upload Assets to `/incoming/`

When referencing local paths like:
```
E:\ACTIVE PROJECTS-PIPELINE\AFROMATIONS\Website\afromations_flag_pick.gif
```

Upload the file to:
```
/incoming/afromations_flag_pick.gif
```

### Step 2: Run the Asset Organizer

```bash
python tools/organize_assets.py \
  --input /incoming \
  --output /assets \
  --manifest /assets/manifest.json
```

This script:
1. Scans `/incoming/` for new files
2. Computes content hashes for deduplication
3. Categorizes assets by type (image, video, document, font)
4. Moves files to appropriate `/assets/` subdirectories
5. Updates `/assets/manifest.json` with metadata

### Step 3: Reference Assets in Code

After organization, reference assets using their manifest path:

```javascript
// Frontend (Next.js)
import heroImage from '@/assets/hero/afromations_flag_pick.gif';

// Or via public path
<Image src="/assets/hero/afromations_flag_pick.gif" alt="AfroMations Hero" />
```

```python
# Backend (Python)
from pathlib import Path
ASSETS_DIR = Path(__file__).parent.parent / "assets"
hero_path = ASSETS_DIR / "hero" / "afromations_flag_pick.gif"
```

---

## Asset Manifest Schema

`/assets/manifest.json`:
```json
{
  "version": "1.0",
  "generated_at": "2024-01-19T12:00:00Z",
  "assets": {
    "hero/afromations_flag_pick.gif": {
      "original_name": "afromations_flag_pick.gif",
      "content_hash": "sha256:abc123...",
      "size_bytes": 1234567,
      "mime_type": "image/gif",
      "category": "hero",
      "uploaded_at": "2024-01-19T11:00:00Z",
      "dimensions": {
        "width": 1920,
        "height": 1080
      }
    }
  }
}
```

---

## What Happens When Local Paths Are Referenced

When the build spec or user input references a local path like:

```
"E:\ACTIVE PROJECTS-PIPELINE\AFROMATIONS\Website\afromations_flag_pick.gif"
```

CloudCo/Claude Code will:

1. **NOT** attempt to read from that path (it's inaccessible)
2. **CREATE** a TODO entry documenting the required asset
3. **GENERATE** instructions for the user to upload the asset
4. **WRITE** a stub/placeholder if the asset is non-blocking
5. **CONTINUE** building with clear documentation of what's missing

### Example TODO Entry

```markdown
## Missing Asset: afromations_flag_pick.gif

**Referenced Path**: E:\ACTIVE PROJECTS-PIPELINE\AFROMATIONS\Website\afromations_flag_pick.gif
**Expected Location**: /incoming/afromations_flag_pick.gif
**Purpose**: Hero section background media

### Upload Instructions:
1. Copy `afromations_flag_pick.gif` to `/incoming/` directory
2. Run: `python tools/organize_assets.py --input /incoming --output /assets`
3. Verify: Check `/assets/manifest.json` for the new entry

### Placeholder:
A gradient placeholder will be used until the asset is provided.
```

---

## Git Configuration for Assets

### Large Files (Git LFS)

For video files and large images, use Git LFS:

```bash
# Track large media files
git lfs track "*.mp4"
git lfs track "*.mov"
git lfs track "*.gif"  # If >10MB
git lfs track "*.psd"
git lfs track "*.ai"
```

### .gitignore for /incoming/

The `/incoming/` directory should be git-ignored for raw uploads:

```gitignore
# Raw upload staging area
/incoming/*
!/incoming/.gitkeep
!/incoming/README.md
```

### /assets/ is Versioned

The organized `/assets/` directory IS committed:

```gitignore
# Assets are versioned
!/assets/
```

---

## Platform-Specific Notes

### Docker Builds

When building in Docker, mount the assets volume:

```yaml
# docker-compose.yml
services:
  web:
    volumes:
      - ./assets:/app/assets:ro
```

### Coolify Deployments

Use Coolify's persistent storage for assets:

```yaml
# coolify.yml
volumes:
  - name: assets
    path: /app/assets
    persistent: true
```

### Railway Deployments

Railway uses the repository's `/assets/` directory directly. Ensure assets are committed before deployment.

---

## Frequently Asked Questions

### Q: Can I use cloud storage URLs instead?

**A**: Yes, for large media files. Store the URL in the manifest:

```json
{
  "hero/afromations_flag_pick.gif": {
    "type": "remote",
    "url": "https://storage.example.com/assets/hero.gif",
    "content_hash": "sha256:abc123..."
  }
}
```

### Q: What about secrets in asset files?

**A**: Never commit assets containing secrets. Use:
- Environment variables for API keys
- Docker secrets for sensitive config
- `.gitignore` for any file that might contain credentials

### Q: How do I handle very large video files?

**A**: Options:
1. Git LFS for files under 2GB
2. External storage (S3, GCS, Cloudflare R2) with manifest URLs
3. Mount volumes in production (not committed to repo)

---

## Summary

| Scenario | Action |
|----------|--------|
| Local path referenced (`E:\...`) | Create TODO + upload instructions |
| Asset uploaded to `/incoming/` | Run organizer script |
| Asset in `/assets/manifest.json` | Safe to reference in code |
| Large file (>50MB) | Use Git LFS or external storage |
| Missing asset at build time | Use placeholder + document |

---

## Related Documents

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment procedures
- [/spec/PRD.json](../spec/PRD.json) - Product requirements
