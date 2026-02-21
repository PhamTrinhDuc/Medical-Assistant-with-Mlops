from unstructured.partition.pdf import partition_pdf
from unstructured.chunking.title import chunk_by_title
from utils.config import AppConfig
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

def single_parition(file_path: str):
  elements = partition_pdf(
      filename=file_path,  # Path to your PDF file
      strategy="hi_res", # Use the most accurate (but slower) processing method of extraction
      hi_res_model_name="yolox", # Use YOLOX model for high-res strategy
      # infer_table_structure=True, # Keep tables as structured HTML, not jumbled text
      # extract_image_block_types=["Image"], # Grab images found in the PDF
      # extract_image_block_to_payload=True, # Store images as base64 data you can actually use
      languages=["vie"],
    )

  print(f"✅ Extracted {len(elements)} elements")
  return elements

def single_chunks_by_title(elements):
  
    """Create intelligent chunks using title-based strategy"""
    print("🔨 Creating smart chunks...")
    try:
      chunks = chunk_by_title(
        elements, # The parsed PDF elements from previous step
        max_characters=2048, # Hard limit - never exceed 3000 characters per chunk
        new_after_n_chars=2048, # Try to start a new chunk after 2400 characters
        combine_text_under_n_chars=500 # Merge tiny chunks under 500 chars with neighbors
      )

      print(f"✅ Created {len(chunks)} chunks")
      return chunks
    except Exception as e: 
      return f"Error chunking by tile: {str(e)}"

def convert_chunks_to_json(chunks, output_path: str):
    """Convert chunks to JSON format compatible with Elasticsearch indexing"""
    chunk_list = []
    
    for chunk in chunks:
        chunk_dict = {
            "element_id": chunk.id if hasattr(chunk, 'id') else chunk.id_to_hash(chunk.to_dict()),
            "text": chunk.text if hasattr(chunk, 'text') else str(chunk),
            "metadata": chunk.metadata.to_dict() if hasattr(chunk.metadata, 'to_dict') else dict(chunk.metadata)
        }
        chunk_list.append(chunk_dict)
    
    # Save to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunk_list, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Saved {len(chunk_list)} chunks to {output_path}")
    return chunk_list
         
if __name__ == "__main__":
  file_path = AppConfig.DSM5_PATH
  elements = single_parition(file_path)
  
  chunks = single_chunks_by_title(elements)
  
  # Convert and save to JSON
  output_path = AppConfig.DSM5_CHUNKS_PATH
  chunks_json = convert_chunks_to_json(chunks, output_path)
  
  # Print first chunk as example
  if chunks_json:
    print("\n📄 Example chunk:")
    print(json.dumps(chunks_json[0], ensure_ascii=False, indent=2))
