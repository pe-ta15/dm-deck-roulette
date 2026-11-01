import bpy
import math
from mathutils import Vector

# Photorealistic, unbranded trading-card deck case opening.
# Rendered headlessly by Blender; final encode is VP8/WebM for browser compatibility.
W, H, FPS, FRAMES = 1280, 720, 24, 96
OUT = "/tmp/case-opening-frames/frame_"
import os
os.makedirs("/tmp/case-opening-frames", exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
if hasattr(scene, "eevee"):
    scene.eevee.taa_render_samples=64
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=100
scene.render.fps=FPS
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.view_settings.view_transform="AgX"
scene.world.color=(0.006,0.009,0.016)
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.006,0.009,0.016,1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.28

def material(name, color, metallic=0.0, roughness=0.4):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metallic
    bs.inputs["Roughness"].default_value=roughness
    return m

def cube(name, loc, scale, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object
    o.name=name
    o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new("Soft manufactured edges","BEVEL")
        mod.width=bevel
        mod.segments=5
        mod.profile=0.5
        mod2=o.modifiers.new("Weighted corner normals","WEIGHTED_NORMAL")
    return o

mat_shell=material("Matte charcoal polymer",(0.022,0.029,0.039),0.08,0.29)
mat_edge=material("Soft-touch edge",(0.045,0.055,0.069),0.12,0.32)
mat_inner=material("Deep black interior",(0.003,0.005,0.009),0.0,0.52)
mat_metal=material("Subtle graphite hinge",(0.12,0.145,0.17),0.72,0.24)
mat_floor=material("Studio floor",(0.009,0.013,0.021),0.12,0.34)

# Studio floor and low, seamless dark environment.
cube("Studio floor",(0,0,-0.18),(200,200,0.25),mat_floor,0.08)

# Case footprint: approximately 2.55 x 1.72; realistic hard-shell proportions.
cx, cy = 0.0, 0.0
base_z=0.13
width, depth=2.55, 1.72
wall=0.13
# Four walls create a visibly hollow storage cavity.
cube("Case front wall",(0,-depth/2+wall/2,0.55),(width,wall,0.84),mat_shell,0.075)
cube("Case rear wall",(0,depth/2-wall/2,0.55),(width,wall,0.84),mat_shell,0.075)
cube("Case left wall",(-width/2+wall/2,0,0.55),(wall,depth-2*wall,0.84),mat_shell,0.075)
cube("Case right wall",(width/2-wall/2,0,0.55),(wall,depth-2*wall,0.84),mat_shell,0.075)
cube("Case bottom",(0,0,0.18),(width-0.12,depth-0.12,0.22),mat_shell,0.075)
cube("Inner padded base",(0,0,0.305),(width-0.36,depth-0.36,0.025),mat_inner,0.025)
# Thin inner lip around the opening.
cube("Front inner lip",(0,-depth/2+wall+0.035,0.96),(width-0.22,0.055,0.075),mat_edge,0.018)
cube("Rear inner lip",(0,depth/2-wall-0.035,0.96),(width-0.22,0.055,0.075),mat_edge,0.018)
cube("Left inner lip",(-width/2+wall+0.035,0,0.96),(0.055,depth-0.38,0.075),mat_edge,0.018)
cube("Right inner lip",(width/2-wall-0.035,0,0.96),(0.055,depth-0.38,0.075),mat_edge,0.018)

# Lid is a thick, unmarked, slightly textured single-piece shell.
hinge=bpy.data.objects.new("Lid hinge pivot",None)
scene.collection.objects.link(hinge)
hinge.location=(0,depth/2-0.02,1.015)
lid=cube("Plain hinged lid",(0,0,0),(width+0.04,depth+0.10,0.22),mat_shell,0.085)
lid.parent=hinge
lid.location=(0,-depth/2+0.02,0.045)
lid.rotation_euler=(0,0,0)
# Inner panel on the lid underside, also plain.
inner_lid=cube("Lid inner panel",(0,0,0),(width-0.24,depth-0.30,0.035),mat_inner,0.045)
inner_lid.parent=hinge
inner_lid.location=(0,-depth/2+0.02,-0.085)
# Hinge barrel along the rear edge.
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.075, depth=width-0.28,
                                    location=(0,depth/2-0.01,1.015), rotation=(0,math.pi/2,0))
hinge_barrel=bpy.context.object
hinge_barrel.name="Continuous rear hinge"
hinge_barrel.data.materials.append(mat_metal)
bev=hinge_barrel.modifiers.new("Hinge edge bevel","BEVEL"); bev.width=0.018; bev.segments=3
hinge_barrel.modifiers.new("Hinge normals","WEIGHTED_NORMAL")

# Small unbranded front catch, physically attached to the front face.
catch=cube("Front magnetic catch",(0,-depth/2-0.012,0.94),(0.34,0.045,0.12),mat_metal,0.035)

# Camera: close three-quarter product view, centered with room for the light bloom.
bpy.ops.object.camera_add(location=(4.25,-6.8,4.55))
camera=bpy.context.object
camera.name="Product camera"
target=Vector((0,0,0.78))
camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type="ORTHO"
camera.data.ortho_scale=6.35
scene.camera=camera
camera.data.lens=55

def area(name, loc, power, color, size, target=(0,0,0.5), shape="DISK", size_y=None):
    bpy.ops.object.light_add(type="AREA", location=loc)
    l=bpy.context.object; l.name=name
    l.data.energy=power; l.data.color=color; l.data.shape=shape; l.data.size=size
    if size_y and hasattr(l.data,"size_y"): l.data.size_y=size_y
    l.rotation_euler=(Vector(target)-l.location).to_track_quat("-Z","Y").to_euler()
    return l

area("Large cool softbox",(0,-4.5,6.5),780,(0.73,0.82,1.0),5.0)
area("Warm edge strip",(4.0,1.5,4.2),1050,(1.0,0.77,0.52),3.2)
area("Blue rim light",(-4.0,2.2,3.3),1250,(0.38,0.62,1.0),3.0)
area("Front fill",(1.5,-5.0,2.4),250,(1.0,1.0,1.0),3.5)

# Internal light blooms as the lid releases.
bpy.ops.object.light_add(type="AREA", location=(0,0,0.78))
core=bpy.context.object
core.name="Interior reveal light"
core.data.energy=0
core.data.color=(1.0,0.84,0.56)
core.data.shape="DISK"
core.data.size=1.0
core.rotation_euler=(0,0,0)
core.data.keyframe_insert(data_path="energy",frame=1)
core.data.energy=0; core.data.keyframe_insert(data_path="energy",frame=39)
core.data.energy=260; core.data.keyframe_insert(data_path="energy",frame=56)
core.data.energy=1900; core.data.keyframe_insert(data_path="energy",frame=76)
core.data.energy=5200; core.data.keyframe_insert(data_path="energy",frame=91)
core.data.energy=5200; core.data.keyframe_insert(data_path="energy",frame=96)

# Opening animation: subtle settling, latch release, then a decisive hinged swing.
for frame, angle in [(1,0),(35,0),(40,-0.10),(47,-0.55),(58,-1.42),(69,-2.15),(78,-2.32),(96,-2.32)]:
    hinge.rotation_euler.x=angle
    hinge.keyframe_insert(data_path="rotation_euler",frame=frame,index=0)
# Slight camera push-in during the reveal, then whiteout.
for frame, scale in [(1,6.55),(34,6.55),(55,6.25),(78,5.95),(90,5.85),(96,5.85)]:
    camera.data.ortho_scale=scale
    camera.data.keyframe_insert(data_path="ortho_scale",frame=frame)

# A restrained shake at the instant the catch releases.
for frame, z in [(1,4.55),(39,4.55),(42,4.51),(45,4.58),(48,4.55),(96,4.55)]:
    camera.location.z=z
    camera.keyframe_insert(data_path="location",frame=frame,index=2)

# Whiteout is a camera exposure ramp: the whole rendered image blooms, hiding the cut.
for frame, exposure in [(1,0.0),(78,0.0),(84,1.1),(89,3.0),(93,5.0),(96,5.0)]:
    scene.view_settings.exposure=exposure
    scene.view_settings.keyframe_insert(data_path="exposure",frame=frame)

scene.frame_start=1
scene.frame_end=FRAMES
scene.render.image_settings.color_mode="RGB"
scene.render.filepath=OUT
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.use_file_extension=True
scene.render.film_transparent=False
scene.render.image_settings.color_depth="8"
scene.render.resolution_x=W
scene.render.resolution_y=H
scene.render.resolution_percentage=100
scene.frame_set(1)
bpy.ops.render.render(animation=True)
print("Rendered 3D deck case frames")
