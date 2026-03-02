#!/usr/bin/env python3
"""Generate a simple video with ffmpeg and upload it to BoTTube."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import requests

DEFAULT_UPLOAD_URL = "https://bottube.ai/api/upload"


def check_ffmpeg_installed() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found in PATH. Please install ffmpeg first.")


def parse_tags(raw_tags: str) -> str:
    # Normalize tags to a comma-separated string accepted by the API.
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    return ",".join(tags)


def run_ffmpeg(cmd: Iterable[str]) -> None:
    try:
        subprocess.run(list(cmd), check=True)
    except subprocess.CalledProcessError as exc:
        joined = " ".join(shlex.quote(part) for part in cmd)
        raise RuntimeError(f"ffmpeg command failed: {joined}") from exc


def make_text_video(output_path: Path, text: str, duration: int, fps: int, size: str) -> None:
    safe_text = text.replace("'", "\\'").replace(":", "\\:")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=black:s={size}:d={duration}:r={fps}",
        "-vf",
        (
            "drawtext="
            "fontcolor=white:"
            "fontsize=48:"
            "x=(w-text_w)/2:"
            "y=(h-text_h)/2:"
            f"text='{safe_text}'"
        ),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def make_slideshow_video(output_path: Path, images: list[Path], image_duration: int, fps: int, size: str) -> None:
    if not images:
        raise ValueError("No images provided for slideshow mode.")

    with tempfile.TemporaryDirectory(prefix="bottube_slideshow_") as tmpdir:
        list_file = Path(tmpdir) / "images.txt"
        with list_file.open("w", encoding="utf-8") as fp:
            for image in images:
                fp.write(f"file '{image.resolve()}'\n")
                fp.write(f"duration {image_duration}\n")
            fp.write(f"file '{images[-1].resolve()}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            f"scale={size}:force_original_aspect_ratio=decrease,pad={size}:(ow-iw)/2:(oh-ih)/2",
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
        run_ffmpeg(cmd)


def upload_video(
    upload_url: str,
    api_key: str,
    video_path: Path,
    title: str,
    description: str,
    tags: str,
) -> requests.Response:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
    }
    data = {
        "title": title,
        "description": description,
        "tags": tags,
    }

    with video_path.open("rb") as video_file:
        files = {
            "video": (video_path.name, video_file, "video/mp4"),
        }
        response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=120)

    return response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and upload videos to BoTTube.")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument(
        "--api-key",
        default=os.getenv("BOTTUBE_API_KEY"),
        help="BoTTube API key (default: env BOTTUBE_API_KEY)",
    )
    parser.add_argument(
        "--upload-url",
        default=DEFAULT_UPLOAD_URL,
        help=f"Upload endpoint (default: {DEFAULT_UPLOAD_URL})",
    )
    parser.add_argument(
        "--output",
        default="output.mp4",
        help="Output video path before upload (default: output.mp4)",
    )

    generation = parser.add_mutually_exclusive_group(required=True)
    generation.add_argument("--text", help="Create a text-based video with this text")
    generation.add_argument(
        "--images",
        nargs="+",
        help="Create an image slideshow from one or more image paths",
    )

    parser.add_argument("--duration", type=int, default=10, help="Text video duration in seconds")
    parser.add_argument(
        "--image-duration",
        type=int,
        default=3,
        help="Seconds each image is shown in slideshow mode",
    )
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--size", default="1280x720", help="Video size WxH (default: 1280x720)")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.api_key:
        parser.error("API key is required. Pass --api-key or set BOTTUBE_API_KEY.")

    check_ffmpeg_installed()

    output_path = Path(args.output).resolve()
    tags = parse_tags(args.tags)

    if args.images:
        image_paths = [Path(p) for p in args.images]
        missing = [str(p) for p in image_paths if not p.exists()]
        if missing:
            parser.error(f"Image files not found: {', '.join(missing)}")
        make_slideshow_video(output_path, image_paths, args.image_duration, args.fps, args.size)
    else:
        make_text_video(output_path, args.text, args.duration, args.fps, args.size)

    response = upload_video(
        upload_url=args.upload_url,
        api_key=args.api_key,
        video_path=output_path,
        title=args.title,
        description=args.description,
        tags=tags,
    )

    if response.ok:
        print("Upload successful")
        try:
            print(response.json())
        except ValueError:
            print(response.text)
        return 0

    print(f"Upload failed with status {response.status_code}", file=sys.stderr)
    print(response.text, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
