# Versioning and releases

MagicEditor uses [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

| Piece | Where | Rule |
|-------|--------|------|
| Version | `src/magiceditor/version.py` `VERSION` | Source of truth. `MAJOR.MINOR.PATCH`, optional `-prerelease` |
| Package | `pyproject.toml` `[project].version` | Same string as `VERSION` |
| Installer | `packaging/inno/MagicEditor.iss` `MyAppVersion` | Same string as `VERSION` |
| Notes | `docs/CHANGELOG.md` | Heading `## [VERSION]` |
| Git tag | `v` + `VERSION` | Example: `v0.9.8` |
| Channel | `version.py` `STAGE` | Display only (`BETA`, `RC1`, or empty). Not part of the semver |

Before **1.0.0**, a minor bump may include breaking changes. From 1.0.0 on:

- **MAJOR** — breaking change
- **MINOR** — backward-compatible feature
- **PATCH** — backward-compatible fix

`STAGE` is the word shown next to the number in the status bar and the About dialog. Leave it empty for a stable release. Do not copy it into `pyproject.toml`.

The in-app list is **Ajuda → Novidades**. It renders `docs/CHANGELOG.md`, which is also packed into the Windows executable.

## Check

```powershell
uv run python scripts/check_release_version.py
uv run python scripts/check_release_version.py --tag v0.9.8
```

The same check runs in GitHub Actions on every push and pull request.

## Bump

```powershell
uv run python scripts/bump_version.py 0.9.9
```

That updates the three version files and inserts an empty `## [0.9.9]` section when the changelog does not have one yet. Fill the bullets, run the check, then commit.

## Publish

GitHub publishes the Windows executable and the Inno installer when a tag is pushed. The workflow is `.github/workflows/release.yml`. It installs the lockfile with `uv sync` and then runs `scripts/build.ps1 -Exe -Inno -SkipDeps`. That script uses the repo `.venv` when PyInstaller is installed there, which is what `uv sync --all-extras` provides on the runner.

```powershell
git tag v0.9.9
git push origin main
git push origin v0.9.9
```

The tag must be exactly `v` plus `VERSION`. The release notes are the matching section of `docs/CHANGELOG.md`.

Local installers stay under `dist/` and are not committed. See [BUILD.md](BUILD.md).
