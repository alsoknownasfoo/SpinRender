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


# ---------------------------------------------------------------------------
# Rotation math helpers — translate UI parameters to kicad-cli --rotate X,Y,Z
#
# kicad-cli applies: M = R_X(kx) · R_Y(ky) · R_Z(kz)
# (Z applied first to the board vertex, X applied last)
# ---------------------------------------------------------------------------

def _rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1,0,0],[0,c,-s],[0,s,c]]

def _rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c,0,s],[0,1,0],[-s,0,c]]

def _rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c,-s,0],[s,c,0],[0,0,1]]

def _matmul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def _rodrigues(axis, angle_rad):
    """Rotation matrix for `angle_rad` around unit `axis` (Rodrigues)."""
    ax, ay, az = axis
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    t = 1 - c
    return [
        [t*ax*ax+c,    t*ax*ay-s*az, t*ax*az+s*ay],
        [t*ax*ay+s*az, t*ay*ay+c,    t*ay*az-s*ax],
        [t*ax*az-s*ay, t*ay*az+s*ax, t*az*az+c   ]
    ]

def _euler_xyz_from_matrix(M):
    """
    Decompose rotation matrix M into intrinsic XYZ Euler angles (degrees),
    i.e.  M = R_X(kx) · R_Y(ky) · R_Z(kz).
    Returns (kx_deg, ky_deg, kz_deg).
    """
    # M[row][col] indexing
    sy = max(-1.0, min(1.0, M[0][2]))  # sin(ky), clamped for stability
    ky = math.asin(sy)
    cos_ky = math.cos(ky)
    if abs(cos_ky) > 1e-6:
        kx = math.atan2(-M[1][2], M[2][2])
        kz = math.atan2(-M[0][1], M[0][0])
    else:
        # Gimbal lock: ky = ±90°; set kz=0 and solve for kx.
        # For ky=-90°: M[2][0]=cos(kx-kz), M[2][1]=sin(kx-kz)
        # For ky=+90°: M[2][0]=cos(kx+kz), M[2][1]=-sin(kx+kz)
        if sy < 0:
            kx = math.atan2(M[2][1], M[2][0])
        else:
            kx = math.atan2(-M[2][1], M[2][0])
        kz = 0.0
    return math.degrees(kx), math.degrees(ky), math.degrees(kz)

def compute_kicad_angles(board_tilt, board_roll, spin_tilt, spin_heading, anim_angle_deg):
    """
    Translate SpinRender Universal-Joint parameters for a single animation
    frame into kicad-cli --rotate X,Y,Z angles.
    """
    if spin_tilt == 0.0:
        # Fast path: spin around Z (which is the normal in our aligned model)
        return board_tilt, 0.0, anim_angle_deg + board_roll

    # General path: compute full matrix and decompose
    t = math.radians(spin_tilt)
    h = math.radians(spin_heading)
    
    # Polar axis is Z (matching our aligned mesh normal)
    axis = (math.sin(t)*math.cos(h),
            math.sin(t)*math.sin(h),
            math.cos(t))

    R_spin = _rodrigues(axis, math.radians(anim_angle_deg))
    M = _matmul(_rot_x(math.radians(board_tilt)),
                _matmul(R_spin, _rot_z(math.radians(board_roll))))
    return _euler_xyz_from_matrix(M)

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
    # kicad-cli --rotate mapping:
    #   board_tilt  → kx (static elevation from top-down camera)
    #   spin around Z (spin_tilt=90, spin_heading=90) → kz animates
    PRESETS = {
        'hero': {
            'board_tilt': 45.0,
            'board_roll': -45.0,
            'spin_tilt': 45.0,
            'spin_heading': -135.0,
            'direction': 'ccw',
            'period': 10.0,
            'lighting': 'studio'
        },
        'spin': {
            'board_tilt': 90.0,
            'board_roll': -70.0,
            'spin_tilt': -20.0,
            'spin_heading': 0.0,
            'direction': 'ccw',
            'period': 10.0,
            'lighting': 'studio'
        },
        'flip': {
            'board_tilt': 0.0,
            'board_roll': -180.0,
            'spin_tilt': -90.0,
            'spin_heading': -135.0,
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
        # Create temp directory for frames - use a slightly more persistent name
        # so we can use it for looping preview after render finishes
        temp_dir = tempfile.mkdtemp(prefix='spinrender_frames_')

        try:
            # Generate frames
            frame_count = self.generate_frames(temp_dir)
            if self.canceled:
                # Clean up on cancel
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return None

            # Determine output path
            output_path = self.get_output_path()

            # Save a preview frame before assembly
            preview_frame_path = None
            if frame_count > 0:
                middle_frame = frame_count // 2
                src_frame = os.path.join(temp_dir, f"frame{middle_frame:04d}.png")
                if os.path.exists(src_frame):
                    preview_dir = os.path.join(tempfile.gettempdir(), 'spinrender_preview')
                    os.makedirs(preview_dir, exist_ok=True)
                    preview_frame_path = os.path.join(preview_dir, 'last_render_preview.png')
                    shutil.copy2(src_frame, preview_frame_path)

            # Assemble output based on format
            format_type = self.settings.get('format', 'mp4')
            if self.progress_callback:
                self.progress_callback(frame_count, frame_count, f"ASSEMBLING {format_type.upper()}...")

            if format_type == 'mp4':
                self.assemble_mp4(temp_dir, output_path, frame_count)
            elif format_type == 'gif':
                self.assemble_gif(temp_dir, output_path, frame_count)
            elif format_type == 'png_sequence':
                self.assemble_png_sequence(temp_dir, output_path, frame_count)
                last_frame = os.path.join(output_path, f"frame{frame_count-1:04d}.png")
                if os.path.exists(last_frame):
                    preview_frame_path = last_frame

            # Return output path, preview frame path, and frame dir for looping
            return {
                'output': output_path, 
                'preview': preview_frame_path or output_path,
                'frame_dir': temp_dir,
                'frame_count': frame_count
            }

        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
        # Note: We don't delete temp_dir in finally anymore if successful, 
        # so the UI can loop the frames. The UI will be responsible for 
        # cleaning up previous frame dirs.

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

        if self.progress_callback:
            self.progress_callback(0, frame_count, "INITIALIZING RENDER...")

        # Render each frame
        for i in range(frame_count):
            if self.canceled:
                print("// render canceled by user")
                return i

            output_path = os.path.join(output_dir, f"frame{i:04d}.png")

            # 1. Calculate animation angle for this frame
            raw_angle = i * step_degrees
            anim_angle = raw_angle if direction == 'ccw' else -raw_angle

            # 2. Translate Universal-Joint parameters to kicad-cli --rotate X,Y,Z
            kx, ky, kz = compute_kicad_angles(
                board_tilt, board_roll, spin_tilt, spin_heading, anim_angle
            )
            # kicad-cli's argparser (nargs=0..1) misinterprets a value starting with '-'
            # as a new flag. Normalize kx into [0, 360) so the string never leads with '-'.
            kx = kx % 360.0
            if kx > 359.9999:  # floating-point near-zero wraps to ~360; snap to 0
                kx = 0.0
            rotate_str = f"{kx:.4f},{ky:.4f},{kz:.4f}"

            # Find kicad-cli command
            kicad_cli = find_command('kicad-cli')
            if not kicad_cli:
                raise RuntimeError("kicad-cli not found in PATH or common locations")

            # Build kicad-cli command
            cmd = [
                kicad_cli, 'pcb', 'render',
                '--perspective',
                '--rotate', rotate_str,
                '--zoom', '0.85',
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

                # Update progress with completed frame
                if self.progress_callback:
                    self.progress_callback(i + 1, frame_count, f"RENDERING FRAME {i+1}/{frame_count}", output_path)

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
