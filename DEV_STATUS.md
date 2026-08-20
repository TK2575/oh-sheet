# Development Status - Docker Setup & Pipeline Issues

## Current Challenge

The Oh Sheet pipeline is now fully containerized and mostly working, but the **engraving stage is failing** due to a fundamental incompatibility between how the arrange/humanize stages generate note durations and music21's MusicXML export capabilities.

### Root Issue

The arrangement stage creates notes with impossibly fine-grained durations (2048th notes) that music21 cannot export to MusicXML format. When local engraving fails, the pipeline falls back to a proprietary remote service (`oh-sheet-ml-pipeline`) which is not available in the open-source setup.

**Error Chain:**
1. Ingest → Transcribe → Arrange stages succeed ✅
2. Skip humanize (`skip_humanizer=true` flag added) ✅
3. Engrave stage fails: MusicXML export rejects "2048th" durations ❌
4. Falls back to remote service (unreachable) ❌
5. Pipeline fails with `MLEngraverTransportError`

### Changes Made This Session

**Docker & Infrastructure:**
- Fixed Python version compatibility (Python 3.12 venv required; 3.14+ lacks PyPI wheels)
- Updated `Dockerfile.dev` with `llvm-dev` system package for llvmlite builds
- Added `require-docker` check to Makefile
- Configured Vite dev server with proper `0.0.0.0` binding for Docker networking
- Fixed Vite proxy to use `orchestrator` service name (Docker DNS)

**Backend Fixes:**
- Added missing `backend.workers.separate` import to fix Celery task registration
- Disabled PDF rendering (`render_pdf=False`) to avoid LilyPond compilation errors
- Added quantization of note durations to 64th notes (attempted fix, incomplete)
- Frontend: Re-enabled audio/MIDI upload UI modes (were disabled for demo day)
- Frontend: Added `skip_humanizer=true` flag to job submission

**Frontend (frontend-v2):**
- Fixed upload response parsing (removed non-existent `body["audio"]` key extraction)
- Added segmented picker for YouTube/Audio/MIDI input modes
- Fixed Vite config for Docker networking

## Quantization Fix Attempt (Session 2026-08-19)

### Root Cause Identified
The arrange stage generates notes with impossibly fine-grained durations (2048th notes ≈ 0.00048828 quarter notes) that music21 cannot export to MusicXML. The error chain:
1. Arrange creates notes with extreme durations
2. `makeMeasures()` / `makeTies()` may further subdivide these
3. music21 export rejects: `Cannot convert "2048th" duration to MusicXML (too short)`

### Fixes Implemented (Multiple Layers)
1. **Pre-build quantization** (`_quantize_durations_before_build`)
   - Quantizes ScoreNote durations to 1/64 quarter notes BEFORE building music21 score
   - Clamps extremes to 1/64 minimum

2. **Post-measureization quantization** (`_quantize_after_measureization`)
   - Runs after `makeMeasures()`/`makeTies()` to catch any durations music21 creates
   - Modifies music21 note objects directly

3. **Safety quantization in MusicXML export** (`_stream_to_musicxml_bytes`)
   - Final fallback to clamp any remaining problematic durations
   - Improved error handling and logging

### Status
- ✅ Unit tests pass (quantization logic works in isolation)
- ❌ End-to-end pipeline still fails with 2048th error
- **Issue**: music21 may be caching or preserving duration representations that bypass our quantization

### Files Changed
- `backend/services/engrave_local.py` — added 3 quantization layers + logging
- `backend/jobs/runner.py` — removed broken quantization code
- `backend/test_quantization.py` — unit test validating quantization logic
- `DEV_STATUS.md` — this file

### Next Steps (If Continuing)
1. **Investigate music21 internals** — determine where "2048th" representation comes from
2. **Quantize in arrange stage** — fix duration calculation before notes reach engrave
3. **Alternative approach** — use MIDI-only output path instead of MusicXML export
4. **Use remote engraver** — configure external MusicXML service if available

## Testing

Created `test_pipeline.py` CLI tool for faster iteration:
```bash
python test_pipeline.py audio.mp3 [--no-skip-humanizer]
```

Avoids UI reload delays; streams job status and shows exact API responses.

## Files Changed

- `Dockerfile.dev` - llvm-dev + improved pip caching
- `Makefile` - frontend Docker target, require-docker check
- `README.md` - Docker-first quick start
- `docker-compose.yml` - Added frontend-v2 Vite dev server
- `backend/jobs/runner.py` - skip_humanizer, quantization, PDF disable
- `backend/services/engrave_local.py` - Attempted quantization fix
- `backend/workers/__init__.py` - Fixed separate task import
- `frontend-v2/src/*.js` - Upload parsing, mode selectors, Vite config
