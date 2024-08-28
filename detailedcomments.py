#following is the final script with detailed comments to understand how the code works, explaining each function in detail.

# Import necessary modules
import os  # Standard Python module for interacting with the operating system
import bpy  # Blender Python API for scripting
from mathutils import Vector  # Blender math utilities for working with vectors
import math  # Standard Python module for mathematical operations

# Define the main folder path where subfolders containing 3D mesh files (.obj, .stl, .glb) are located
main_folder_path = "C:/Users/winni/Downloads/mainmeshfolder"

# Define the output path where processed files and renders will be saved
output_path = "C:/Users/winni/Downloads/mainmeshfolder/testing77"

# Ensure the output directory exists, if not, create it
if not os.path.exists(output_path):
    os.makedirs(output_path)

# Path to the HDRI (High Dynamic Range Image) file used for environment lighting
hdri_path = "C:/Users/winni/Downloads/mainmeshfolder/overcast_soil_puresky_4k.exr"

# Function to set up HDRI environment lighting in the scene
def setup_hdri_lighting(hdri_path):
    world = bpy.context.scene.world  # Access the world settings of the current scene
    world.use_nodes = True  # Enable node-based environment lighting
    nodes = world.node_tree.nodes  # Access the nodes in the world node tree
    links = world.node_tree.links  # Access the links (connections) between nodes
    
    # Clear any existing nodes in the world node tree
    nodes.clear()
    
    # Add an Environment Texture node to use the HDRI for lighting
    env_texture_node = nodes.new(type='ShaderNodeTexEnvironment')
    env_texture_node.image = bpy.data.images.load(hdri_path)  # Load the HDRI file
    
    # Add Mapping and Texture Coordinate nodes to control HDRI placement and rotation
    mapping_node = nodes.new(type='ShaderNodeMapping')
    tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    
    # Connect the Texture Coordinate node to the Mapping node, and then to the Environment Texture node
    links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], env_texture_node.inputs['Vector'])
    
    # Add a Background node to hold the HDRI lighting
    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.inputs['Strength'].default_value = 1.0  # Set the initial brightness of the HDRI
    
    # Link the Environment Texture node to the Background node
    links.new(env_texture_node.outputs['Color'], background_node.inputs['Color'])
    
    # Add the Output node to connect the Background node to the world output
    output_node = nodes.new(type='ShaderNodeOutputWorld')
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

# Disable transparency in the render settings to ensure the background is not transparent
bpy.context.scene.render.film_transparent = False

# Function to set up color management settings for the scene
def setup_color_management():
    bpy.context.scene.view_settings.view_transform = 'Raw'  # Use 'Raw' to prevent color correction
    bpy.context.scene.view_settings.look = 'None'  # No additional look applied
    bpy.context.scene.view_settings.exposure = -0.426  # Adjust exposure to control brightness
    bpy.context.scene.view_settings.gamma = 1.567  # Adjust gamma for contrast

# Function to combine all selected mesh objects into a single object
def combine_objects():
    bpy.ops.object.select_all(action='DESELECT')  # Deselect all objects
    bpy.ops.object.select_by_type(type='MESH')  # Select all mesh objects
    bpy.ops.object.join()  # Join the selected meshes into one

# Function to make a mesh's data unique, so it's independent from other objects
def make_mesh_unique(mesh_object):
    mesh_object.data = mesh_object.data.copy()  # Copy the mesh data to make it unique

# Function to render a frame from a specific camera position
def render_frame(mesh_name, position_name, position, output_path):
    bpy.context.scene.render.image_settings.file_format = 'PNG'  # Set the output file format to PNG
    camera.location = position  # Move the camera to the specified position
    camera.keyframe_insert(data_path="location", frame=1)  # Insert a keyframe for camera position
    bpy.context.scene.frame_set(1)  # Set the frame to 1
    render_filepath = os.path.join(output_path, f"{mesh_name}_{position_name}.png")  # Define the output path for the render
    bpy.context.scene.render.filepath = render_filepath  # Set the render file path
    bpy.ops.render.render(write_still=True)  # Render the image and save it
    print(f"Rendered {position_name} view of {mesh_name} to {render_filepath}")

# Function to fit a mesh into a defined bounding box size
def fit_mesh_to_bounding_box(mesh_object, target_size):
    make_mesh_unique(mesh_object)  # Make the mesh data unique
    bpy.context.view_layer.objects.active = mesh_object  # Set the mesh as the active object
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')  # Set the object's origin to its center of mass
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # Apply location, rotation, and scale transformations
    bbox = [mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box]  # Calculate the world coordinates of the bounding box corners
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])  # Calculate the size of the bounding box
    scale_factor = min(target_size[i] / bbox_size[i] for i in range(3)) * 0.85  # Calculate the scaling factor and add padding
    mesh_object.scale = [scale_factor] * 3  # Scale the mesh uniformly
    bpy.ops.object.transform_apply(scale=True)  # Apply the scaling transformation

# Function to correct the orientation of a mesh if it is upside down
def correct_mesh_orientation(mesh_object):
    make_mesh_unique(mesh_object)  # Make the mesh data unique
    z_up_vector = Vector((0, 0, 1))  # Define the up vector along the Z-axis
    up_axis = Vector((0, 0, 1))  # Define the axis that should be up
    rotation = mesh_object.matrix_world.to_3x3().transposed()  # Get the transposed rotation matrix
    up_vector = rotation @ up_axis  # Calculate the current up vector
    if up_vector.dot(z_up_vector) < 0:  # Check if the mesh is upside down
        bpy.context.view_layer.objects.active = mesh_object  # Set the mesh as the active object
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # Apply location, rotation, and scale transformations
        mesh_object.rotation_euler.rotate_axis('X', 3.14159)  # Rotate the mesh 180 degrees around the X-axis to correct orientation

# Function to dynamically adjust the camera distance based on the bounding box size
def adjust_camera_distance(mesh_object, base_distance=10, padding_factor=1.5):
    bbox = [mesh_object.matrix_world @ Vector(corner) for corner in mesh_object.bound_box]  # Calculate the world coordinates of the bounding box corners
    bbox_size = Vector([max(coord) - min(coord) for coord in zip(*bbox)])  # Calculate the size of the bounding box
    max_dim = max(bbox_size)  # Find the largest dimension of the bounding box
    distance = base_distance + max_dim * padding_factor  # Calculate the camera distance with padding
    return distance  # Return the calculated distance

# Function to center the mesh in the camera view
def center_mesh_in_camera_view(camera, mesh_object):
    bpy.context.view_layer.objects.active = mesh_object  # Set the mesh as the active object
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')  # Set the object's origin to its bounding box center
    bbox_center = sum((Vector(b) for b in mesh_object.bound_box), Vector()) / 8  # Calculate the center of the bounding box
    bbox_center_world = mesh_object.matrix_world @ bbox_center  # Transform the center to world coordinates
    camera_constraint = camera.constraints.new(type='TRACK_TO')  # Add a constraint to track the object
    camera_constraint.target = mesh_object  # Set the target of the constraint to the mesh
    camera_constraint.track_axis = 'TRACK_NEGATIVE_Z'  # Set the camera to track along the negative Z-axis
    camera_constraint.up_axis = 'UP_Y'  # Set the up axis to Y
    bpy.context.scene.camera = camera  # Set the camera as the active camera
    bpy.context.view_layer.update()  # Update the view layer

# Function to set up the camera for rendering
def setup_camera_for_rendering(camera, mesh_object):
    adjusted_distance = adjust_camera_distance(mesh_object)  # Adjust the camera distance based on the mesh size
    center_mesh_in_camera_view(camera, mesh_object)  # Center the mesh in the camera view
    camera.location.z = mesh_object.location.z + adjusted_distance  # Position the camera above the mesh
    return adjusted_distance  # Return the adjusted camera distance

# Function to rotate the camera around the mesh for a turntable animation
def rotate_camera_around_mesh(camera, mesh_object, frame_count, radius, eye_offset=0):
    for frame in range(1, frame_count + 1):  # Iterate through each frame
        angle = 2 * math.pi * (frame / frame_count)  # Calculate the rotation angle for this frame
        camera.location.x = mesh_object.location.x + radius * math.cos(angle) + eye_offset  # Calculate the camera's X position
        camera.location.y = mesh_object.location.y + radius * math.sin(angle)  # Calculate the camera's Y position
        camera.location.z = mesh_object.location.z  # Keep the camera at the mesh's Z position
        camera.keyframe_insert(data_path="location", frame=frame)  # Insert a keyframe for the camera's location
        bpy.context.view_layer.update()  # Update the view layer
        print(f"Frame {frame}: Camera location - {camera.location}")  # Print the camera's location for debugging

# Function to render a stereoscopic turntable animation with left and right eye views
def render_stereoscopic_turntable(subfolder_name, mesh_name, output_path, frame_count, radius, eye_distance):
    bpy.context.scene.frame_start = 1  # Set the start frame
    bpy.context.scene.frame_end = frame_count  # Set the end frame
    
    # Set common render settings
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = H264'  # AV1
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'MEDIUM' # LOSSLESS, HIGH, PERC_LOSELESS, MEDIUM, LOW, LOWEST
    bpy.context.scene.render.ffmpeg.ffmpeg_preset = 'BEST'  #BEST, GOOD, REALTIME

    # Render for the left eye
    print("Rendering for left eye")
    rotate_camera_around_mesh(camera, mesh_object, frame_count, radius, -eye_distance / 2)  # Rotate the camera for the left eye
    left_eye_video = os.path.join(output_path, f"{subfolder_name}{mesh_name}_turntable_left{eye_distance}mm.mp4")  # Define the output path for the left eye video
    bpy.context.scene.render.filepath = left_eye_video  # Set the file path for the left eye render
    bpy.ops.render.render(animation=True)  # Render the left eye animation
    print(f"Rendered 360-degree turntable for left eye of {mesh_name}")

    # Render for the right eye
    print("Rendering for right eye")
    rotate_camera_around_mesh(camera, mesh_object, frame_count, radius, eye_distance / 2)  # Rotate the camera for the right eye
    right_eye_video = os.path.join(output_path, f"{subfolder_name}{mesh_name}_turntable_right{eye_distance}mm.mp4")  # Define the output path for the right eye video
    bpy.context.scene.render.filepath = right_eye_video  # Set the file path for the right eye render
    bpy.ops.render.render(animation=True)  # Render the right eye animation
    print(f"Rendered 360-degree turntable for right eye of {mesh_name}")
    
    # Commented out side-by-side video generation
    # Combine left and right videos side-by-side using Compositor Nodes
    # bpy.context.scene.use_nodes = True
    # nodes = bpy.context.scene.node_tree.nodes
    # links = bpy.context.scene.node_tree.links
    
    # Clear existing nodes
    # for node in nodes:
    #     nodes.remove(node)
    
    # Add input nodes
    # left_movie = nodes.new(type="CompositorNodeMovieClip")
    # right_movie = nodes.new(type="CompositorNodeMovieClip")
    
    # Load the rendered videos
    # left_movie.clip = bpy.data.movieclips.load(left_eye_video)
    # right_movie.clip = bpy.data.movieclips.load(right_eye_video)
    
    # Add translate nodes to position the videos
    # translate_left = nodes.new(type="CompositorNodeTranslate")
    # translate_right = nodes.new(type="CompositorNodeTranslate")
    
    # Adjust translation to ensure proper side-by-side alignment
    # translate_left.inputs["X"].default_value = -bpy.context.scene.render.resolution_x // 2
    # translate_right.inputs["X"].default_value = bpy.context.scene.render.resolution_x // 2
    
    # Add an alpha over node to combine the two inputs
    # alpha_over = nodes.new(type="CompositorNodeAlphaOver")
    
    # Add an output node
    # composite = nodes.new(type="CompositorNodeComposite")
    
    # Link nodes
    # links.new(left_movie.outputs["Image"], translate_left.inputs[0])
    # links.new(right_movie.outputs["Image"], translate_right.inputs[0])
    # links.new(translate_left.outputs["Image"], alpha_over.inputs[1])
    # links.new(translate_right.outputs["Image"], alpha_over.inputs[2])
    # links.new(alpha_over.outputs["Image"], composite.inputs["Image"])
    
    # Set output path for side-by-side video
    # bpy.context.scene.render.filepath = os.path.join(output_path, f"{mesh_name}_turntable_side_by_side.mp4")
    # bpy.context.scene.render.resolution_x *= 2  # Double width for side-by-side video
    
    # Render the combined video
    # bpy.ops.render.render(animation=True)
    # print(f"Rendered side-by-side stereoscopic turntable for {mesh_name}")

# Function to generate flexible camera positions around the object
def generate_camera_positions(n, distance):
    positions = {}
    for i in range(n):  # Iterate to generate 'n' positions
        angle = 2 * math.pi * i / n  # Calculate the angle for this position
        x = distance * math.cos(angle)  # Calculate the X position of the camera
        y = distance * math.sin(angle)  # Calculate the Y position of the camera
        positions[f'angle_{i}'] = Vector((x, y, 0))  # Store the position as a vector
    return positions  # Return the dictionary of camera positions

# Function to render multiple frames from different camera positions
def render_flexible_frames(subfolder_name, mesh_name, output_path, num_positions, distance):
    camera_positions = generate_camera_positions(num_positions, distance)  # Generate camera positions
    for position_name, position in camera_positions.items():  # Iterate over the generated positions
        render_frame(mesh_name, position_name, position, output_path)  # Render a frame for each position

# Set the frame rate and calculate the total number of frames for the animation
frame_rate = 6  # Set the frame rate to 6 frames per second
animation_duration = 10  # Set the animation duration to 10 seconds
total_frames = frame_rate * animation_duration  # Calculate the total number of frames
bpy.context.scene.render.fps = frame_rate  # Set the scene's frame rate

# Set the resolution of the output images/videos
bpy.context.scene.render.resolution_x = 1280  # Set the horizontal resolution
bpy.context.scene.render.resolution_y = 720  # Set the vertical resolution

# Use the Cycles render engine (Blender's ray-tracing engine)
bpy.context.scene.render.engine = 'CYCLES'  # Set the render engine to Cycles
bpy.context.scene.cycles.samples = 128  # Set the number of samples for rendering (higher is better quality)
bpy.context.scene.cycles.use_adaptive_sampling = True  # Enable adaptive sampling to reduce render times

# Uncomment the following lines to use the Eevee render engine instead (Blender's real-time engine)
# bpy.context.scene.render.engine = 'BLENDER_EEVEE'
# bpy.context.scene.eevee.taa_render_samples = 64  # Set the number of samples for Eevee
# bpy.context.scene.eevee.use_gtao = False  # Disable Ambient Occlusion in Eevee
# bpy.context.scene.eevee.use_bloom = False  # Disable Bloom in Eevee
# bpy.context.scene.eevee.use_ssr = False  # Disable Screen Space Reflections in Eevee

# Set up the HDRI environment lighting using the specified HDRI file
setup_hdri_lighting(hdri_path)

# Apply the color management settings defined earlier
setup_color_management()

# Create a camera in the scene at the specified location
bpy.ops.object.camera_add(location=(0, 0, 10))
camera = bpy.context.object  # Store the created camera object
camera.name = 'Camera.001'  # Name the camera

# Set the created camera as the active camera for rendering
bpy.context.scene.camera = camera

# Zoom in the camera by adjusting the focal length
camera.data.lens = 70  # Set the camera's focal length to 70mm

# Disable Depth of Field to avoid blurriness in the render
camera.data.dof.use_dof = False

# Add a soft area light to the scene for additional lighting
bpy.ops.object.light_add(type='AREA', location=(5, 5, 5))
area_light = bpy.context.object  # Store the created light object
area_light.data.energy = 100  # Set the light's energy (brightness)
area_light.data.size = 10  # Set the size of the light to create soft shadows
area_light.data.use_shadow = False  # Disable shadows for this light

# Add a sun lamp for directional light
bpy.ops.object.light_add(type='SUN', location=(10, 10, 10))
sun_light = bpy.context.object  # Store the created sun lamp object
sun_light.data.energy = 1  # Set the sun lamp's energy (brightness)
sun_light.data.use_shadow = False  # Disable shadows for this light

# Add point lights around the object for better illumination
point_light_positions = [
    (5, 5, 10),
    (-5, -5, 10),
    (-5, 5, 10),
    (5, -5, 10)
]

# Create point lights at the specified positions
for position in point_light_positions:
    bpy.ops.object.light_add(type='POINT', location=position)
    point_light = bpy.context.object  # Store the created point light object
    point_light.data.energy = 50  # Set the point light's energy (brightness)
    point_light.data.use_shadow = False  # Disable shadows for these lights

# Iterate through each subfolder in the main folder
for subfolder_name in os.listdir(main_folder_path):
    subfolder_path = os.path.join(main_folder_path, subfolder_name)
    
    if os.path.isdir(subfolder_path):  # Check if the path is a directory
        print(f"Processing folder: {subfolder_path}")

        # Create an output folder for each subfolder
        subfolder_output_path = os.path.join(output_path, subfolder_name)
        if not os.path.exists(subfolder_output_path):
            os.makedirs(subfolder_output_path)
        
        # List all .obj, .stl, and .glb files in the subfolder
        mesh_files = [f for f in os.listdir(subfolder_path) if f.endswith((".obj", ".stl", ".glb"))]
        
        for mesh_file in mesh_files:
            # Clear the scene before processing the new mesh
            bpy.ops.object.select_all(action='DESELECT')
            bpy.ops.object.select_by_type(type='MESH')
            bpy.ops.object.delete()
            
            mesh_file_path = os.path.join(subfolder_path, mesh_file)
            
            # Import the mesh file using the appropriate method
            if mesh_file.endswith(".obj"):
                bpy.ops.wm.obj_import(filepath=mesh_file_path)
            elif mesh_file.endswith(".stl"):
                bpy.ops.wm.stl_import(filepath=mesh_file_path)
            elif mesh_file.endswith(".glb"):
                bpy.ops.wm.gltf_import(filepath=mesh_file_path)
            print(f"Imported {mesh_file} successfully.")
            
            # Combine all imported objects into one
            combine_objects()
            
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
            
            # Process each mesh individually
            fit_mesh_to_bounding_box(mesh_object, Vector((5, 5, 5)))
            correct_mesh_orientation(mesh_object)
            
            # Apply smooth shading to the mesh
            bpy.context.view_layer.objects.active = mesh_object
            bpy.ops.object.shade_smooth()
            
            adjusted_distance = setup_camera_for_rendering(camera, mesh_object)
            
            num_positions = 3
            render_flexible_frames(subfolder_name, mesh_object.name, subfolder_output_path, num_positions, adjusted_distance)
            
            # Render stereoscopic turntables for different interocular distances (IODs)
            for iod in [55, 60, 65]:
                render_stereoscopic_turntable(subfolder_name, mesh_object.name, subfolder_output_path, total_frames, adjusted_distance, eye_distance=iod / 1000)
            
            # Ensure the object is removed correctly to avoid errors
            bpy.ops.object.select_all(action='DESELECT')
            bpy.context.view_layer.objects.active = None
            
            # Now, after all operations, delete the mesh object
            bpy.data.objects.remove(mesh_object)
            print(f"Deleted {mesh_object_name}.")
                    
        # Clean up and remove any leftover imported objects to avoid overlap in the next iteration
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete()

print("Rendering completed.")
