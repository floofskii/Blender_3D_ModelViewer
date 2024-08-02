import os
import bpy
from mathutils import Vector
import math

# Folder path to the .obj, .stl, and .glb files
folder_path = "C:/Users/winni/Downloads/dragon"

# Define the output path
output_path = "C:/Users/winni/Downloads/dragon/testing5"  #current path output

# Ensure the output directory exists
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Function to render a frame from a specific camera position
def render_frame(mesh_name, position_name, position, output_path):
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    camera.location = position
    camera.keyframe_insert(data_path="location", frame=1)
    bpy.context.scene.frame_set(1)
    render_filepath = os.path.join(output_path, f"{mesh_name}_{position_name}.png")
    bpy.context.scene.render.filepath = render_filepath
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {position_name} view of {mesh_name} to {render_filepath}")

# Function to fit the mesh into a defined bounding box
def fit_mesh_to_bounding_box(mesh_object, target_size):
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bbox = [mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box]
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])
    scale_factor = min(target_size[i] / bbox_size[i] for i in range(3)) * 0.85  # Add padding by scaling down to 85%
    mesh_object.scale = [scale_factor] * 3
    bpy.ops.object.transform_apply(scale=True)

# Function to correct the orientation of the mesh if it is upside down
def correct_mesh_orientation(mesh_object):
    z_up_vector = Vector((0, 0, 1))
    up_axis = Vector((0, 0, 1))
    rotation = mesh_object.matrix_world.to_3x3().transposed()
    up_vector = rotation @ up_axis
    if up_vector.dot(z_up_vector) < 0:
        bpy.context.view_layer.objects.active = mesh_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        mesh_object.rotation_euler.rotate_axis('X', 3.14159)  # Rotate 180 degrees

# Function to dynamically adjust the camera distance based on the bounding box size
def adjust_camera_distance(mesh_object, base_distance=10, padding_factor=1.5):
    bbox = [mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box]
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])
    max_dim = max(bbox_size)
    distance = base_distance + max_dim * padding_factor  # Add padding based on the bounding box size
    return distance

# Function to center the mesh in the camera view
def center_mesh_in_camera_view(camera, mesh_object):
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bbox_center = sum((Vector(b) for b in mesh_object.bound_box), Vector()) / 8
    bbox_center_world = mesh_object.matrix_world @ bbox_center
    camera_constraint = camera.constraints.new(type='TRACK_TO')
    camera_constraint.target = mesh_object
    camera_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    camera_constraint.up_axis = 'UP_Y'
    bpy.context.scene.camera = camera
    bpy.context.view_layer.update()

# Function to setup camera for rendering
def setup_camera_for_rendering(camera, mesh_object):
    adjusted_distance = adjust_camera_distance(mesh_object)
    center_mesh_in_camera_view(camera, mesh_object)
    camera.location.z = mesh_object.location.z + adjusted_distance  # Adjusting camera height
    return adjusted_distance

# Function to rotate the camera around the mesh
def rotate_camera_around_mesh(camera, mesh_object, frame_count, radius):
    for frame in range(1, frame_count + 1):
        angle = 2 * math.pi * (frame / frame_count)
        camera.location.x = mesh_object.location.x + radius * math.cos(angle)
        camera.location.y = mesh_object.location.y + radius * math.sin(angle)
        camera.location.z = mesh_object.location.z
        camera.keyframe_insert(data_path="location", frame=frame)
        bpy.context.view_layer.update()

# Function to render the turntable animation
def render_turntable(mesh_name, output_path, frame_count, radius):
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frame_count
    rotate_camera_around_mesh(camera, mesh_object, frame_count, radius)
    bpy.context.scene.render.filepath = os.path.join(output_path, f"{mesh_name}_turntable.mp4")
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    bpy.context.scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
    bpy.ops.render.render(animation=True)
    print(f"Rendered 360-degree turntable for {mesh_name}")

# Function to generate flexible camera positions
def generate_camera_positions(n, distance):
    positions = {}
    for i in range(n):
        angle = 2 * math.pi * i / n
        x = distance * math.cos(angle)
        y = distance * math.sin(angle)
        positions[f'angle_{i}'] = Vector((x, y, 0))
    return positions

# Function to render flexible frames around the object
def render_flexible_frames(mesh_name, output_path, num_positions, distance):
    camera_positions = generate_camera_positions(num_positions, distance)
    for position_name, position in camera_positions.items():
        render_frame(mesh_name, position_name, position, output_path)

# Set the frame rate and calculate total frames for the animation
frame_rate = 30  # Desired frame rate
animation_duration = 10  # Duration in seconds
total_frames = frame_rate * animation_duration  # Total number of frames
bpy.context.scene.render.fps = frame_rate  # Set the frame rate

# Set the resolution
bpy.context.scene.render.resolution_x = 3840  # 2K:1920, 1080; 4K: 3840, 2160; 1K: 1280, 720
bpy.context.scene.render.resolution_y = 2160

# Set background color to black using Workbench
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.background_type = 'WORLD'
bpy.context.scene.world.color = (0, 0, 0)  # Set the background color to black

# List all .obj, .stl, and .glb files in the folder
mesh_files = [f for f in os.listdir(folder_path) if f.endswith((".obj", ".stl", ".glb"))]

# Create a light source
bpy.ops.object.light_add(type='SUN', radius=1, location=(10, 10, 10))
light = bpy.context.object
light.data.energy = 5

# Create a camera
bpy.ops.object.camera_add(location=(0, 0, 10))
camera = bpy.context.object
camera.name = 'Camera.001'

# Set the created camera as the active camera
bpy.context.scene.camera = camera

# Zoom in the camera by adjusting the focal length
camera.data.lens = 70  # Increase this value to zoom in

# Process each .obj, .stl, or .glb file
for mesh_file in mesh_files:
    # Full path to the mesh file
    mesh_file_path = os.path.join(folder_path, mesh_file)

    # Import the mesh file
    if mesh_file.endswith(".obj"):
        bpy.ops.import_scene.obj(filepath=mesh_file_path)
    elif mesh_file.endswith(".stl"):
        bpy.ops.import_mesh.stl(filepath=mesh_file_path)
    elif mesh_file.endswith(".glb"):
        bpy.ops.import_scene.gltf(filepath=mesh_file_path)
    print(f"Imported {mesh_file} successfully.")

    # Get the name of the imported mesh object
    imported_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
    if imported_objects:
        mesh_object = imported_objects[0]
        mesh_object_name = mesh_object.name
    else:
        raise RuntimeError("No mesh object was imported.")

    # Add a basic material to the mesh if it doesn't have one
    if not mesh_object.data.materials:
        mat = bpy.data.materials.new(name="BasicMaterial")
        mat.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray color
        mesh_object.data.materials.append(mat)

    # Apply smooth shading to the mesh
    bpy.context.view_layer.objects.active = mesh_object
    bpy.ops.object.shade_smooth()

    # Fit the mesh into a bounding box
    target_size = Vector((5, 5, 5))
    fit_mesh_to_bounding_box(mesh_object, target_size)

    # Correct the orientation of the mesh
    correct_mesh_orientation(mesh_object)

    # Setup the camera for consistent rendering
    adjusted_distance = setup_camera_for_rendering(camera, mesh_object)

    # Define number of camera positions for images
    num_positions = 11  # Change this value to increase or decrease the number of images

    # Render flexible frames around the object
    render_flexible_frames(mesh_object_name, output_path, num_positions, adjusted_distance)

    # Render the turntable animation
    render_turntable(mesh_object_name, output_path, total_frames, adjusted_distance)

    # Delete the imported mesh object
    bpy.data.objects.remove(mesh_object)
    print(f"Deleted {mesh_object_name}.")

print("Rendering completed.")
