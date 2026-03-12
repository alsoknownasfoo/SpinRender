#!/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
print("DEBUG: Starting script imports...")
import wx
import wx.glcanvas as glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import trimesh
import math
import os
import subprocess
import tempfile
import shutil
import threading
from pathlib import Path

print("DEBUG: Imports completed.")

# --- Constants & Matrix Math (Identical to SpinRender/core/renderer.py) ---

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
    ax, ay, az = axis
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    t = 1 - c
    return [
        [t*ax*ax+c,    t*ax*ay-s*az, t*ax*az+s*ay],
        [t*ax*ay+s*az, t*ay*ay+c,    t*ay*az-s*ax],
        [t*ax*az-s*ay, t*ay*az+s*ax, t*az*az+c   ]
    ]

def _euler_xyz_from_matrix(M):
    sy = max(-1.0, min(1.0, M[0][2]))
    ky = math.asin(sy)
    cos_ky = math.cos(ky)
    if abs(cos_ky) > 1e-6:
        kx = math.atan2(-M[1][2], M[2][2])
        kz = math.atan2(-M[0][1], M[0][0])
    else:
        if sy < 0: kx = math.atan2(M[2][1], M[2][0])
        else: kx = math.atan2(-M[2][1], M[2][0])
        kz = 0.0
    return math.degrees(kx), math.degrees(ky), math.degrees(kz)

def compute_kicad_angles(board_tilt, board_roll, spin_tilt, spin_heading, anim_angle_deg):
    if spin_tilt == 0.0:
        return board_tilt, anim_angle_deg, board_roll
    t = math.radians(spin_tilt)
    h = math.radians(spin_heading)
    axis = (math.sin(t)*math.cos(h), math.sin(t)*math.sin(h), math.cos(t))
    R_spin = _rodrigues(axis, math.radians(anim_angle_deg))
    M = _matmul(_rot_x(math.radians(board_tilt)),
                _matmul(R_spin, _rot_z(math.radians(board_roll))))
    return _euler_xyz_from_matrix(M)

def find_kicad_cli():
    common_paths = ['kicad-cli', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli', '/usr/local/bin/kicad-cli', '/opt/homebrew/bin/kicad-cli']
    for path in common_paths:
        if shutil.which(path): return path
        if os.path.exists(path): return path
    return None

# --- UI Components ---

class ParityCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, is_rendered=False):
        attribs = [glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24, 0]
        super().__init__(parent, attribList=attribs)
        self.context = glcanvas.GLContext(self)
        self.is_rendered = is_rendered
        self.initialized = False
        self.mesh_data = None
        self.texture = None
        self.model_center = np.array([0.0, 0.0, 0.0])
        self.model_size = 150.0
        self.board_tilt = 45.0
        self.board_roll = -45.0
        self.spin_tilt = 45.0
        self.spin_heading = -135.0
        self.anim_angle = 0.0
        self.target_aspect = 16.0 / 9.0
        self.studio_mode = True
        
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)

    def init_gl(self):
        if self.initialized: return
        self.SetCurrent(self.context)
        glEnable(GL_DEPTH_TEST); glDepthFunc(GL_LESS); glDisable(GL_CULL_FACE); glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        # --- Studio Lighting Setup ---
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0) # Key Light (Warm)
        glEnable(GL_LIGHT1) # Fill Light (Cool)
        glEnable(GL_LIGHT2) # Back Light (Rim)
        
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Light 0: Key Light (Front Right, Warm)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.5, 1.0, 2.0, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.9, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        
        # Light 1: Fill Light (Front Left, Cool)
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.5, 0.5, 1.0, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.3, 0.35, 0.45, 1.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
        
        # Light 2: Back Light (High Back, White)
        glLightfv(GL_LIGHT2, GL_POSITION, [0.0, 2.0, -2.0, 0.0])
        glLightfv(GL_LIGHT2, GL_DIFFUSE, [0.5, 0.5, 0.5, 1.0])
        
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        
        glEnable(GL_LINE_SMOOTH); glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2.0); glClearColor(0.04, 0.04, 0.04, 1.0)
        self.initialized = True

    def CaptureToImage(self, filepath, width=1280, height=720):
        self.SetCurrent(self.context); glViewport(0, 0, width, height); glClearColor(0.0, 0.0, 0.0, 1.0); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._render_scene_content(0, 0, width, height); glPixelStorei(GL_PACK_ALIGNMENT, 1); data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)
        image = wx.Image(width, height); image.SetData(data); image = image.Mirror(False); image.SaveFile(filepath, wx.BITMAP_TYPE_JPEG); self.Refresh(); return filepath

    def set_mesh(self, mesh):
        try:
            if hasattr(mesh, 'process'): mesh.process(validate=True)
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90), [1, 0, 0]))
            bounds = mesh.bounds; self.model_center = (bounds[0] + bounds[1]) / 2; self.model_size = np.linalg.norm(bounds[1] - bounds[0])
            try:
                sharp_mask = mesh.face_adjacency_angles > 0.52; sharp_edges = mesh.face_adjacency_edges[sharp_mask]
                try: boundary_edges = mesh.edges_unique[mesh.edges_unique_count == 1]
                except: boundary_edges = mesh.edges_boundary if hasattr(mesh, 'edges_boundary') else []
                if len(sharp_edges) > 0 and len(boundary_edges) > 0: edges = np.vstack([sharp_edges, boundary_edges])
                elif len(sharp_edges) > 0: edges = sharp_edges
                else: edges = boundary_edges
                if len(edges) == 0: edges = mesh.edges_unique
            except: edges = mesh.edges_unique
            line_vertices = mesh.vertices[edges].reshape(-1, 3); tri_vertices = mesh.vertices[mesh.faces].reshape(-1, 3); tri_normals = np.repeat(mesh.face_normals, 3, axis=0)
            self.mesh_data = {'vertices': line_vertices.astype(np.float32), 'count': len(line_vertices), 'tri_vertices': tri_vertices.astype(np.float32), 'tri_normals': tri_normals.astype(np.float32), 'tri_count': len(tri_vertices)}; self.Refresh()
        except Exception as e: print(f"DEBUG: Error in set_mesh: {e}")

    def set_image(self, img_path):
        if not os.path.exists(img_path): return
        self.SetCurrent(self.context); img = wx.Image(img_path, wx.BITMAP_TYPE_ANY)
        if not img.IsOk(): return
        w, h = img.GetSize(); data = img.GetData()
        if self.texture is None: self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture); glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, data); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR); glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR); self.Refresh()

    def on_paint(self, event):
        self.SetCurrent(self.context); self.init_gl(); size = self.GetClientSize(); scale = self.GetContentScaleFactor(); w, h = int(size.x * scale), int(size.y * scale)
        if w == 0 or h == 0: return
        aspect = float(w) / float(h); target = self.target_aspect
        if aspect > target: vw, vh = int(h * target), h; vx, vy = (w - vw) // 2, 0
        else: vw, vh = w, int(w / target); vx, vy = 0, (h - vh) // 2
        glViewport(0, 0, w, h); glClearColor(0.0, 0.0, 0.0, 1.0); glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT); self._render_scene_content(vx, vy, vw, vh); self.SwapBuffers()

    def _render_scene_content(self, vx, vy, vw, vh):
        glViewport(vx, vy, vw, vh)
        if self.is_rendered and self.texture:
            glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0, 1, 1, 0, -1, 1); glMatrixMode(GL_MODELVIEW); glLoadIdentity(); glEnable(GL_TEXTURE_2D); glBindTexture(GL_TEXTURE_2D, self.texture); glColor4f(1, 1, 1, 1); glBegin(GL_QUADS); glTexCoord2f(0,0); glVertex2f(0, 0); glTexCoord2f(1,0); glVertex2f(1, 0); glTexCoord2f(1,1); glVertex2f(1, 1); glTexCoord2f(0,1); glVertex2f(0, 1); glEnd(); glDisable(GL_TEXTURE_2D)
        else:
            glMatrixMode(GL_PROJECTION); glLoadIdentity(); cam_dist = (self.model_size * 0.5) / (0.4142 * min(1.0, self.target_aspect) * 0.85); gluPerspective(45.0, self.target_aspect, 1.0, cam_dist * 10.0); glMatrixMode(GL_MODELVIEW); glLoadIdentity(); gluLookAt(0, 0, cam_dist, 0, 0, 0, 0, 1, 0)
            
            # --- RENDER FLOOR (Studio faked background) ---
            if self.studio_mode:
                glDisable(GL_LIGHTING); glBegin(GL_QUADS); glColor3f(0.02, 0.02, 0.02); glVertex3f(-1000, -self.model_size, -1000); glVertex3f(1000, -self.model_size, -1000); glColor3f(0.05, 0.05, 0.05); glVertex3f(1000, -self.model_size, 1000); glVertex3f(-1000, -self.model_size, 1000); glEnd(); glEnable(GL_LIGHTING)

            glRotatef(self.board_tilt, 1, 0, 0); t = math.radians(self.spin_tilt); h = math.radians(self.spin_heading); axis = (math.sin(t)*math.cos(h), math.sin(t)*math.sin(h), math.cos(t)); glRotatef(self.anim_angle, axis[0], axis[1], axis[2]); glRotatef(self.board_roll, 0, 0, 1)
            
            # 1. ORIGIN AXES (Always visible but dim in Studio)
            glDisable(GL_LIGHTING); glLineWidth(1.0); glBegin(GL_LINES)
            asize = self.model_size * 0.3 if self.model_size > 0 else 50.0
            glColor4f(1, 0, 0, 0.3); glVertex3f(0,0,0); glVertex3f(asize,0,0); glColor4f(0, 1, 0, 0.3); glVertex3f(0,0,0); glVertex3f(0,asize,0); glColor4f(0, 0, 1, 0.3); glVertex3f(0,0,0); glVertex3f(0,0,asize); glEnd(); glLineWidth(2.0)
            
            glTranslatef(-self.model_center[0], -self.model_center[1], -self.model_center[2])
            if self.mesh_data:
                glEnable(GL_LIGHTING); glEnable(GL_POLYGON_OFFSET_FILL); glPolygonOffset(1.0, 1.0)
                
                # Material Properties
                glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
                glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50.0)
                
                glColor4f(0.85, 0.85, 0.85, 1.0) 
                glEnableClientState(GL_VERTEX_ARRAY); glEnableClientState(GL_NORMAL_ARRAY)
                glVertexPointer(3, GL_FLOAT, 0, self.mesh_data['tri_vertices']); glNormalPointer(GL_FLOAT, 0, self.mesh_data['tri_normals'])
                glDrawArrays(GL_TRIANGLES, 0, self.mesh_data['tri_count']); glDisableClientState(GL_NORMAL_ARRAY); glDisable(GL_POLYGON_OFFSET_FILL)
                glDisable(GL_LIGHTING); glColor4f(0.2, 0.2, 0.2, 0.5) # Thin silhouette edges
                glVertexPointer(3, GL_FLOAT, 0, self.mesh_data['vertices']); glDrawArrays(GL_LINES, 0, self.mesh_data['count']); glDisableClientState(GL_VERTEX_ARRAY)
            else: glColor3f(0.4, 0.4, 0.4); glBegin(GL_LINE_LOOP); glVertex3f(-20, 0, -20); glVertex3f(20, 0, -20); glVertex3f(20, 0, 20); glVertex3f(-20, 0, 20); glEnd()
            
            # Reset Projection for viewport overlay
            glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0, vw, vh, 0, -1, 1); glMatrixMode(GL_MODELVIEW); glLoadIdentity(); glDisable(GL_LIGHTING)
            glColor4f(1.0, 1.0, 1.0, 0.2); glBegin(GL_LINE_LOOP); glVertex2f(0, 0); glVertex2f(vw, 0); glVertex2f(vw, vh); glVertex2f(0, vh); glEnd()

    def on_size(self, event): self.Refresh()

class ParityFrame(wx.Frame):
    def __init__(self, board_path):
        super().__init__(None, title="SpinRender Matrix Parity Debugger", size=(1600, 900))
        self.board_path = board_path; self.temp_dir = tempfile.mkdtemp(prefix='spinrender_parity_'); self.kicad_cli = find_kicad_cli()
        self.is_rendering = False; self.pending_render = False; self.live_timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.on_live_timer, self.live_timer)
        panel = wx.Panel(self); main_sizer = wx.BoxSizer(wx.HORIZONTAL); ctrl_panel = wx.ScrolledWindow(panel, size=(280, -1)); ctrl_panel.SetScrollRate(0, 20); ctrl_panel.SetBackgroundColour(wx.Colour(25, 25, 25)); ctrl_sizer = wx.BoxSizer(wx.VERTICAL); self.sliders = {}
        params = [("Board Tilt", -180, 180, 45), ("Board Roll", -180, 180, -45), ("Spin Tilt", -180, 180, 45), ("Spin Heading", -180, 180, -135), ("Anim Angle", -360, 360, 0)]
        for name, min_v, max_v, def_v in params:
            lbl = wx.StaticText(ctrl_panel, label=f"{name.upper()}: {def_v}"); lbl.SetForegroundColour(wx.Colour(180, 180, 180)); slider = wx.Slider(ctrl_panel, value=def_v, minValue=min_v, maxValue=max_v, style=wx.SL_HORIZONTAL); slider.Bind(wx.EVT_SLIDER, self.on_param_change); ctrl_sizer.Add(lbl, 0, wx.ALL, 5); ctrl_sizer.Add(slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10); self.sliders[name.lower().replace(" ", "_")] = (slider, lbl, name)
        
        # Quality Controls
        self.high_quality = wx.CheckBox(ctrl_panel, label="HIGH QUALITY RENDERING"); self.high_quality.SetForegroundColour(wx.WHITE); ctrl_sizer.Add(self.high_quality, 0, wx.ALL, 10)
        self.studio_cb = wx.CheckBox(ctrl_panel, label="STUDIO MODE (OPENGL)"); self.studio_cb.SetForegroundColour(wx.WHITE); self.studio_cb.SetValue(True); self.studio_cb.Bind(wx.EVT_CHECKBOX, self.on_studio_toggle); ctrl_sizer.Add(self.studio_cb, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10)

        self.save_btn = wx.Button(ctrl_panel, label="SAVE PARITY PAIR (1280x720)"); self.save_btn.SetBackgroundColour(wx.Colour(0, 150, 0)); self.save_btn.SetForegroundColour(wx.WHITE); self.save_btn.Bind(wx.EVT_BUTTON, self.on_save_pair); ctrl_sizer.Add(self.save_btn, 0, wx.ALL | wx.EXPAND, 10)
        self.status = wx.StaticText(ctrl_panel, label="READY"); self.status.SetForegroundColour(wx.Colour(0, 188, 212)); ctrl_sizer.Add(self.status, 0, wx.ALL, 10); self.kicad_info = wx.TextCtrl(ctrl_panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 120)); self.kicad_info.SetBackgroundColour(wx.Colour(15, 15, 15)); self.kicad_info.SetForegroundColour(wx.Colour(255, 214, 0)); ctrl_sizer.Add(self.kicad_info, 0, wx.EXPAND | wx.ALL, 10); self.log = wx.TextCtrl(ctrl_panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 150)); self.log.SetBackgroundColour(wx.Colour(10, 10, 10)); self.log.SetForegroundColour(wx.Colour(150, 150, 150)); ctrl_sizer.Add(self.log, 1, wx.EXPAND | wx.ALL, 10); ctrl_panel.SetSizer(ctrl_sizer); main_sizer.Add(ctrl_panel, 0, wx.EXPAND); view_sizer = wx.BoxSizer(wx.VERTICAL); canvas_sizer = wx.BoxSizer(wx.HORIZONTAL); self.pre_canvas = ParityCanvas(panel); canvas_sizer.Add(self.pre_canvas, 1, wx.EXPAND | wx.ALL, 4); self.ren_canvas = ParityCanvas(panel, is_rendered=True); canvas_sizer.Add(self.ren_canvas, 1, wx.EXPAND | wx.ALL, 4); view_sizer.Add(canvas_sizer, 1, wx.EXPAND); main_sizer.Add(view_sizer, 1, wx.EXPAND); panel.SetSizer(main_sizer); self.Bind(wx.EVT_CLOSE, self.on_close); threading.Thread(target=self.load_model, daemon=True).start()

    def on_studio_toggle(self, event):
        self.pre_canvas.studio_mode = self.studio_cb.GetValue(); self.pre_canvas.Refresh()

    def load_model(self):
        glb_path = str(Path(self.board_path).with_suffix('.glb'))
        if not os.path.exists(glb_path): wx.CallAfter(self.status.SetLabel, "GLB MISSING"); return
        try:
            mesh = trimesh.load(glb_path);
            if isinstance(mesh, trimesh.Scene): mesh = mesh.to_mesh()
            if np.max(mesh.extents) < 1.0: mesh.apply_scale(1000.0)
            wx.CallAfter(self.pre_canvas.set_mesh, mesh); wx.CallAfter(self.status.SetLabel, "MODEL LOADED")
        except Exception as e: wx.CallAfter(self.status.SetLabel, f"ERROR: {e}")

    def on_param_change(self, event):
        for key, (slider, lbl, name) in self.sliders.items():
            val = slider.GetValue(); lbl.SetLabel(f"{name.upper()}: {val}"); setattr(self.pre_canvas, key, val)
        kx, ky, kz = compute_kicad_angles(self.pre_canvas.board_tilt, self.pre_canvas.board_roll, self.pre_canvas.spin_tilt, self.pre_canvas.spin_heading, self.pre_canvas.anim_angle); self.kicad_info.SetValue(f"KICAD-CLI ROTATE:\n{kx:.4f},{ky:.4f},{kz:.4f}"); self.pre_canvas.Refresh()
        self.live_timer.Start(300, oneShot=True)

    def on_live_timer(self, event):
        if self.is_rendering: self.pending_render = True
        else: threading.Thread(target=self._run_render, args=(True,)).start()

    def on_save_pair(self, event):
        self.save_btn.Enable(False); threading.Thread(target=self._run_render, args=(False,)).start()

    def _run_render(self, is_live):
        self.is_rendering = True; wx.CallAfter(self.status.SetLabel, "LIVE RENDERING..." if is_live else "SAVING PAIR...")
        bt, br, st, sh, aa = self.pre_canvas.board_tilt, self.pre_canvas.board_roll, self.pre_canvas.spin_tilt, self.pre_canvas.spin_heading, self.pre_canvas.anim_angle
        kx, ky, kz = compute_kicad_angles(bt, br, st, sh, aa); kx %= 360.0; rotate_str = f"{kx:.4f},{ky:.4f},{kz:.4f}"
        if is_live: ki_path = os.path.join(self.temp_dir, "live_preview.jpg")
        else:
            base_name = f"BT{int(bt)}_BR{int(br)}_ST{int(st)}_SH{int(sh)}_AA{int(aa)}"
            gl_path = os.path.join(os.getcwd(), f"{base_name}_opengl.jpg"); wx.CallAfter(self.pre_canvas.CaptureToImage, gl_path); ki_path = os.path.join(os.getcwd(), f"{base_name}_kicad.jpg")
        
        quality = "high" if self.high_quality.GetValue() else "basic"
        cmd = [self.kicad_cli, 'pcb', 'render', '--perspective', '--rotate', rotate_str, '--zoom', '0.85', '-w', '1280', '-h', '720', '--background', 'opaque', '--quality', quality, '--light-side', '0.15', '--light-side-elevation', '45', '-o', ki_path, self.board_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True); wx.CallAfter(self.ren_canvas.set_image, ki_path); wx.CallAfter(self.status.SetLabel, "LIVE UPDATED" if is_live else "PAIR SAVED")
        except Exception as e: wx.CallAfter(self.status.SetLabel, "FAILED"); print(f"ERROR: {e}")
        self.is_rendering = False
        if self.pending_render: self.pending_render = False; wx.CallAfter(self.live_timer.Start, 10, True)
        if not is_live: wx.CallAfter(self.save_btn.Enable, True)

    def on_close(self, event):
        if os.path.exists(self.temp_dir): shutil.rmtree(self.temp_dir)
        self.Destroy()

if __name__ == "__main__":
    app = wx.App(); board = "../res/testboard.kicad_pcb"
    if os.path.exists(board):
        frame = ParityFrame(board); frame.Show(); wx.SafeYield(); frame.Layout(); event = wx.CommandEvent(wx.EVT_SLIDER.typeId); frame.on_param_change(event); app.MainLoop()
    else: print(f"Error: {board} not found.")
