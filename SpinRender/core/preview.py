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
                    kicad_cli = path; break
                except (FileNotFoundError, subprocess.TimeoutExpired): continue
            if not kicad_cli: return False
            cmd = [kicad_cli, 'pcb', 'export', 'glb', '--fuse-shapes', '--grid-origin', '--no-dnp', '--subst-models', '--include-pads', '--include-silkscreen', board_path, '--output', output_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, text=True)
            return result.returncode == 0 and os.path.exists(output_path)
        except Exception: return False

    @staticmethod
    def load_glb_mesh(glb_path):
        try:
            scene = trimesh.load(glb_path)
            if isinstance(scene, trimesh.Scene):
                if not scene.geometry: return None
                mesh = scene.to_mesh()
            else: mesh = scene
            
            # Auto-scale from meters to mm if needed
            if np.max(mesh.extents) < 1.0:
                mesh.apply_scale(1000.0)
                
            return mesh
        except Exception: return None


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
        self.rotation_angle = 0.0
        self.rotation_x, self.rotation_y, self.rotation_z = 30.0, 0.0, 0.0
        self.rotation_speed = 1.2
        self.direction_sign = 1.0  # 1.0 for CCW, -1.0 for CW
        self.playing = False
        self.model_center = np.array([0.0, 0.0, 0.0])
        self.model_size = 150.0
        self.loading_state = "exporting"
        self.Bind(wx.EVT_PAINT, self.on_paint); self.Bind(wx.EVT_SIZE, self.on_size)
        self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.on_timer)
        self.loading_timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self._on_loading_timer, self.loading_timer)
        self.loading_timer.Start(50)
        wx.CallAfter(self._start_loading_thread)

    def _start_loading_thread(self):
        threading.Thread(target=self._export_and_load_sync, daemon=True).start()

    def _on_loading_timer(self, _event):
        if self.loading_state: self.Refresh()
        else: self.loading_timer.Stop()

    def _export_and_load_sync(self):
        try:
            temp_dir = tempfile.gettempdir()
            glb_path = os.path.join(temp_dir, f"{Path(self.board_path).stem}_preview.glb")
            if PCBModelLoader.export_glb(self.board_path, glb_path):
                mesh = PCBModelLoader.load_glb_mesh(glb_path)
                if mesh: wx.CallAfter(self._set_mesh, mesh)
                else: wx.CallAfter(self._update_loading, None)
            else: wx.CallAfter(self._update_loading, None)
        except Exception: wx.CallAfter(self._update_loading, None)

    def _update_loading(self, state):
        self.loading_state = state; self.Refresh()

    def _set_mesh(self, mesh):
        # Use idiomatic trimesh processing to clean topology
        try:
            mesh.process(validate=True)
        except Exception:
            # Fallback to simple merge if process() is not fully available
            if hasattr(mesh, 'merge_vertices'):
                mesh.merge_vertices()
        
        bounds = mesh.bounds
        self.model_center = (bounds[0] + bounds[1]) / 2
        self.model_size = np.linalg.norm(bounds[1] - bounds[0])
        
        # EXTRACT FEATURE EDGES (Clean Outlines)
        try:
            # 1. Get sharp edges (adjacent faces > 30 degrees)
            sharp_mask = mesh.face_adjacency_angles > 0.52
            sharp_edges = mesh.face_adjacency_edges[sharp_mask]
            
            # 2. Get boundary edges (edges with only one face)
            try:
                boundary_edges = mesh.edges_unique[mesh.edges_unique_count == 1]
            except Exception:
                # Older trimesh fallback
                boundary_edges = mesh.edges_boundary if hasattr(mesh, 'edges_boundary') else []
            
            if len(sharp_edges) > 0 and len(boundary_edges) > 0:
                edges = np.vstack([sharp_edges, boundary_edges])
            elif len(sharp_edges) > 0:
                edges = sharp_edges
            else:
                edges = boundary_edges
                
            if len(edges) == 0:
                edges = mesh.edges_unique
        except Exception as e:
            print(f"[SpinRender] Feature extraction fallback: {e}")
            edges = mesh.edges_unique
        
        line_vertices = mesh.vertices[edges].reshape(-1, 3)
        self.mesh_data = {'vertices': line_vertices.astype(np.float32), 'count': len(line_vertices)}
        
        self.loading_state = None; self.Refresh()

    def init_gl(self):
        if self.initialized: return
        self.SetCurrent(self.context)
        glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LESS)
        glDisable(GL_CULL_FACE)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_LIGHTING)
        glEnable(GL_LINE_SMOOTH); glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(1.2)
        glClearColor(0.04, 0.04, 0.04, 1.0)
        self.initialized = True

    def on_paint(self, _event):
        size = self.GetSize(); scale = self.GetContentScaleFactor()
        w, h = int(size.x * scale), int(size.y * scale)
        if w == 0 or h == 0: return
        self.SetCurrent(self.context); self.init_gl()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, w, h)

        if self.loading_state:
            glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0, size.x, size.y, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW); glLoadIdentity()
            self._draw_loading_overlay(size.x, size.y)
        else:
            glMatrixMode(GL_PROJECTION); glLoadIdentity()
            aspect = float(size.x)/float(size.y)
            cam_dist = (self.model_size * 0.5) / (0.4142 * min(1.0, aspect) * 0.9)
            gluPerspective(45.0, aspect, 1.0, cam_dist * 10.0)
            glMatrixMode(GL_MODELVIEW); glLoadIdentity()
            gluLookAt(0, 0, cam_dist, 0, 0, 0, 0, 1, 0)
            # Apply static orientation (X, Y, Z set the tilt of the spin axis)
            glRotatef(self.rotation_x, 1, 0, 0)
            glRotatef(self.rotation_y, 0, 1, 0)
            glRotatef(self.rotation_z, 0, 0, 1)
            # Apply animated spin around the Y-axis of the tilted coordinate system
            glRotatef(self.rotation_angle, 0, 1, 0)
            glTranslatef(-self.model_center[0], -self.model_center[1], -self.model_center[2])
            glColor4f(0.5, 0.5, 0.5, 0.75) 
            if self.mesh_data: self._draw_mesh()
            else: self._draw_placeholder()
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
            glVertex3f(-size, d, -size); glVertex3f(size, d, -size); glVertex3f(size, d, -size); glVertex3f(size, d, size)
            glVertex3f(size, d, size); glVertex3f(-size, d, size); glVertex3f(-size, d, size); glVertex3f(-size, d, -size)
            glVertex3f(d, -size/4, -size); glVertex3f(d, size/4, -size); glVertex3f(d, -size/4, size); glVertex3f(d, size/4, size)
        glEnd()

    def _draw_loading_overlay(self, width, height):
        glDisable(GL_DEPTH_TEST)
        glColor4f(0.04, 0.04, 0.04, 0.8); glBegin(GL_QUADS); glVertex2f(0, 0); glVertex2f(width, 0); glVertex2f(width, height); glVertex2f(0, height); glEnd()
        BAR_W, BAR_H, CX, CY = 180, 2, width/2, height/2
        global _SPINRENDER_GLUT_INIT
        try:
            if not _SPINRENDER_GLUT_INIT:
                try: glutInit()
                except: pass
                _SPINRENDER_GLUT_INIT = True
            text = "Loading 3D Model..."; text_w = len(text) * 9
            glColor3f(0.6, 0.6, 0.6); glRasterPos2f(CX - (text_w/2), CY - 15)
            for char in text: glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(char))
        except: pass
        bx, by = CX - (BAR_W/2), CY + 10
        glColor3f(0.15, 0.15, 0.15); glBegin(GL_QUADS); glVertex2f(bx, by); glVertex2f(bx+BAR_W, by); glVertex2f(bx+BAR_W, by+BAR_H); glVertex2f(bx, by+BAR_H); glEnd()
        t = time.time(); pos = (t * 150) % (BAR_W + 40) - 40
        vs, ve = max(bx, bx + pos), min(bx + BAR_W, bx + pos + 40)
        if vs < ve:
            glColor3f(0.0, 0.737, 0.831); glBegin(GL_QUADS); glVertex2f(vs, by); glVertex2f(ve, by); glVertex2f(ve, by+BAR_H); glVertex2f(vs, by+BAR_H); glEnd()
        glEnable(GL_DEPTH_TEST)

    def on_size(self, _event): self.Refresh()
    def on_timer(self, _event):
        if self.playing: 
            self.rotation_angle = (self.rotation_angle + (self.direction_sign * self.rotation_speed)) % 360.0
            self.Refresh()
    def set_rotation(self, x, y, z): self.rotation_x, self.rotation_y, self.rotation_z = x, y, z; self.Refresh()
    def set_period(self, period): self.rotation_speed = 360.0 / (period * 30.0)
    def set_direction(self, direction_str):
        self.direction_sign = -1.0 if direction_str.lower() == 'cw' else 1.0
        self.Refresh()
    def start_preview(self): self.playing = True; self.timer.Start(33)
    def stop_preview(self): self.playing = False; self.timer.Stop()
    def cleanup(self): self.stop_preview()


class PreviewRenderer(wx.Panel):
    """
    Fallback wireframe 3D preview renderer
    """
    def __init__(self, parent, board_path):
        super().__init__(parent); self.rotation_angle, self.rotation_x, self.rotation_y, self.rotation_z, self.rotation_speed, self.playing = 0.0, 0.0, 0.0, 0.0, 1.2, False
        self.direction_sign = 1.0
        self.SetBackgroundColour(wx.Colour(10, 10, 10)); self.Bind(wx.EVT_PAINT, self.on_paint)
        self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.on_timer)

    def on_paint(self, _event):
        dc = wx.PaintDC(self); gc = wx.GraphicsContext.Create(dc)
        if not gc: return
        w, h = self.GetSize(); self.draw_pcb_wireframe(gc, w/2, h/2)

    def draw_pcb_wireframe(self, gc, cx, cy):
        size, verts, rotated = 100, [(-size, -size/4, -size), (size, -size/4, -size), (size, -size/4, size), (-size, -size/4, size), (-size, size/4, -size), (size, size/4, -size), (size, size/4, size), (-size, size/4, size)], []
        for x, y, z in verts:
            # Apply static orientation (X, Y, Z set the tilt of the spin axis)
            xr = math.radians(self.rotation_x); y1 = y*math.cos(xr) - z*math.sin(xr); z1 = y*math.sin(xr) + z*math.cos(xr)
            yr = math.radians(self.rotation_y); x2 = x*math.cos(yr) - z1*math.sin(yr); z2 = x*math.sin(yr) + z1*math.cos(yr)
            zr = math.radians(self.rotation_z); x3 = x2*math.cos(zr) - y1*math.sin(zr); y2 = x2*math.sin(zr) + y1*math.cos(zr)
            # Apply animated spin around Y-axis
            ar = math.radians(self.rotation_angle); xf = x3*math.cos(ar) - z2*math.sin(ar); zf = x3*math.sin(ar) + z2*math.cos(ar)
            scale = 200.0 / (200.0 + zf); rotated.append((cx + xf*scale, cy + y2*scale, zf))
        edges, pen = [(0,1), (1,2), (2,3), (3,0), (4,5), (5,6), (6,7), (7,4), (0,4), (1,5), (2,6), (3,7)], wx.Pen(wx.Colour(85, 85, 85, 150), 1)
        for s, e in edges:
            x1, y1, z1 = rotated[s]; x2, y2, z2 = rotated[e]
            gc.SetPen(pen); gc.StrokeLine(x1, y1, x2, y2)

    def on_timer(self, _event):
        if self.playing: 
            self.rotation_angle = (self.rotation_angle + (self.direction_sign * self.rotation_speed)) % 360.0
            self.Refresh()
    def set_rotation(self, x, y, z): self.rotation_x, self.rotation_y, self.rotation_z = x, y, z; self.Refresh()
    def set_period(self, period): self.rotation_speed = 360.0 / (period * 30.0)
    def set_direction(self, direction_str):
        self.direction_sign = -1.0 if direction_str.lower() == 'cw' else 1.0
        self.Refresh()
    def start_preview(self): self.playing = True; self.timer.Start(33)
    def stop_preview(self): self.playing = False; self.timer.Stop()
    def cleanup(self): self.stop_preview()
