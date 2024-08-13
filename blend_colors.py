#The section that sets the background color to black using Workbench settings has been removed. This will allow Blender to use its default background settings.

import os
import bpy
from mathutils import Vector
import math

# Main folder path containing subfolders with .obj, .stl, and .glb files
main_folder_path = "C:/Users/winni/Downloads/meshfolder"

# Define the output path
output_path = "C:/Users/winni/Downloads/meshfolder/testing5"

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
def fit_all_meshes_to_bounding_box(mesh_objects, target_size):
    bpy.ops.object.select_all(action='DESELECT')
    for mesh_object in mesh_objects:
        mesh_object.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objects[0]
    bpy.ops.object.join()
    combined_object = bpy.context.view_layer.objects.active

    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bbox = [combined_object.matrix_world @ Vector(corner) for corner in combined_object.bound_box]
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])
    scale_factor = min(target_size[i] / bbox_size[i] for i in range(3)) * 0.85
    combined_object.scale = [scale_factor] * 3
    bpy.ops.object.transform_apply(scale=True)
    return combined_object

# Function to correct the orientation of the mesh if it is upside down
def correct_mesh_orientation(mesh_object):
    z_up_vector = Vector((0, 0, 1))
    up_axis = Vector((0, 0, 1))
    rotation = mesh_object.matrix_world.to_3x3().transposed()
    up_vector = rotation @ up_axis
    if up_vector.dot(z_up_vector) < 0:
        bpy.context.view_layer.objects.active = mesh_object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        mesh_object.rotation_euler.rotate_axis('X', 3.14159)

# Function to dynamically adjust the camera distance based on the bounding box size
def adjust_camera_distance(mesh_object, base_distance=10, padding_factor=1.5):
    bbox = [mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box]
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])
    max_dim = max(bbox_size)
    distance = base_distance + max_dim * padding_factor
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
    camera.location.z = mesh_object.location.z + adjusted_distance
    return adjusted_distance

# Function to rotate the camera around the mesh
def rotate_camera_around_mesh(camera, mesh_object, frame_count, radius, eye_offset=0):
    for frame in range(1, frame_count + 1):
        angle = 2 * math.pi * (frame / frame_count)
        camera.location.x = mesh_object.location.x + radius * math.cos(angle) + eye_offset
        camera.location.y = mesh_object.location.y + radius * math.sin(angle)
        camera.location.z = mesh_object.location.z
        camera.keyframe_insert(data_path="location", frame=frame)
        bpy.context.view_layer.update()
        # Debugging: Print camera position
        print(f"Frame {frame}: Camera location - {camera.location}")

# Function to render the stereoscopic turntable animation
def render_stereoscopic_turntable(mesh_name, output_path, frame_count, radius, eye_distance):
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = frame_count
    
    # Set common render settings
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    bpy.context.scene.render.ffmpeg.ffmpeg_preset = 'BEST'

    # Render for the left eye
    print("Rendering for left eye")
    rotate_camera_around_mesh(camera, combined_object, frame_count, radius, -eye_distance / 2)
    left_eye_video = os.path.join(output_path, f"{mesh_name}_turntable_left.mp4")
    bpy.context.scene.render.filepath = left_eye_video
    bpy.ops.render.render(animation=True)
    print(f"Rendered 360-degree turntable for left eye of {mesh_name}")

    # Render for the right eye
    print("Rendering for right eye")
    rotate_camera_around_mesh(camera, combined_object, frame_count, radius, eye_distance / 2)
    right_eye_video = os.path.join(output_path, f"{mesh_name}_turntable_right.mp4")
    bpy.context.scene.render.filepath = right_eye_video
    bpy.ops.render.render(animation=True)
    print(f"Rendered 360-degree turntable for right eye of {mesh_name}")

    # Combine left and right videos side-by-side using Compositor Nodes
    bpy.context.scene.use_nodes = True
    nodes = bpy.context.scene.node_tree.nodes
    links = bpy.context.scene.node_tree.links
    
    # Clear existing nodes
    for node in nodes:
        nodes.remove(node)
    
    # Add input nodes
    left_movie = nodes.new(type="CompositorNodeMovieClip")
    right_movie = nodes.new(type="CompositorNodeMovieClip")
    
    # Load the rendered videos
    left_movie.clip = bpy.data.movieclips.load(left_eye_video)
    right_movie.clip = bpy.data.movieclips.load(right_eye_video)
    
    # Add translate nodes to position the videos
    translate_left = nodes.new(type="CompositorNodeTranslate")
    translate_right = nodes.new(type="CompositorNodeTranslate")
    
    # Adjust translation to ensure proper side-by-side alignment
    translate_left.inputs["X"].default_value = -bpy.context.scene.render.resolution_x // 2
    translate_right.inputs["X"].default_value = bpy.context.scene.render.resolution_x // 2
    
    # Add an alpha over node to combine the two inputs
    alpha_over = nodes.new(type="CompositorNodeAlphaOver")
    
    # Add an output node
    composite = nodes.new(type="CompositorNodeComposite")
    
    # Link nodes
    links.new(left_movie.outputs["Image"], translate_left.inputs[0])
    links.new(right_movie.outputs["Image"], translate_right.inputs[0])
    links.new(translate_left.outputs["Image"], alpha_over.inputs[1])
    links.new(translate_right.outputs["Image"], alpha_over.inputs[2])
    links.new(alpha_over.outputs["Image"], composite.inputs["Image"])
    
    # Set output path for side-by-side video
    bpy.context.scene.render.filepath = os.path.join(output_path, f"{mesh_name}_turntable_side_by_side.mp4")
    bpy.context.scene.render.resolution_x *= 2  # Double width for side-by-side video
    
    # Render the combined video
    bpy.ops.render.render(animation=True)
    print(f"Rendered side-by-side stereoscopic turntable for {mesh_name}")

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
frame_rate = 6
animation_duration = 10
total_frames = frame_rate * animation_duration
bpy.context.scene.render.fps = frame_rate

# Set the resolution
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

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
camera.data.lens = 70

# Eye distance for stereoscopic effect
eye_distance = 0.1
    
# Iterate through each subfolder in the main folder
for subfolder_name in os.listdir(main_folder_path):
    subfolder_path = os.path.join(main_folder_path, subfolder_name)
    
    if os.path.isdir(subfolder_path):
        print(f"Processing folder: {subfolder_path}")
        
        # List all .obj, .stl, and .glb files in the subfolder
        mesh_files = [f for f in os.listdir(subfolder_path) if f.endswith((".obj", ".stl", ".glb"))]
        
        mesh_objects = []
        for mesh_file in mesh_files:
            mesh_file_path = os.path.join(subfolder_path, mesh_file)
            
            # Import the mesh file
            if mesh_file.endswith(".obj"):
                bpy.ops.wm.obj_import(filepath=mesh_file_path)
            elif mesh_file.endswith(".stl"):
                bpy.ops.import_mesh.stl(filepath=mesh_file_path)
            elif mesh_file.endswith(".glb"):
                bpy.ops.import_scene.gltf(filepath=mesh_file_path)
            print(f"Imported {mesh_file} successfully.")
            
            imported_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
            mesh_objects.extend(imported_objects)
        
        if mesh_objects:
            combined_object = fit_all_meshes_to_bounding_box(mesh_objects, Vector((5, 5, 5)))
            correct_mesh_orientation(combined_object)
            
            # Add a basic material to the mesh if it doesn't have one
            if not combined_object.data.materials:
                mat = bpy.data.materials.new(name="BasicMaterial")
                mat.diffuse_color = (0.8, 0.8, 0.8, 1)  # Light gray color
                combined_object.data.materials.append(mat)
                
            # Apply smooth shading to the mesh
            bpy.context.view_layer.objects.active = combined_object
            bpy.ops.object.shade_smooth()
            
            adjusted_distance = setup_camera_for_rendering(camera, combined_object)
            
            num_positions = 3
            render_flexible_frames(combined_object.name, output_path, num_positions, adjusted_distance)
            
            render_stereoscopic_turntable(combined_object.name, output_path, total_frames, adjusted_distance, eye_distance)
            
            # Ensure the object is removed correctly to avoid errors
            bpy.ops.object.select_all(action='DESELECT')
            if combined_object.name in bpy.context.view_layer.objects:
                bpy.data.objects.remove(bpy.context.view_layer.objects[combined_object.name])
            print(f"Deleted {combined_object.name}.")
        
        # Clean up and remove imported objects to avoid overlap in the next iteration
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete()

print("Rendering completed.")
