"""
Core rendering engine for SpinRender
Implements the tilted-loop model from the PRD
"""
import subprocess
import os
import shutil
import tempfile
import json
import math
import time
from datetime import datetime
from pathlib import Path

def find_command(cmd):
    """Find a command in PATH or common locations"""
    # Try PATH first
    path = shutil.which(cmd)
    if path:
        return path

    # Common locations for KiCad and FFmpeg
    common_paths = []
    if cmd == 'kicad-cli':
        common_paths = [
            '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli',
            '/usr/local/bin/kicad-cli',
            '/opt/homebrew/bin/kicad-cli'
        ]
    elif cmd == 'ffmpeg':
        common_paths = [
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg'
        ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


class RenderEngine:
    """
    Core rendering engine for SpinRender
    Implements the tilted-loop model from the PRD
    """

    # Preset configurations (Universal Joint model)
    PRESETS = {
        'hero': {
            'board_tilt': 35.0,
            'board_roll': -90.0,
            'spin_tilt': 0.0,
            'spin_heading': 0.0,
            'direction': 'ccw',
            'period': 10.0,
            'lighting': 'studio'
        },
        'spin': {
            'board_tilt': 0.0,
            'board_roll': -90.0,
            'spin_tilt': 0.0,
            'spin_heading': 0.0,
            'direction': 'ccw',
            'period': 10.0,
            'lighting': 'studio'
        },
        'roll': {
            'board_tilt': 0.0,
            'board_roll': 0.0,
            'spin_tilt': 90.0,
            'spin_heading': 0.0,
            'direction': 'ccw',
            'period': 10.0,
            'lighting': 'studio'
        }
    }

    # Lighting presets
    LIGHTING_PRESETS = {
        'studio': {
            'light_side': 0.15,
            'light_side_elevation': 45
        },
        'dramatic': {
            'light_side': 0.3,
            'light_side_elevation': 90
        },
        'soft': {
            'light_side': 0.05,
            'light_side_elevation': 20
        },
        'none': {
            'light_side': 0.0,
            'light_side_elevation': 90
        }
    }

    def __init__(self, board_path, settings, progress_callback=None):
        """
        Initialize render engine

        Args:
            board_path: Path to .kicad_pcb file
            settings: Dict of render settings
            progress_callback: Function(current, total, message)
        """
        self.board_path = board_path
        self.board_dir = os.path.dirname(board_path)
        self.settings = settings
        self.progress_callback = progress_callback
        self.canceled = False

        # Apply preset defaults if using a preset
        if settings.get('preset') in self.PRESETS:
            preset = self.PRESETS[settings['preset']]
            for key, value in preset.items():
                if key not in settings or settings.get('preset') != 'custom':
                    settings.setdefault(key, value)

    def render(self):
        """
        Main render entry point
        Generates frames and assembles final output
        """
        # Create temp directory for frames
        temp_dir = tempfile.mkdtemp(prefix='spinrender_')

        try:
            # Generate frames
            frame_count = self.generate_frames(temp_dir)
            if self.canceled:
                return None

            # Determine output path
            output_path = self.get_output_path()

            # Assemble output based on format
            format_type = self.settings.get('format', 'mp4')
            if self.progress_callback:
                self.progress_callback(frame_count, frame_count, f"// assembling {format_type}...")

            if format_type == 'mp4':
                self.assemble_mp4(temp_dir, output_path, frame_count)
            elif format_type == 'gif':
                self.assemble_gif(temp_dir, output_path, frame_count)
            elif format_type == 'png_sequence':
                self.assemble_png_sequence(temp_dir, output_path, frame_count)

            return output_path

        finally:
            # Clean up temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def cancel(self):
        """Cancel the render process"""
        self.canceled = True

    def generate_frames(self, output_dir):
        """
        Generate individual frames using kicad-cli
        """
        # Calculate frame parameters
        period = float(self.settings.get('period', 10.0))
        fps = 30
        frame_count = int(period * fps)
        step_degrees = 360.0 / frame_count

        # Universal Joint parameters
        board_tilt = float(self.settings.get('board_tilt', 0.0))
        board_roll = float(self.settings.get('board_roll', 0.0))
        spin_tilt = float(self.settings.get('spin_tilt', 0.0))
        spin_heading = float(self.settings.get('spin_heading', 0.0))
        direction = self.settings.get('direction', 'ccw')

        # Get lighting parameters
        lighting = self.settings.get('lighting', 'studio')
        light_params = self.LIGHTING_PRESETS.get(lighting, self.LIGHTING_PRESETS['studio'])

        # Get resolution
        resolution = self.settings.get('resolution', '1920x1080')
        width, height = map(int, resolution.split('x'))

        # Render each frame
        for i in range(frame_count):
            if self.canceled:
                print("// render canceled by user")
                return i

            # Update progress
            if self.progress_callback:
                self.progress_callback(i + 1, frame_count, f"// rendering frame {i+1}/{frame_count}")

            # 1. Calculate animation angle
            angle = (i * step_degrees)
            if direction == 'ccw':
                angle = -angle

            # 2. Translate Universal Joint to KiCad Euler X,Y,Z
            if spin_tilt == 0:
                # Vertical Turntable mode
                kx, ky, kz = board_tilt, angle, board_roll
            elif abs(spin_tilt) == 90:
                # Horizontal Roll mode
                if spin_heading == 0:
                    kx, ky, kz = angle, 0, board_tilt + board_roll
                else:
                    kx, ky, kz = angle, spin_heading, board_tilt + board_roll
            else:
                # Interpolated state
                kx, ky, kz = board_tilt + spin_tilt, angle, board_roll + spin_heading

            rotate_str = f"{kx:.4f},{ky:.4f},{kz:.4f}"

            output_path = os.path.join(output_dir, f"frame{i:04d}.png")

            # Find kicad-cli command
            kicad_cli = find_command('kicad-cli')
            if not kicad_cli:
                raise RuntimeError("kicad-cli not found in PATH or common locations")

            # Build kicad-cli command
            cmd = [
                kicad_cli, 'pcb', 'render',
                '--rotate', rotate_str,
                '--zoom', '0.7',
                '-w', str(width),
                '-h', str(height),
                '--background', 'opaque',
                '--quality', 'high',
                '--light-side', str(light_params['light_side']),
                '--light-side-elevation', str(light_params['light_side_elevation']),
                '-o', output_path,
                self.board_path
            ]

            # Add CLI overrides if specified
            cli_overrides = self.settings.get('cli_overrides', '').strip()
            if cli_overrides:
                cmd.extend(cli_overrides.split())

            # Execute render and pipe output to console
            print(f"> {' '.join(cmd)}")
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Stream output to console
                for line in process.stdout:
                    print(f"  {line.strip()}")
                
                process.wait(timeout=30)
                if process.returncode != 0:
                    raise RuntimeError(f"Frame {i} render failed with exit code {process.returncode}")
                    
            except subprocess.TimeoutExpired:
                process.kill()
                raise RuntimeError(f"Frame {i} render timed out")
            except Exception as e:
                raise RuntimeError(f"Frame {i} render failed: {str(e)}")

        return frame_count

    def assemble_mp4(self, frame_dir, output_path, frame_count):
        """
        Assemble frames into MP4 video using ffmpeg
        """
        ffmpeg = find_command('ffmpeg')
        if not ffmpeg:
            raise RuntimeError("ffmpeg not found in PATH or common locations")

        cmd = [
            ffmpeg,
            '-y',
            '-framerate', '30',
            '-i', os.path.join(frame_dir, 'frame%04d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-profile:v', 'high',
            '-level', '4.1',
            '-crf', '18',
            '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            output_path
        ]

        print(f"> {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, stdout=None, stderr=None, timeout=300)
        except subprocess.CalledProcessError as e:
            raise RuntimeError("MP4 assembly failed. See console output.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("MP4 assembly timed out")

    def assemble_gif(self, frame_dir, output_path, frame_count):
        """
        Assemble frames into GIF using ffmpeg
        """
        ffmpeg = find_command('ffmpeg')
        if not ffmpeg:
            raise RuntimeError("ffmpeg not found in PATH or common locations")

        palette_path = os.path.join(frame_dir, 'palette.png')
        palette_cmd = [
            ffmpeg, '-y', '-framerate', '30',
            '-i', os.path.join(frame_dir, 'frame%04d.png'),
            '-vf', 'palettegen', palette_path
        ]

        print(f"> {' '.join(palette_cmd)}")
        try:
            subprocess.run(palette_cmd, check=True, stdout=None, stderr=None, timeout=60)
        except subprocess.CalledProcessError:
            raise RuntimeError("GIF palette generation failed.")

        gif_cmd = [
            ffmpeg, '-y', '-framerate', '30',
            '-i', os.path.join(frame_dir, 'frame%04d.png'),
            '-i', palette_path,
            '-filter_complex', 'paletteuse',
            output_path
        ]

        print(f"> {' '.join(gif_cmd)}")
        try:
            subprocess.run(gif_cmd, check=True, stdout=None, stderr=None, timeout=300)
        except subprocess.CalledProcessError:
            raise RuntimeError("GIF assembly failed.")

    def assemble_png_sequence(self, frame_dir, output_path, frame_count):
        """
        Copy PNG sequence to output directory
        """
        os.makedirs(output_path, exist_ok=True)
        for i in range(frame_count):
            src = os.path.join(frame_dir, f"frame{i:04d}.png")
            dst = os.path.join(output_path, f"frame{i:04d}.png")
            shutil.copy2(src, dst)

    def get_output_path(self):
        """
        Determine output file/directory path based on settings
        """
        if self.settings.get('output_auto', True):
            timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
            output_base = os.path.join(self.board_dir, "Renders", timestamp)
            os.makedirs(output_base, exist_ok=True)
        else:
            output_base = self.settings.get('output_path', self.board_dir)

        format_type = self.settings.get('format', 'mp4')
        board_name = os.path.splitext(os.path.basename(self.board_path))[0]

        if format_type == 'png_sequence':
            output_path = os.path.join(output_base, board_name)
            os.makedirs(output_path, exist_ok=True)
        else:
            ext = 'mp4' if format_type == 'mp4' else 'gif'
            output_path = os.path.join(output_base, f"{board_name}.{ext}")

        return output_path
