from docling.datamodel.pipeline_options import smolvlm_picture_description

pipeline_options.picture_description_options = smolvlm_picture_description
import pathlib

def get_all_files_pathlib(directory_path):
    p = pathlib.Path(directory_path)
    # Use rglob("*") to recursively find all files and directories.
    # We can filter for only files using the .is_file() method.
    files_list = [file for file in p.rglob('*') if file.is_file()]
    # To get string paths:
    # files_str_list = [str(file) for file in files_list]
    return files_list

# Example usage:
directory_to_search = '/media/projects' # Search from the current directory
all_files = get_all_files_pathlib(directory_to_search)
for file_path in all_files:
    print(file_path)
