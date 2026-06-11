<!-- Generated: 2026-06-10 | Maintainer: SpinRender Team -->

# Release Process Guide

Step-by-step process for cutting a SpinRender release: version bump, PCM zip,
GitHub release, and the KiCad PCM addons-repo metadata MR.

`build/` is gitignored — it's a local staging/scratch area. Nothing in this
guide depends on committed build scripts; everything is reproduced manually
following the steps below.

---

## 1. Version bump

Bump the version in **both** places, in the same commit (or back-to-back
commits before tagging):

- `SpinRender/__init__.py` → `__version__ = "X.Y.Z"`
- `pyproject.toml` → `version = "X.Y.Z"`

The tag (step 4) must point at a commit where **both** files already show the
new version. If you tag before bumping, or bump in two separate commits and
tag the first one, the PCM zip will ship a stale `__version__` — this is
exactly what went wrong with the first v0.8.0 attempt (zip reported
`0.7.0-beta`).

---

## 2. Build the PCM zip

The zip layout is **flat**: `plugins/`, `resources/`, and `metadata.json` at
the zip root (NOT nested under a `SpinRender/` folder — that was the 0.6→0.7
packaging fix and must not regress).

```bash
# 1. Sync current source into the staging dir, renaming SpinRender/ -> plugins/
rsync -a --delete \
  --exclude='__pycache__' --exclude='logs' --exclude='.DS_Store' \
  SpinRender/ build/pcm/plugins/

# 2. Sanity check: should print the NEW version, and diff should be empty
grep __version__ build/pcm/plugins/__init__.py
diff -rq SpinRender build/pcm/plugins --exclude=__pycache__ --exclude=logs --exclude=.DS_Store

# 3. Zip it (run from build/pcm/)
cd build/pcm
rm -f ../sr-pcm-XYZ.zip   # XYZ = version with no dots, e.g. 0.8.0 -> 080
zip -rq -X ../sr-pcm-XYZ.zip plugins resources metadata.json \
  -x '*.DS_Store' -x '*__pycache__*'
cd ../..

# 4. Compute the values needed for the addons-repo metadata MR (step 5)
shasum -a 256 build/sr-pcm-XYZ.zip                 # download_sha256
stat -f%z build/sr-pcm-XYZ.zip                     # download_size
find build/pcm -type f -exec stat -f%z {} \; | awk '{s+=$1} END {print s}'  # install_size
```

`build/pcm/resources/icon.png` and `build/pcm/metadata.json` are hand-curated
and persist between releases — only update `metadata.json`'s `versions` array
and `description_full` (see step 3).

### ⚠️ `build/pcm/metadata.json` must list exactly ONE version

This is the package's **own** metadata, bundled inside the zip. KiCad's PCM
validator rejects it if `versions` has more than one entry:

```json
"versions": [
    {
        "version": "0.8.0",
        "status": "stable",
        "kicad_version": "9.0"
    }
]
```

Do **not** copy the multi-version array from the addons-repo index here — that
multi-version array (with `download_sha256`/`download_size`/`install_size`)
belongs only in the addons-repo `packages/.../metadata.json` (step 5).

### ⚠️ Tag naming rules (PCM v2 schema)

Every string in `metadata.json`'s `tags` array must match
`^[a-z][-a-z0-9]{0,48}[a-z0-9]$` — i.e. **must start with a lowercase letter**.
Tags like `3d` are invalid (starts with a digit) and will fail the addons-repo
validation pipeline. Use `three-d` or drop it.

---

## 3. Update root `metadata.json` (optional, repo copy)

The repo-root `metadata.json` is a reference copy and isn't what KiCad's PCM
actually serves (that comes from the addons-repo index, step 5). Keep it in
sync with `build/pcm/metadata.json`'s single-version entry + description/tags
if you want it to reflect the latest release, but it's not load-bearing.

---

## 4. GitHub release

```bash
# Tag the version-bump commit (must have BOTH __init__.py and pyproject.toml updated)
git tag vX.Y.Z <commit-sha>
git push origin vX.Y.Z

# Create the release with the zip, labeled for readability
gh release create vX.Y.Z \
  "build/sr-pcm-XYZ.zip#SpinRender PCM Build (sr-pcm-XYZ.zip)" \
  --title "SpinRender X.Y.Z" \
  --notes-file build/RELEASE_NOTES_XYZ.md
```

If you need to redo a release (wrong zip, wrong tag commit, etc.):

```bash
gh release delete vX.Y.Z --cleanup-tag --yes   # deletes both release + tag, remote + local-on-push
git tag -d vX.Y.Z                               # clean up local tag if it lingers
```

### Release notes format

Match the style of `build/RELEASE_NOTES_070b.md` / `build/RELEASE_NOTES_080.md`:

```markdown
# SpinRender vX.Y.Z

## Highlights

### <emoji> <Theme 1>
- Bullet points, **bold** for key terms, `code` for flags/files/identifiers.
- Group related changes from multiple commits into one bullet.

### <emoji> <Theme 2>
...

## Install
- **PCM:** Plugin and Content Manager → search "SpinRender".
- **Manual:** download `sr-pcm-XYZ.zip` and install via PCM's "Install from File…", or use `install.sh` / `install.bat` from a clone.

**Full changelog:** https://github.com/alsoknownasfoo/SpinRender/compare/vPREV...vX.Y.Z
```

To find what's changed since the last tag:

```bash
git log --format="%s" vPREV..HEAD | grep -v "^chore\|^debug\|^Merge\|^fix(tests)"
```

Group commits thematically (e.g. "Windows support", "Theming & dialog fixes",
"Stability & crash fixes") rather than listing them 1:1 — the goal is a
human-readable changelog, not a commit dump. Every release should get this
treatment, even "minor" ones — a one-line release body (e.g. "windows support
and various bug fixes") is not acceptable.

---

## 5. KiCad PCM addons-repo metadata MR

The official addon index lives at `kicad/addons/metadata` (project ID
`29185721`), under `packages/com.alsoknownasfoo.spinrender/metadata.json`.
We submit changes via a draft MR from our fork `alsoknownasfoo/metadata`
(project ID `82894976`).

### Auth

`glab` is pre-authenticated as `alsoknownasfoo`. Verify with:

```bash
glab auth status
```

### Step A — fetch upstream's current file

Get the current `versions` array and other fields from upstream `main` (don't
assume your fork's `main` is up to date — it often lags):

```bash
glab api "projects/29185721/repository/branches/main"   # get HEAD sha
glab api "projects/29185721/repository/files/packages%2Fcom.alsoknownasfoo.spinrender%2Fmetadata.json/raw?ref=main"
```

### Step B — create branch + commit on the fork

Use the upstream HEAD sha as `start_sha` (the fork shares an object pool with
upstream, so this works even if the fork's branches are stale — no need to
sync the fork first):

```bash
cat > /tmp/commit_XYZ.json << 'EOF'
{
  "branch": "spinrender-X.Y.Z",
  "start_sha": "<upstream main HEAD sha>",
  "commit_message": "spinrender X.Y.Z",
  "actions": [
    {
      "action": "update",
      "file_path": "packages/com.alsoknownasfoo.spinrender/metadata.json",
      "content": "<full new metadata.json as an escaped JSON string>"
    }
  ]
}
EOF
glab api projects/82894976/repository/commits --method POST --input /tmp/commit_XYZ.json
```

The new `metadata.json` content:
- **Prepend** a new version entry to the existing `versions` array (newest
  first), keeping all prior entries intact.
- New entry needs `version`, `status`, `kicad_version`, `download_sha256`,
  `download_size`, `download_url`, `install_size` — all computed in step 2.
- Update `description_full` / `tags` / etc. only if they're actually changing
  for this release — otherwise carry over verbatim from upstream.
- Re-check every tag against the `^[a-z][-a-z0-9]{0,48}[a-z0-9]$` regex before
  submitting.

### Step C — open the draft MR

```bash
cat > /tmp/mr_XYZ.json << EOF
{"source_branch": "spinrender-X.Y.Z", "target_branch": "main", "target_project_id": 29185721, "title": "Draft: spinrender X.Y.Z", "description": "new release. updating the metadata to point at X.Y.Z.", "remove_source_branch": true}
EOF
glab api projects/82894976/merge_requests --method POST -H "Content-Type: application/json" --input /tmp/mr_XYZ.json
```

Note: `-H "Content-Type: application/json"` is **required** for this call —
without it `glab api` sends an empty content-type and GitLab returns
HTTP 415.

### Step D — watch the validation pipeline

```bash
glab api "projects/82894976/repository/commits/<sha>/statuses?all=true"
```

Two pipelines run per push: `validate-push` (on the fork) and `validate-merge`
(on the MR). Both must report `success`. On failure, get the trace:

```bash
glab api "projects/82894976/pipelines/<pipeline_id>/jobs"
glab api "projects/82894976/jobs/<job_id>/trace" | tail -c 2000
```

### Common validation failures

| Error | Cause | Fix |
|---|---|---|
| `'<tag>' does not match '^[a-z][-a-z0-9]{0,48}[a-z0-9]$'` | A tag starts with a digit or uppercase, or has invalid chars | Remove or rename the tag (e.g. drop `3d`) |
| `Version X.Y.Z: metadata in package must have exactly one version` | The **zip's** `metadata.json` has multiple entries in `versions` | Fix `build/pcm/metadata.json` to a single-entry `versions` array, rebuild the zip, re-upload, update the MR's sha256/size |

### Fixing a failed pipeline (already-open MR)

Push another commit to the same branch — same `commits` API call as step B
but with `"branch": "spinrender-X.Y.Z"` and no `start_sha` (it already
exists). If the zip itself needed to change, redo step 2 fully (rebuild,
recompute hash/size, `gh release upload` to replace the asset) before pushing
the metadata fix, so the sha256 in the MR matches the live asset.

---

## Quick checklist

- [ ] `SpinRender/__init__.py` and `pyproject.toml` both bumped, same commit
- [ ] `build/pcm/plugins/` re-synced from `SpinRender/` (rsync --delete)
- [ ] `build/pcm/plugins/__init__.py` shows the new version
- [ ] `build/pcm/metadata.json` has exactly **one** entry in `versions`
- [ ] All tags match `^[a-z][-a-z0-9]{0,48}[a-z0-9]$`
- [ ] Zip is flat (`plugins/`, `resources/`, `metadata.json` at root) — diff file count/paths against the previous release's zip as a sanity check
- [ ] Tag points at the version-bump commit; GitHub release created with rich, themed notes
- [ ] Addons-repo MR opened as draft from `alsoknownasfoo/metadata` against `kicad/addons/metadata`, with correct sha256/size/install_size
- [ ] Both `validate-push` and `validate-merge` pipelines green before flipping MR out of draft
