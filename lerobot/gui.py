import dearpygui.dearpygui as dpg
import subprocess
import threading
import os

# To store references to input fields
input_fields = {}

def start_recording_callback(sender, app_data, user_data):
    base_command = ["python", "lerobot/scripts/control_robot.py"]

    # --- Robot Config ---
    robot_type = dpg.get_value(input_fields["robot_type"])
    if robot_type:
        base_command.extend([f"--robot.type={robot_type}"])

    # --- Control Config ---
    base_command.append("--control.type=record")

    repo_id = dpg.get_value(input_fields["repo_id"])
    if repo_id:
        base_command.extend([f"--control.repo_id={repo_id}"])
    else:
        dpg.set_value(input_fields["output_text"], "Error: Repository ID is required.\n")
        return

    single_task = dpg.get_value(input_fields["single_task"])
    if single_task:
        base_command.extend([f"--control.single_task='{single_task}'"]) # Single quotes for tasks with spaces
    else:
        dpg.set_value(input_fields["output_text"], "Error: Single Task description is required.\n")
        return

    if dpg.get_value(input_fields["root"]):
        base_command.extend([f"--control.root={dpg.get_value(input_fields['root'])}"])
    if dpg.get_value(input_fields["fps"]):
        base_command.extend([f"--control.fps={dpg.get_value(input_fields['fps'])}"])

    base_command.extend([f"--control.warmup_time_s={dpg.get_value(input_fields['warmup_time_s'])}"])
    base_command.extend([f"--control.episode_time_s={dpg.get_value(input_fields['episode_time_s'])}"])
    base_command.extend([f"--control.reset_time_s={dpg.get_value(input_fields['reset_time_s'])}"])
    base_command.extend([f"--control.num_episodes={dpg.get_value(input_fields['num_episodes'])}"])
    base_command.extend([f"--control.video={dpg.get_value(input_fields['video'])}"])
    base_command.extend([f"--control.push_to_hub={dpg.get_value(input_fields['push_to_hub'])}"])
    base_command.extend([f"--control.private={dpg.get_value(input_fields['private'])}"])

    tags_str = dpg.get_value(input_fields["tags"])
    if tags_str:
        # Assuming tags are comma-separated in the input field
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        # Format for CLI: --control.tags='["tag1","tag2"]' or --control.tags=tag1 tag2
        # The script expects nargs='*', so space separated should work.
        # However, if a tag itself has a space, it might break.
        # The safest is to pass it like --control.tags '["tag1", "tag with space"]'
        # For now, let's try space separated, simpler for user input.
        if tags_list:
             base_command.append("--control.tags")
             base_command.extend(tags_list)


    base_command.extend([f"--control.num_image_writer_processes={dpg.get_value(input_fields['num_image_writer_processes'])}"])
    base_command.extend([f"--control.num_image_writer_threads_per_camera={dpg.get_value(input_fields['num_image_writer_threads_per_camera'])}"])
    base_command.extend([f"--control.display_data={dpg.get_value(input_fields['display_data'])}"])
    base_command.extend([f"--control.play_sounds={dpg.get_value(input_fields['play_sounds'])}"])
    base_command.extend([f"--control.resume={dpg.get_value(input_fields['resume'])}"])

    # For simplicity, execute in the workspace root
    # The script lerobot/scripts/control_robot.py should handle relative paths if necessary
    command_to_run = " ".join(base_command)
    dpg.set_value(input_fields["output_text"], f"Executing: {command_to_run}\n")

    def run_script():
        # Run in the workspace root.
        # The user's workspace is available via an environment variable or a known path.
        # For now, assuming the script is run from the workspace root.
        process = subprocess.Popen(
            command_to_run,
            shell=True, # Added shell=True for easier command construction with spaces/quotes
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirect stderr to stdout
            text=True,
            cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Run from lerobot project root
        )
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                current_text = dpg.get_value(input_fields["output_text"])
                dpg.set_value(input_fields["output_text"], current_text + output)
        rc = process.poll()
        current_text = dpg.get_value(input_fields["output_text"])
        dpg.set_value(input_fields["output_text"], current_text + f"\nProcess finished with exit code {rc}\n")

    thread = threading.Thread(target=run_script)
    thread.start()


def main():
    dpg.create_context()
    dpg.create_viewport(title='LeRobot GUI', width=1000, height=800) # Increased window size
    dpg.setup_dearpygui()

    with dpg.window(label="Data Recording", tag="data_recording_window"):
        dpg.add_text("LeRobot Data Recording Controls")
        dpg.add_separator()

        # Robot Config
        dpg.add_text("Robot Configuration")
        input_fields["robot_type"] = dpg.add_input_text(label="Robot Type (e.g., so100, lekiwi)", default_value="so100") # Added default
        dpg.add_separator()

        # Control Config - Record
        dpg.add_text("Recording Configuration")
        input_fields["repo_id"] = dpg.add_input_text(label="Repo ID (e.g., your_username/dataset_name)")
        input_fields["single_task"] = dpg.add_input_text(label="Task Description")
        input_fields["root"] = dpg.add_input_text(label="Root Directory (optional, e.g., data/my_dataset)")
        input_fields["fps"] = dpg.add_input_int(label="FPS (optional)", default_value=30) # Default based on examples
        input_fields["warmup_time_s"] = dpg.add_input_float(label="Warmup Time (s)", default_value=10.0)
        input_fields["episode_time_s"] = dpg.add_input_float(label="Episode Time (s)", default_value=60.0)
        input_fields["reset_time_s"] = dpg.add_input_float(label="Reset Time (s)", default_value=60.0)
        input_fields["num_episodes"] = dpg.add_input_int(label="Number of Episodes", default_value=50)
        
        input_fields["tags"] = dpg.add_input_text(label="Tags (comma-separated, optional)")
        
        dpg.add_separator()
        dpg.add_text("Advanced Settings")
        input_fields["video"] = dpg.add_checkbox(label="Encode Video", default_value=True)
        input_fields["push_to_hub"] = dpg.add_checkbox(label="Push to Hub", default_value=True)
        input_fields["private"] = dpg.add_checkbox(label="Private Hub Repo", default_value=False)
        input_fields["num_image_writer_processes"] = dpg.add_input_int(label="Num Image Writer Processes", default_value=0)
        input_fields["num_image_writer_threads_per_camera"] = dpg.add_input_int(label="Num Image Writer Threads/Camera", default_value=4)
        input_fields["display_data"] = dpg.add_checkbox(label="Display Camera Data", default_value=False)
        input_fields["play_sounds"] = dpg.add_checkbox(label="Play Sounds", default_value=True)
        input_fields["resume"] = dpg.add_checkbox(label="Resume Recording", default_value=False)
        dpg.add_separator()

        dpg.add_button(label="Start Recording", callback=start_recording_callback)
        dpg.add_separator()

        dpg.add_text("Output:")
        input_fields["output_text"] = dpg.add_input_text(label="", multiline=True, default_value="", width=-1, height=300, readonly=True)


    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == '__main__':
    main() 