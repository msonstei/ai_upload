import os
import sys

def replace_spaces_with_underscores(directory_path):
    """
    Recursively renames files and directories to replace spaces with underscores.

    Args:
        directory_path (str): The path to the starting directory.
    """
    print(f"Starting rename process in: {directory_path}")
    
    # Use os.walk with topdown=False to rename contents before their parent directory.
    # This prevents issues where renaming a parent directory makes its subdirectories inaccessible.
    for root, dirs, files in os.walk(directory_path, topdown=False):
        # 1. Rename files
        for filename in files:
            if ' ' in filename:
                old_filepath = os.path.join(root, filename)
                new_filename = filename.replace(' ', '_')
                new_filepath = os.path.join(root, new_filename)
                try:
                    os.rename(old_filepath, new_filepath)
                    print(f"Renamed file: {filename} -> {new_filename}")
                except OSError as e:
                    print(f"Error renaming file {old_filepath}: {e}")

        # 2. Rename directories
        # We iterate through the 'dirs' list provided by os.walk, but the actual renaming
        # happens using the path constructed from 'root' and the original dir name.
        for i, dirname in enumerate(dirs):
            if ' ' in dirname:
                old_dirpath = os.path.join(root, dirname)
                new_dirname = dirname.replace(' ', '_')
                new_dirpath = os.path.join(root, new_dirname)
                try:
                    os.rename(old_dirpath, new_dirpath)
                    print(f"Renamed directory: {dirname} -> {new_dirname}")
                    # Update the dirs list in place so os.walk continues correctly with the new name
                    dirs[i] = new_dirname 
                except OSError as e:
                    print(f"Error renaming directory {old_dirpath}: {e}")

    print("Rename process complete.")

if __name__ == "__main__":
    # The script can be run with a directory path as an argument, 
    # or it will default to the current working directory.
    if len(sys.argv) > 1:
        start_directory = sys.argv[1]
    else:
        start_directory = "/home/webui/Desktop/Close_out" # Current directory
        print(f"No directory specified. Defaulting to current directory: {os.getcwd()}")

    # Ensure the path is an absolute path for safety
    abs_start_directory = os.path.realpath(start_directory)
    
    if os.path.isdir(abs_start_directory):
        replace_spaces_with_underscores(abs_start_directory)
    else:
        print(f"Error: Directory not found at {abs_start_directory}")

