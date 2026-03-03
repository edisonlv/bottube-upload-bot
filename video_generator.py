"""Video generation module using ffmpeg."""
import subprocess
import random
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import json


class VideoGenerator:
    """Generate slideshow videos using ffmpeg."""
    
    # Color schemes for different topics
    COLOR_SCHEMES = {
        'AI Agents': [
            ('#1a1a2e', '#16213e', '#0f3460'),
            ('#0d0d0d', '#1a1a1a', '#2d2d2d'),
            ('#000428', '#004e92', '#004e92'),
        ],
        'RustChain': [
            ('#1a0a00', '#331a00', '#4d2600'),
            ('#0a0a0a', '#1a1a1a', '#ff6b00'),
            ('#000000', '#121212', '#ff4500'),
        ],
        'Blockchain': [
            ('#0a192f', '#112240', '#1d3557'),
            ('#000000', '#0d0d0d', '#00ff88'),
            ('#0f0f23', '#1a1a3e', '#2d2d5e'),
        ],
        'Decentralized Systems': [
            ('#0d1117', '#161b22', '#21262d'),
            ('#1a1a2e', '#16213e', '#0f3460'),
            ('#000000', '#0a0a0a', '#6c5ce7'),
        ],
    }
    
    def __init__(self, config: dict):
        self.config = config
        self.video_config = config.get('video', {})
        self.output_dir = Path(self.video_config.get('output_dir', 'generated'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.duration_per_slide = self.video_config.get('duration_per_slide', 5)
        self.resolution = self.video_config.get('resolution', '1920x1080')
        self.fps = self.video_config.get('fps', 30)
        self.background_music = self.video_config.get('background_music', '')
    
    def _get_color_scheme(self, topic: str) -> Tuple[str, str, str]:
        """Get a random color scheme for the topic."""
        schemes = self.COLOR_SCHEMES.get(topic, self.COLOR_SCHEMES['AI Agents'])
        return random.choice(schemes)
    
    def _generate_slide_video(
        self,
        text: str,
        output_path: str,
        duration: int,
        colors: Tuple[str, str, str],
        resolution: str = '1920x1080'
    ) -> bool:
        """Generate a single slide with text overlay."""
        width, height = resolution.split('x')
        
        # Create gradient background with text
        # Using drawbox for gradient effect and drawtext for text
        filter_complex = (
            f"color=c={colors[0]}:s={resolution}:d={duration}:r={self.fps},"
            f"drawbox=x=0:y=0:w={width}:h={height}:color={colors[1]}@0.5:t=fill,"
            f"drawtext=text='{text}':"
            f"fontsize=72:fontcolor=white:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"shadowcolor=black:shadowx=3:shadowy=3"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', filter_complex,
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-t', str(duration),
            '-r', str(self.fps),
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"Timeout generating slide: {text}")
            return False
        except FileNotFoundError:
            print("ffmpeg not found. Please install ffmpeg.")
            return False
    
    def _concatenate_videos(
        self,
        video_files: List[str],
        output_path: str,
        add_audio: bool = True
    ) -> bool:
        """Concatenate multiple video files into one."""
        if not video_files:
            return False
        
        # Create concat list file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for video_file in video_files:
                f.write(f"file '{video_file}'\n")
            concat_list = f.name
        
        try:
            # Concatenate videos
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list,
                '-c:v', 'libx264',
                '-crf', '23',
                '-preset', 'medium',
                '-pix_fmt', 'yuv420p',
            ]
            
            # Add background music if available
            music_path = Path(self.background_music)
            if add_audio and music_path.exists():
                cmd.extend([
                    '-i', str(music_path),
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-shortest',
                    '-map', '0:v',
                    '-map', '1:a',
                ])
            else:
                cmd.append('-an')  # No audio
            
            cmd.append(output_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("Timeout concatenating videos")
            return False
        except Exception as e:
            print(f"Error concatenating videos: {e}")
            return False
        finally:
            # Clean up concat list
            Path(concat_list).unlink(missing_ok=True)
            # Clean up individual slide files
            for video_file in video_files:
                Path(video_file).unlink(missing_ok=True)
    
    def generate_video(
        self,
        topic: str,
        captions: List[str],
        title: str
    ) -> Optional[str]:
        """
        Generate a slideshow video for a topic.
        
        Args:
            topic: The topic name (e.g., "AI Agents")
            captions: List of captions for slides
            title: Video title (used for filename)
        
        Returns:
            Path to generated video or None if failed
        """
        colors = self._get_color_scheme(topic)
        
        # Select 3-5 random captions
        selected_captions = random.sample(
            captions,
            min(len(captions), random.randint(3, 5))
        )
        
        # Generate individual slide videos
        slide_files = []
        temp_dir = tempfile.mkdtemp()
        
        for i, caption in enumerate(selected_captions):
            slide_path = f"{temp_dir}/slide_{i}.mp4"
            
            if self._generate_slide_video(
                caption,
                slide_path,
                self.duration_per_slide,
                colors,
                self.resolution
            ):
                slide_files.append(slide_path)
            else:
                print(f"Failed to generate slide: {caption}")
        
        if not slide_files:
            print("No slides generated successfully")
            return None
        
        # Generate output filename
        safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in title)
        safe_title = safe_title[:50].strip()
        output_path = self.output_dir / f"{safe_title}.mp4"
        
        # Concatenate slides into final video
        if self._concatenate_videos(slide_files, str(output_path)):
            print(f"Generated video: {output_path}")
            return str(output_path)
        else:
            print("Failed to concatenate slides")
            return None
    
    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
