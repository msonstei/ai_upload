from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
import pathlib
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.document_converter import DocumentConverter

# Configure accelerator options for GPU
accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.CUDA,  # or AcceleratorDevice.AUTO
)

# Configure for ORC
pipeline_options = PdfPipelineOptions()
pipeline_options.ocr_options = RapidOcrOptions(
    backend="torch",
)

# Use Ollama
vlm_options = VlmPipelineOptions(
    enable_remote_services=True,
    vlm_options={
        "url": "http://du-webui:11434/v1/chat/completions",  # or any other compatible endpoint
        "params": {
            "model": "qwen3-embedding",
            "max_tokens": 4096,
        },
        "concurrency": 64,  # default is 1
        "prompt": "Convert this page to docling.",
        "timeout": 90,
    }
)

def process_files(file):
    source = file #"https://arxiv.org/pdf/2408.09869"  # file path or URL
    converter = DocumentConverter()
    doc = converter.convert(source).document

    print(doc.export_to_markdown())  # output: "### Docling Technical Report[...]"
    return




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
   if str(file_path)[-3:] == 'pdf':
      process_files(file_path)
   else:
      pass
