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
scene.world.color=(1.0,1.0,1.0)
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value=(1.0,1.0,1.0,1)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.8

def material(name, color, metallic=0.0, roughness=0.4):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metallic
    bs.inputs["Roughness"].default_value=roughness
    if "Transmission Weight" in bs.inputs:
        bs.inputs["Transmission Weight"].default_value=0.28 if "milky" in name.lower() else 0.0
    if "Coat Weight" in bs.inputs:
        bs.inputs["Coat Weight"].default_value=0.22 if "milky" in name.lower() else 0.0
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

mat_shell=material("Milky translucent white polypropylene",(0.82,0.87,0.86),0.0,0.22)
mat_edge=material("Translucent milky edge",(0.91,0.94,0.92),0.0,0.24)
mat_inner=material("Soft grey inner cavity",(0.25,0.29,0.28),0.0,0.38)
mat_metal=material("Pale translucent hinge",(0.67,0.72,0.70),0.25,0.25)
mat_floor=material("Seamless white studio floor",(0.96,0.97,0.96),0.0,0.5)

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

area("Large softbox",(0,-4.5,6.5),1050,(1.0,1.0,1.0),5.0)
area("Soft warm edge strip",(4.0,1.5,4.2),700,(1.0,0.91,0.78),3.2)
area("Neutral rim light",(-4.0,2.2,3.3),650,(0.88,0.94,1.0),3.0)
area("Front fill",(1.5,-5.0,2.4),500,(1.0,1.0,1.0),3.5)

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

# Light leaks forcefully through the opening seam as the lid releases.
beam_mat=bpy.data.materials.new("Soft champagne-white energy beams")
beam_mat.diffuse_color=(1.0,0.91,0.70,0.22)
beam_mat.use_nodes=True
beam_nodes=beam_mat.node_tree.nodes
beam_bs=beam_nodes.get("Principled BSDF")
beam_bs.inputs["Base Color"].default_value=(1.0,0.88,0.62,1)
if "Emission Color" in beam_bs.inputs:
    beam_bs.inputs["Emission Color"].default_value=(1.0,0.83,0.52,1)
if "Emission Strength" in beam_bs.inputs:
    beam_bs.inputs["Emission Strength"].default_value=2.2
beam_bs.inputs["Roughness"].default_value=0.28
if "Alpha" in beam_bs.inputs:
    beam_bs.inputs["Alpha"].default_value=0.20
if hasattr(beam_mat, "surface_render_method"):
    beam_mat.surface_render_method="DITHERED"

for index, (x, y, tilt) in enumerate([(-0.42,0.0,-0.24),(0.0,0.0,0.0),(0.42,0.0,0.24)]):
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.72, radius2=0.035, depth=2.5,
                                    location=(x,y,2.15), rotation=(0,tilt,0))
    beam=bpy.context.object
    beam.name=f"Opening light beam {index+1}"
    beam.data.materials.append(beam_mat)
    beam.scale=(0.001,0.001,0.001)
    beam.keyframe_insert(data_path="scale",frame=39)
    beam.scale=(0.72,0.72,0.55)
    beam.keyframe_insert(data_path="scale",frame=45)
    beam.scale=(1.0,1.0,1.0)
    beam.keyframe_insert(data_path="scale",frame=57)
    beam.scale=(1.18,1.18,1.12)
    beam.keyframe_insert(data_path="scale",frame=70)
    beam.scale=(1.18,1.18,1.12)
    beam.keyframe_insert(data_path="scale",frame=96)

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
for frame, exposure in [(1,0.0),(76,0.0),(82,1.0),(88,2.8),(92,5.0),(96,5.0)]:
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
