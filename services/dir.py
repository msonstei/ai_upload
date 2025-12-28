import os

def list_directories_os(path='input/transfer/'):
    """
    Returns a list of immediate directory names under the given path.
    By default, it checks the current directory ('.').
    """
    directories = []
    for entry in os.listdir(path):
        # Construct the full path to check if it is a directory
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            directories.append(entry)
    return directories[0]

# Example usage:
#if __name__== 'main':
    #directory_list = list_directories_os('/media/projects/projects/Completed_Projects')
#    directory_list = list_directories_os('input/transfer/') 
#    print(f"Directories in the current location: {directory_list}")
#    directory = directory_list[0]
#    print(directory)
