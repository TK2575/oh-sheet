#!/usr/bin/env python3
"""CLI tool to test the pipeline with an audio file."""
import json
import sys
import time
import httpx
from pathlib import Path

API_URL = "http://localhost:8000"

def upload_audio(file_path: str) -> dict:
    """Upload an audio file and return the RemoteAudioFile reference."""
    print(f"📤 Uploading {file_path}...")
    with open(file_path, "rb") as f:
        files = {"file": (Path(file_path).name, f)}
        resp = httpx.post(f"{API_URL}/v1/uploads/audio", files=files)
    resp.raise_for_status()
    result = resp.json()
    print(f"✓ Uploaded: {result}")
    return result

def create_job(audio: dict, title: str = "Test", skip_humanizer: bool = True) -> str:
    """Create a job and return the job_id."""
    payload = {
        "audio": audio,
        "title": title,
        "skip_humanizer": skip_humanizer,
    }
    print(f"📋 Creating job with skip_humanizer={skip_humanizer}...")
    resp = httpx.post(f"{API_URL}/v1/jobs", json=payload)
    resp.raise_for_status()
    result = resp.json()
    job_id = result.get("job_id")
    print(f"✓ Job created: {job_id}")
    return job_id

def poll_job(job_id: str, max_polls: int = 120) -> dict:
    """Poll job status until complete."""
    for i in range(max_polls):
        resp = httpx.get(f"{API_URL}/v1/jobs/{job_id}")
        resp.raise_for_status()
        job = resp.json()
        status = job.get("status")
        print(f"[{i+1}/{max_polls}] Status: {status}")

        if status in ("succeeded", "failed"):
            return job

        time.sleep(1)

    raise TimeoutError(f"Job {job_id} did not complete within {max_polls} seconds")

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <audio_file> [--no-skip-humanizer]")
        sys.exit(1)

    audio_file = sys.argv[1]
    skip_humanizer = "--no-skip-humanizer" not in sys.argv

    if not Path(audio_file).exists():
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)

    try:
        # Upload
        audio = upload_audio(audio_file)

        # Create job
        job_id = create_job(audio, title=Path(audio_file).stem, skip_humanizer=skip_humanizer)

        # Poll
        print("\n⏳ Waiting for pipeline to complete...")
        job = poll_job(job_id)

        print(f"\n{'='*60}")
        print(f"Status: {job.get('status')}")
        print(f"Error: {job.get('error', 'None')}")
        print(f"{'='*60}")

        if job.get("status") == "succeeded":
            result = job.get("result", {})
            print(f"✅ Success!")
            print(f"  MusicXML: {result.get('musicxml_uri')}")
            print(f"  MIDI: {result.get('humanized_midi_uri')}")
            print(f"  PDF: {result.get('pdf_uri', 'N/A')}")
        else:
            print(f"❌ Job failed: {job.get('error')}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
