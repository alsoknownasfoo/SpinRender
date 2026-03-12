"""
SpinRender 3D Preview System
Implements 3D GLB file preview with OpenGL
"""
import wx
import wx.glcanvas as glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np
import trimesh
import math
import time
import threading
import subprocess
import os
import tempfile
from pathlib import Path

# Global flag to ensure glutInit is only called once per session
if '_SPINRENDER_GLUT_INIT' not in globals():
    _SPINRENDER_GLUT_INIT = False


class PCBModelLoader:
    """
    Loads and processes 3D models from KiCad PCBs
    """

    @staticmethod
    def export_glb(board_path, output_path):
        try:
            kicad_cli = None
            common_paths = ['kicad-cli', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli', '/usr/local/bin/kicad-cli', '/opt/homebrew/bin/kicad-cli']
            for path in common_paths:
                try:
                    subprocess.run([path, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False)
                    kicad_cli = path
                    break
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            if not kicad_cli:
                return False
            cmd = [kicad_cli, 'pcb', 'export', 'glb', '--fuse-shapes', '--grid-origin', '--no-dnp', '--subst-models', '--include-pads', '--include-silkscreen', board_path, '--output', output_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, text=True)
            return result.returncode == 0 and os.path.exists(output_path)
        except Exception:
            return False

    @staticmethod
    def load_glb_mesh(glb_path):
        try:
            scene = trimesh.load(glb_path)
            if isinstance(scene, trimesh.Scene):
                if not scene.geometry:
                    return None
                mesh = scene.to_mesh()
            else:
                mesh = scene
            
            # Align mesh with KiCad base orientation (Top-down view at 0,0,0)
            # Match parity test: Rotate +90 around X to bring face-up
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [1, 0, 0]))

            # Auto-scale from meters to mm if needed
            if np.max(mesh.extents) < 1.0:
                mesh.apply_scale(1000.0)
                
            return mesh
        except Exception:
            return None


class GLPreviewRenderer(glcanvas.GLCanvas):
    """
    OpenGL-accelerated 3D preview renderer - Feature Edge Style
    """

    def __init__(self, parent, board_path):
        attribs = [glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24, 0]
        super().__init__(parent, attribList=attribs)
        self.board_path = board_path
        self.context = glcanvas.GLContext(self)
        self.initialized = False
        self.mesh_data = None
        
        # Universal Joint Parameters
        self.rotation_angle = 0.0
        self.board_tilt = 0.0
        self.board_roll = 0.0
        self.spin_tilt = 0.0
        self.spin_heading = 0.0
        
        self.rotation_speed = 1.2
        self.direction_sign = 1.0  # 1.0 for CCW, -1.0 for CW
        self.playing = False

        # Computed Axis
        self.rotation_axis = np.array([0.0, 1.0, 0.0])
        self._update_rotation_axis()

        self.model_center = np.array([0.0, 0.0, 0.0])
        self.model_size = 150.0
        self.loading_state = "exporting"

        # Target aspect ratio for WYSIWYG preview
        self.target_aspect_ratio = 16.0 / 9.0  # Default to 1920x1080

        # Live Frame Preview State
        self.preview_texture = None
        self.has_texture = False

        # Callback for when model finishes loading
        self.on_model_loaded = None

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)
        self.loading_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_loading_timer, self.loading_timer)
        self.loading_timer.Start(50)
        wx.CallAfter(self._start_loading_thread)

    def _start_loading_thread(self):
        threading.Thread(target=self._export_and_load_sync, daemon=True).start()

    def _on_loading_timer(self, _event):
        if self.loading_state:
            self.Refresh()
        else:
            self.loading_timer.Stop()

    def _export_and_load_sync(self):
        try:
            # 1. Determine Cache Path based on file timestamp
            mtime = int(os.path.getmtime(self.board_path))
            stem = Path(self.board_path).stem
            cache_dir = os.path.join(tempfile.gettempdir(), "SpinRender_Cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            glb_path = os.path.join(cache_dir, f"{stem}_{mtime}.glb")
            
            # Cleanup old versions of this board from cache
            try:
                for f in os.listdir(cache_dir):
                    if f.startswith(f"{stem}_") and f.endswith(".glb") and f != f"{stem}_{mtime}.glb":
                        try: os.remove(os.path.join(cache_dir, f))
                        except: pass
            except: pass
            
            # 2. Check if valid cache exists
            if os.path.exists(glb_path):
                print(f"[SpinRender] Using cached GLB: {glb_path}")
                mesh = PCBModelLoader.load_glb_mesh(glb_path)
                if mesh:
                    wx.CallAfter(self._set_mesh, mesh)
                    return

            # 3. Otherwise Export
            print(f"[SpinRender] Cache miss or invalid. Exporting GLB: {glb_path}")
            if PCBModelLoader.export_glb(self.board_path, glb_path):
                mesh = PCBModelLoader.load_glb_mesh(glb_path)
                if mesh:
                    wx.CallAfter(self._set_mesh, mesh)
                else:
                    wx.CallAfter(self._update_loading, None)
            else:
                wx.CallAfter(self._update_loading, None)
        except Exception as e:
            print(f"[SpinRender] Sync Error: {e}")
            wx.CallAfter(self._update_loading, None)

    def _update_loading(self, state):
        self.loading_state = state
        self.Refresh()

    def _update_rotation_axis(self):
        """
        Compute the 3D rotation axis vector based on SPIN TILT and SPIN HEADING.
        Treat Z as the normal (polar axis) to match KiCad translation parity.
        """
        t = math.radians(self.spin_tilt)
        h = math.radians(self.spin_heading)
        
        # Spherical coordinates with Z as vertical
        x = math.sin(t) * math.cos(h)
        y = math.sin(t) * math.sin(h)
        z = math.cos(t)
        
        self.rotation_axis = np.array([x, y, z])
        norm = np.linalg.norm(self.rotation_axis)
        if norm > 0:
            self.rotation_axis /= norm

    def set_universal_joint_parameters(self, board_tilt, board_roll, spin_tilt, spin_heading):
        self.board_tilt = board_tilt
        self.board_roll = board_roll
        self.spin_tilt = spin_tilt
        self.spin_heading = spin_heading
        self._update_rotation_axis()
        self.Refresh()

    def _set_mesh(self, mesh):
        try:
            mesh.process(validate=True)
        except Exception:
            if hasattr(mesh, 'merge_vertices'):
                mesh.merge_vertices()
        
        bounds = mesh.bounds
        self.model_center = (bounds[0] + bounds[1]) / 2
        self.model_size = np.linalg.norm(bounds[1] - bounds[0])
        
        try:
            sharp_mask = mesh.face_adjacency_angles > 0.52
            sharp_edges = mesh.face_adjacency_edges[sharp_mask]
            try:
                boundary_edges = mesh.edges_unique[mesh.edges_unique_count == 1]
            except Exception:
                boundary_edges = mesh.edges_boundary if hasattr(mesh, 'edges_boundary') else []
            
            if len(sharp_edges) > 0 and len(boundary_edges) > 0:
                edges = np.vstack([sharp_edges, boundary_edges])
            elif len(sharp_edges) > 0:
                edges = sharp_edges
            else:
                edges = boundary_edges
                
            if len(edges) == 0:
                edges = mesh.edges_unique
        except Exception:
            edges = mesh.edges_unique
        
        line_vertices = mesh.vertices[edges].reshape(-1, 3)
        self.mesh_data = {'vertices': line_vertices.astype(np.float32), 'count': len(line_vertices)}

        self.loading_state = None
        self.Refresh()

        # Notify that model has finished loading
        if self.on_model_loaded:
            wx.CallAfter(self.on_model_loaded)

    def init_gl(self):
        if self.initialized:
            return
        self.SetCurrent(self.context)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glDisable(GL_CULL_FACE)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_LIGHTING)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.2)
        glClearColor(0.04, 0.04, 0.04, 1.0)
        self.initialized = True

    def on_paint(self, _event):
        size = self.GetSize()
        scale = self.GetContentScaleFactor()
        w, h = int(size.x * scale), int(size.y * scale)
        if w == 0 or h == 0:
            return
        self.SetCurrent(self.context)
        self.init_gl()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, w, h)

        if self.has_texture:
            # Draw Rendered Frame Texture Overlay with Aspect Ratio Preservation
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, w, h, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            # Calculate aspect ratios
            viewport_aspect = float(w) / float(h) if h > 0 else 1.0

            # Get texture dimensions if available
            if hasattr(self, 'texture_width') and hasattr(self, 'texture_height'):
                texture_aspect = float(self.texture_width) / float(self.texture_height) if self.texture_height > 0 else 1.0
            else:
                texture_aspect = viewport_aspect

            # Calculate letterbox/pillarbox dimensions
            if texture_aspect > viewport_aspect:
                # Texture is wider - add letterbox (black bars top/bottom)
                display_width = w
                display_height = w / texture_aspect
                offset_x = 0
                offset_y = (h - display_height) / 2
            else:
                # Texture is taller - add pillarbox (black bars left/right)
                display_height = h
                display_width = h * texture_aspect
                offset_x = (w - display_width) / 2
                offset_y = 0

            # Draw black background
            glColor4f(0, 0, 0, 1)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(w, 0)
            glVertex2f(w, h)
            glVertex2f(0, h)
            glEnd()

            # Draw texture with correct aspect ratio
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.preview_texture)
            glColor4f(1, 1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(offset_x, offset_y)
            glTexCoord2f(1, 0); glVertex2f(offset_x + display_width, offset_y)
            glTexCoord2f(1, 1); glVertex2f(offset_x + display_width, offset_y + display_height)
            glTexCoord2f(0, 1); glVertex2f(offset_x, offset_y + display_height)
            glEnd()
            glDisable(GL_TEXTURE_2D)
        elif self.loading_state:
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, size.x, size.y, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self._draw_loading_overlay(size.x, size.y)
        else:
            # Use configured target aspect ratio for WYSIWYG preview
            target_aspect = self.target_aspect_ratio

            viewport_aspect = float(w) / float(h) if h > 0 else target_aspect

            # Calculate viewport dimensions with letterboxing/pillarboxing
            if viewport_aspect > target_aspect:
                # Viewport is wider - add pillarbox (black bars left/right)
                viewport_height = h
                viewport_width = int(h * target_aspect)
                viewport_x = (w - viewport_width) // 2
                viewport_y = 0
            else:
                # Viewport is taller - add letterbox (black bars top/bottom)
                viewport_width = w
                viewport_height = int(w / target_aspect)
                viewport_x = 0
                viewport_y = (h - viewport_height) // 2

            # Clear entire viewport to black
            glViewport(0, 0, w, h)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Set viewport to the letterboxed/pillarboxed area
            glViewport(viewport_x, viewport_y, viewport_width, viewport_height)
            glClearColor(0.04, 0.04, 0.04, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            cam_dist = (self.model_size * 0.5) / (0.4142 * min(1.0, target_aspect) * 0.85)
            gluPerspective(45.0, target_aspect, 1.0, cam_dist * 10.0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(0, 0, cam_dist, 0, 0, 0, 0, 1, 0)

            # Match kicad-cli rotation order: R_X(board_tilt) · R_spin · R_Z(board_roll)
            # In OpenGL, last specified = first applied to vertices (right-to-left).
            # So we specify outermost first: board_tilt (X), spin (axis), board_roll (Z).
            glRotatef(self.board_tilt, 1, 0, 0)
            glRotatef(self.direction_sign * self.rotation_angle, self.rotation_axis[0], self.rotation_axis[1], self.rotation_axis[2])
            glRotatef(self.board_roll, 0, 0, 1)

            glTranslatef(-self.model_center[0], -self.model_center[1], -self.model_center[2])
            glColor4f(0.5, 0.5, 0.5, 0.75)
            if self.mesh_data:
                self._draw_mesh()
            else:
                self._draw_placeholder()
                
            # Draw faint gray outline matching the resolution viewport
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, w, h, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # Using same math as viewport calculation above
            if viewport_aspect > target_aspect:
                vw, vh = int(h * target_aspect), h
                vx, vy = (w - vw) // 2, 0
            else:
                vw, vh = w, int(w / target_aspect)
                vx, vy = 0, (h - vh) // 2
                
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 1.0, 1.0, 0.12) # Very faint white/gray
            glBegin(GL_LINE_LOOP)
            glVertex2f(vx, vy)
            glVertex2f(vx + vw, vy)
            glVertex2f(vx + vw, vy + vh)
            glVertex2f(vx, vy + vh)
            glEnd()
        self.SwapBuffers()

    def _draw_mesh(self):
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.mesh_data['vertices'])
        glDrawArrays(GL_LINES, 0, self.mesh_data['count'])
        glDisableClientState(GL_VERTEX_ARRAY)

    def _draw_placeholder(self):
        size = self.model_size * 0.4
        glBegin(GL_LINES)
        for d in [-size, size]:
            glVertex3f(-size, d, -size); glVertex3f(size, d, -size)
            glVertex3f(size, d, -size); glVertex3f(size, d, size)
            glVertex3f(size, d, size); glVertex3f(-size, d, size)
            glVertex3f(-size, d, size); glVertex3f(-size, d, -size)
            glVertex3f(d, -size/4, -size); glVertex3f(d, size/4, -size)
            glVertex3f(d, -size/4, size); glVertex3f(d, size/4, size)
        glEnd()

    def _draw_loading_overlay(self, width, height):
        glDisable(GL_DEPTH_TEST)
        glColor4f(0.04, 0.04, 0.04, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(0, 0); glVertex2f(width, 0); glVertex2f(width, height); glVertex2f(0, height)
        glEnd()
        BAR_W, BAR_H, CX, CY = 180, 2, width/2, height/2
        global _SPINRENDER_GLUT_INIT
        try:
            if not _SPINRENDER_GLUT_INIT:
                try: glutInit()
                except: pass
                _SPINRENDER_GLUT_INIT = True
            text = "Loading 3D Model..."
            text_w = len(text) * 9
            glColor3f(0.6, 0.6, 0.6)
            glRasterPos2f(CX - (text_w/2), CY - 15)
            for char in text:
                glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        except:
            pass
        bx, by = CX - (BAR_W/2), CY + 10
        glColor3f(0.15, 0.15, 0.15)
        glBegin(GL_QUADS)
        glVertex2f(bx, by); glVertex2f(bx+BAR_W, by); glVertex2f(bx+BAR_W, by+BAR_H); glVertex2f(bx, by+BAR_H)
        glEnd()
        t = time.time()
        pos = (t * 150) % (BAR_W + 40) - 40
        vs, ve = max(bx, bx + pos), min(bx + BAR_W, bx + pos + 40)
        if vs < ve:
            glColor3f(0.0, 0.737, 0.831)
            glBegin(GL_QUADS)
            glVertex2f(vs, by); glVertex2f(ve, by); glVertex2f(ve, by+BAR_H); glVertex2f(vs, by+BAR_H)
            glEnd()
        glEnable(GL_DEPTH_TEST)

    def on_size(self, _event):
        self.Refresh()

    def on_timer(self, _event):
        if self.playing:
            self.rotation_angle = (self.rotation_angle + self.rotation_speed) % 360.0
            self.Refresh()

    def set_preview_image(self, image_path):
        """Loads a rendered frame as an OpenGL texture overlay."""
        if not os.path.exists(image_path):
            print(f"[SpinRender] Preview image doesn't exist: {image_path}")
            return

        # Stop the 3D preview animation when showing rendered frames
        if self.playing:
            self.timer.Stop()
            self.playing = False

        self.SetCurrent(self.context)
        try:
            image = wx.Image(image_path, wx.BITMAP_TYPE_PNG)
            if not image.IsOk():
                print(f"[SpinRender] Failed to load image (not ok): {image_path}")
                return

            width, height = image.GetSize()
            data = image.GetData()

            # Store texture dimensions for aspect ratio calculation
            self.texture_width = width
            self.texture_height = height

            if not self.has_texture:
                self.preview_texture = glGenTextures(1)
                self.has_texture = True

            glBindTexture(GL_TEXTURE_2D, self.preview_texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            print(f"[SpinRender] Successfully loaded preview: {width}x{height}, has_texture={self.has_texture}")
            self.Refresh()
        except Exception as e:
            print(f"[SpinRender] GL Preview load failed: {e}")

    def clear_preview_image(self):
        """Clears the rendered frame overlay and returns to wireframe."""
        if self.has_texture:
            try:
                self.SetCurrent(self.context)
                glDeleteTextures([self.preview_texture])
            except:
                pass
            self.preview_texture = None
            self.has_texture = False
            self.Refresh()

    def set_period(self, period):
        self.rotation_speed = 360.0 / (period * 30.0)

    def set_direction(self, direction_str):
        self.direction_sign = -1.0 if direction_str.lower() == 'cw' else 1.0
        self.Refresh()

    def set_aspect_ratio(self, width, height):
        """Set the target aspect ratio for WYSIWYG preview"""
        if height > 0:
            self.target_aspect_ratio = float(width) / float(height)
            self.Refresh()

    def start_preview(self):
        self.playing = True
        self.timer.Start(33)

    def stop_preview(self):
        self.playing = False
        self.timer.Stop()

    def cleanup(self):
        self.stop_preview()


class PreviewRenderer(wx.Panel):
    """
    Fallback wireframe 3D preview renderer
    """
    def __init__(self, parent, board_path):
        super().__init__(parent)
        self.rotation_angle = 0.0
        self.board_tilt = 0.0
        self.board_roll = 0.0
        self.spin_tilt = 0.0
        self.spin_heading = 0.0
        self.rotation_speed = 1.2
        self.playing = False
        self.direction_sign = 1.0
        self.preview_bitmap = None
        self.target_aspect_ratio = 16.0 / 9.0  # Default to 1920x1080
        self.on_model_loaded = None  # Callback for consistency with GLPreviewRenderer
        self._update_rotation_axis()
        self.SetBackgroundColour(wx.Colour(10, 10, 10))
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer)

    def _update_rotation_axis(self):
        t = math.radians(self.spin_tilt)
        h = math.radians(self.spin_heading)
        # Spherical coordinates with Z as vertical
        x = math.sin(t) * math.cos(h)
        y = math.sin(t) * math.sin(h)
        z = math.cos(t)
        self.rotation_axis = [x, y, z]
        norm = math.sqrt(x*x + y*y + z*z)
        if norm > 0:
            self.rotation_axis = [x/norm, y/norm, z/norm]

    def set_universal_joint_parameters(self, board_tilt, board_roll, spin_tilt, spin_heading):
        self.board_tilt = board_tilt
        self.board_roll = board_roll
        self.spin_tilt = spin_tilt
        self.spin_heading = spin_heading
        self._update_rotation_axis()
        self.Refresh()

    def on_paint(self, _event):
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        if not gc:
            return
        w, h = self.GetSize()
        if self.preview_bitmap:
            # Draw with aspect ratio preservation and black bars
            viewport_aspect = float(w) / float(h) if h > 0 else 1.0
            bitmap_width = self.preview_bitmap.GetWidth()
            bitmap_height = self.preview_bitmap.GetHeight()
            bitmap_aspect = float(bitmap_width) / float(bitmap_height) if bitmap_height > 0 else 1.0

            # Calculate letterbox/pillarbox dimensions
            if bitmap_aspect > viewport_aspect:
                # Bitmap is wider - add letterbox (black bars top/bottom)
                display_width = w
                display_height = w / bitmap_aspect
                offset_x = 0
                offset_y = (h - display_height) / 2
            else:
                # Bitmap is taller - add pillarbox (black bars left/right)
                display_height = h
                display_width = h * bitmap_aspect
                offset_x = (w - display_width) / 2
                offset_y = 0

            # Draw black background
            gc.SetBrush(wx.Brush(wx.Colour(0, 0, 0)))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawRectangle(0, 0, w, h)

            # Draw bitmap with correct aspect ratio
            gc.DrawBitmap(self.preview_bitmap, offset_x, offset_y, display_width, display_height)
        else:
            self.draw_pcb_wireframe(gc, w/2, h/2)

    def draw_pcb_wireframe(self, gc, cx, cy):
        size = 100
        verts = [
            (-size, -size/4, -size), (size, -size/4, -size), (size, -size/4, size), (-size, -size/4, size),
            (-size, size/4, -size), (size, size/4, -size), (size, size/4, size), (-size, size/4, size)
        ]
        rotated = []
        axis = self.rotation_axis
        angle = math.radians(self.direction_sign * self.rotation_angle)
        cos_a = math.cos(angle); sin_a = math.sin(angle)
        bt = math.radians(self.board_tilt); cos_bt = math.cos(bt); sin_bt = math.sin(bt)
        br = math.radians(self.board_roll); cos_br = math.cos(br); sin_br = math.sin(br)
        
        for v in verts:
            # Match kicad-cli rotation order: R_X(board_tilt) · R_spin · R_Z(board_roll)
            # Applied right-to-left: Z first, then spin, then X.

            # Step 1: Z rotation (board_roll)
            zx = v[0]*cos_br - v[1]*sin_br
            zy = v[0]*sin_br + v[1]*cos_br
            zz = v[2]

            # Step 2: Spin around axis (Rodrigues)
            dot = zx*axis[0] + zy*axis[1] + zz*axis[2]
            cross = [axis[1]*zz - axis[2]*zy, axis[2]*zx - axis[0]*zz, axis[0]*zy - axis[1]*zx]
            sx = zx*cos_a + cross[0]*sin_a + axis[0]*dot*(1-cos_a)
            sy = zy*cos_a + cross[1]*sin_a + axis[1]*dot*(1-cos_a)
            sz = zz*cos_a + cross[2]*sin_a + axis[2]*dot*(1-cos_a)

            # Step 3: X rotation (board_tilt)
            rx = sx
            ry = sy*cos_bt - sz*sin_bt
            rz = sy*sin_bt + sz*cos_bt

            scale = 200.0 / (200.0 + rz)
            rotated.append((cx + rx*scale, cy + ry*scale, rz))

        edges = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)]
        pen = wx.Pen(wx.Colour(85, 85, 85, 150), 1)
        for s, e in edges:
            x1, y1, z1 = rotated[s]; x2, y2, z2 = rotated[e]
            gc.SetPen(pen); gc.StrokeLine(x1, y1, x2, y2)

    def on_timer(self, _event):
        if self.playing:
            self.rotation_angle = (self.rotation_angle + self.rotation_speed) % 360.0
            self.Refresh()

    def set_preview_image(self, image_path):
        if not os.path.exists(image_path):
            print(f"[SpinRender] Fallback preview image doesn't exist: {image_path}")
            return

        # Stop the 3D preview animation when showing rendered frames
        if self.playing:
            self.timer.Stop()
            self.playing = False

        try:
            self.preview_bitmap = wx.Bitmap(image_path, wx.BITMAP_TYPE_PNG)
            if not self.preview_bitmap.IsOk():
                print(f"[SpinRender] Fallback bitmap not ok: {image_path}")
                return
            print(f"[SpinRender] Fallback preview loaded: {self.preview_bitmap.GetWidth()}x{self.preview_bitmap.GetHeight()}")
            self.Refresh()
        except Exception as e:
            print(f"[SpinRender] Fallback preview load failed: {e}")

    def clear_preview_image(self):
        self.preview_bitmap = None
        self.Refresh()

    def set_period(self, period):
        self.rotation_speed = 360.0 / (period * 30.0)

    def set_direction(self, direction_str):
        self.direction_sign = -1.0 if direction_str.lower() == 'cw' else 1.0
        self.Refresh()

    def set_aspect_ratio(self, width, height):
        """Set the target aspect ratio for WYSIWYG preview"""
        if height > 0:
            self.target_aspect_ratio = float(width) / float(height)
            self.Refresh()

    def start_preview(self):
        self.playing = True
        self.timer.Start(33)

    def stop_preview(self):
        self.playing = False
        self.timer.Stop()

    def cleanup(self):
        self.stop_preview()
