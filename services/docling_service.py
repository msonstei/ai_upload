import os
import requests
import glob
import logging
from pathlib import Path
import json
import time

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions,RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import smolvlm_picture_description
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions

# Configure accelerator options for GPU
accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.CUDA,  # or AcceleratorDevice.AUTO
)

pipeline_options = PdfPipelineOptions()
pipeline_options.ocr_options = RapidOcrOptions(
    backend="torch",
)


artifacts_path = "/root/.cache/docling/models"


pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path,enable_remote_services=True, do_formula_enrichment = True)
pipeline_options.enable_remote_services=True
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.do_picture_description = True
pipeline_options = PdfPipelineOptions(enable_remote_services=True)
pipeline_options.do_formula_enrichment = True
pipeline_options.picture_description_options = smolvlm_picture_description

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)


# Instantiate the converter (models will download the first time you run this)
converter = DocumentConverter()

# Replace with your own Docling API endpoint and key
DOCLING_ENDPOINT = 'http://du-webui:5001/'
DOCLING_API_KEY = ''


def configure_logging(verbose: bool) -> None:
    """Set up a simple console logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%H:%M:%S",
    )

def get_output_path(file_path, output_dir):
        #output_path = os.path.dirname(file_path)
        markdown_output = Path(file_path).stem    
        markdown_output = f"{markdown_output}.md"
        output_path = output_dir
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            print(f"Directory '{output_path}' was created.")
        else:
            pass

        return f'{output_path}/{markdown_output}', markdown_output

def get_docling_data(file_path, output_dir):

    # Convert the document
    try:
        # 1. Open file and convert
        result = converter.convert(file_path)
        logging.info(f"Document processed successfully from: {file_path}")
        # 2. Change input location for output and .md filename
        full_path, markdown_output = get_output_path(file_path, output_dir)
        # 3. Get the original file name
        file_name = Path(file_path).name
        # 4. Move markdown to variable
        markdown_content = result.document.export_to_markdown()
        # 5. Save the output to a local file
        try:
            logging.info(f"Saving file to {markdown_output}")
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
                logging.info(f"Uploading {full_path}")
            logging.info(f"Conversion successful")
            return full_path, markdown_content, file_name
        except Exception as e:
            print (f"Error saving file: {e}")

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
    # If the process fails, return 'fail' as a result for processing
    return 'fail'
