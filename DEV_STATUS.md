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

## Next Steps

### Option 1: Find/Use Remote Engraver (Recommended for Quick Win)
- Research free public MusicXML engraver services or open-source alternatives
- Point `OHSHEET_ENGRAVER_SERVICE_URL` env var to the service
- Would allow end-to-end testing with real output

### Option 2: Fix the Quantization Approach
- Current quantization to 64th notes didn't work; may need different granularity
- Could apply quantization earlier (in arrange stage rather than engrave stage)
- Need to investigate if quantization is actually being called or if music21 validates before it runs

### Option 3: Skip Engraving Entirely
- Return minimal MusicXML stub + valid MIDI 
- Fast path to functional pipeline for testing
- Users get MIDI output and can inspect MusicXML structure

### Option 4: Fix the Arrange Stage
- Modify how arrangement generates note durations to avoid sub-64th-note precision
- Most fundamental fix but requires understanding the arrangement algorithm
- Likely involves changes to `backend/services/arrange.py`

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
