# Blender: 실제 서울 구 경계 + TOP5 위치 3D 장면 (세로 숏폼)
import bpy, json, sys, math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODE = argv[0] if argv else "coords"          # coords | test | render
OUT = argv[1] if len(argv) > 1 else "/tmp/frames"
D = json.load(open("seoul.json"))
M = json.load(open("/home/user/JY_reposit/out/top5_voice/manifest.json"))
import os
FPS = int(os.environ.get('FPS','24'))
ST = {s["id"]: s["start"] for s in M["scenes"]}
TOTAL = M["total"] + 1.2
LON0, LAT0 = 126.99, 37.55
def xy(lon, lat): return ((lon - LON0) * 88.2, (lat - LAT0) * 111.0)   # km

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, int(TOTAL * FPS)

def mat(name, color, emit=0.0, rough=0.6, ecolor=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*(ecolor or color), 1); b.inputs["Emission Strength"].default_value = emit
    return m

M_GU = mat("gu", (0.035, 0.06, 0.12))
M_GUH = mat("guh", (0.06, 0.10, 0.20))
M_EDGE = mat("edge", (0.2, 0.5, 1.0), emit=1.6)
M_RIVER = mat("river", (0.02, 0.10, 0.25), emit=0.6, rough=0.1, ecolor=(0.05, 0.25, 0.6))
M_GOLD = mat("gold", (1.0, 0.42, 0.06), emit=1.1, rough=0.3)
M_GROUND = mat("ground", (0.01, 0.015, 0.03))

# 바닥
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.02)); bpy.context.object.data.materials.append(M_GROUND)

HL = {"강남구", "용산구", "성동구"}
for gu, geom in D["gu"].items():
    if not geom: continue
    rings = geom["coordinates"] if geom["type"] == "Polygon" else [p[0] for p in geom["coordinates"]]
    rings = rings[:1] if geom["type"] == "Polygon" else rings
    for ri, ring in enumerate(rings):
        pts = [xy(*p) for p in ring[:-1]]
        me = bpy.data.meshes.new(gu); me.from_pydata([(x, y, 0) for x, y in pts], [], [list(range(len(pts)))])
        ob = bpy.data.objects.new(gu, me); sc.collection.objects.link(ob)
        ob.data.materials.append(M_GUH if gu in HL else M_GU)
        sol = ob.modifiers.new("s", "SOLIDIFY"); sol.thickness = 0.12; sol.offset = 1
        # 경계선 (발광 커브)
        cu = bpy.data.curves.new(gu + "_e", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.02
        sp = cu.splines.new("POLY"); sp.points.add(len(pts)); sp.use_cyclic_u = True
        for i, (x, y) in enumerate(pts + [pts[0]]): sp.points[i].co = (x, y, 0.125, 1)
        e = bpy.data.objects.new(gu + "_e", cu); sc.collection.objects.link(e); e.data.materials.append(M_EDGE)

# 한강 (개략 경로)
HAN = [(126.80, 37.585), (126.85, 37.570), (126.89, 37.553), (126.93, 37.532), (126.96, 37.518), (126.99, 37.514),
       (127.02, 37.522), (127.05, 37.528), (127.08, 37.522), (127.10, 37.523), (127.12, 37.535), (127.16, 37.555)]
cu = bpy.data.curves.new("han", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.45; cu.bevel_resolution = 0
sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(HAN) - 1)
for i, (lo, la) in enumerate(HAN):
    p = sp.bezier_points[i]; p.co = (*xy(lo, la), 0); p.handle_left_type = p.handle_right_type = "AUTO"
h = bpy.data.objects.new("han", cu); h.scale.z = 0.04; h.location.z = 0.13; sc.collection.objects.link(h); h.data.materials.append(M_RIVER)

# TOP5 (공시가격, 억원) — 위치는 동 단위 개략
C = (127.0500, 37.5215)
TOP = [  # rank, name, price, lon, lat, scene id
    (5, "아크로서울포레스트", 207.1, 127.0444, 37.5446, "t2_rank5"),
    (4, "워너청담", 224.8, C[0] - 0.006, C[1] + 0.002, "t3_rank4"),
    (3, "PH129", 232.3, C[0] + 0.001, C[1] - 0.004, "t4_rank3"),
    (2, "나인원한남", 242.8, 127.0074, 37.5382, "t5_rank2"),
    (1, "에테르노청담", 325.7, C[0] + 0.007, C[1] + 0.001, "t6_rank1"),
]
towers = []
for rank, name, price, lo, la, sid in TOP:
    x, y = xy(lo, la)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.16, depth=1, location=(x, y, 0.5))
    t = bpy.context.object; t.name = name; t.data.materials.append(M_GOLD)
    bpy.ops.object.transform_apply(location=False, scale=False)
    t.data.transform(__import__("mathutils").Matrix.Translation((0, 0, 0.5)))  # 원점을 바닥으로
    t.location = (x, y, 0.12)
    H = price / 325.7 * 4.0
    f0 = int((ST[sid] + 0.4) * FPS)
    t.scale = (1, 1, 0.001); t.keyframe_insert("scale", frame=1); t.keyframe_insert("scale", frame=f0)
    t.scale = (1, 1, H); t.keyframe_insert("scale", frame=f0 + int(1.3 * FPS))
    towers.append((rank, name, price, t, H))

# 조명, 하늘
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.006, 0.01, 0.025, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30))); bpy.context.object.data.energy = 1.2

# 카메라 + 시선 대상
bpy.ops.object.empty_add(location=(0, 0, 0)); tgt = bpy.context.object
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam; cam.data.lens = 28
con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
def P(name):
    for r, n, p, t, H in towers:
        if n == name: return t.location.x, t.location.y, H
cx, cy = xy(*C)
def key(t, cam_pos, tgt_pos):
    f = max(1, int(t * FPS)); cam.location = cam_pos; tgt.location = tgt_pos
    cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f)
ax, ay, _ = P("아크로서울포레스트"); wx, wy, _ = P("워너청담"); px, py, _ = P("PH129"); nx, ny, _ = P("나인원한남"); ex, ey, eh = P("에테르노청담")
key(0, (-6, -26, 18), (2, 0, 0))
key(ST["t2_rank5"] - 0.3, (-2, -14, 9), (3, -1, 0))
key(ST["t2_rank5"] + 1.5, (ax - 1.5, ay - 5, 4.2), (ax, ay, 2.0))
key(ST["t3_rank4"] + 1.5, (wx - 3, wy - 5.5, 4.2), (wx, wy, 2.0))
key(ST["t4_rank3"] + 1.5, (px + 2.5, py - 5.5, 4.2), (px, py, 2.0))
key(ST["t5_rank2"] + 1.5, (nx - 3.5, ny - 5, 4.5), (nx, ny, 2.2))
key(ST["t6_rank1"] + 1.5, (ex + 2.5, ey - 6.5, 5.5), (ex, ey, 2.8))
key(ST["t6_rank1"] + 8.5, (ex + 4, ey - 7.5, 6.5), (ex, ey, 2.8))
key(ST["t7_outro"] + 3.0, (cx - 3, cy - 12, 10), (cx - 1, cy + 0.5, 1))
key(TOTAL, (cx - 4, cy - 14, 12), (cx - 1, cy + 0.5, 1))

# 렌더 설정 (세로)
r = sc.render; r.resolution_x, r.resolution_y = 540, 960
r.engine = "CYCLES"; sc.cycles.samples = 12; sc.cycles.use_denoising = True; sc.cycles.device = "CPU"
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy" if "AgX - Punchy" in [i.identifier for i in type(sc.view_settings).bl_rna.properties["look"].enum_items] else "None"
r.image_settings.file_format = "PNG"; r.filepath = OUT + "/f_"

if MODE == "coords":   # 프레임별 기둥 꼭대기 화면 좌표 → HTML 라벨용
    out = []
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f); fr = {}
        for rank, name, price, t, H in towers:
            top = t.matrix_world @ Vector((0, 0, 1.0))
            v = world_to_camera_view(sc, cam, top)
            fr[name] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 2), round(t.scale.z / H, 3)]
        out.append(fr)
    json.dump({"fps": FPS, "frames": out}, open("coords.json", "w")); print("coords", len(out))
elif MODE == "test":
    import time
    for f in [int(ST["t6_rank1"] * FPS) + 60, int(5 * FPS)]:
        sc.frame_set(f); r.filepath = f"{OUT}/test_{f}.png"; t0 = time.time(); bpy.ops.render.render(write_still=True); print("frame", f, round(time.time() - t0, 1), "s", flush=True)
else:
    a, b = (int(argv[2]), int(argv[3])) if len(argv) > 3 else (sc.frame_start, sc.frame_end)
    sc.frame_start, sc.frame_end = a, b
    bpy.ops.render.render(animation=True)
