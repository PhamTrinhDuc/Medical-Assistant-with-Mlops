
import pickle
from typing import List, Dict, Any
from langchain_core.documents import Document
from utils.config import AppConfig
from chains.milvus_healthcare_chain import get_milvus_store

def format_to_documents(chunks) -> List[Document]:
    """
    Chuyển đổi dữ liệu thô thành danh sách Document của LangChain.
    
    Args:
        data: List of dictionaries, mỗi dictionary đại diện cho một document thô.
        
    Returns:
        List of LangChain Documents
    """
    documents = []
    for chunk in chunks:
      chunk = chunk.to_dict() if hasattr(chunk, "to_dict") else chunk  # Convert nếu là object có method to_dict
      metadata = chunk.get("metadata", {})
      doc = Document(
        page_content=chunk.get('text', ''),
        metadata={
          "element_id": chunk.get('element_id'),
          "file_directory": metadata.get('file_directory'),
          "filename": metadata.get('filename'),
          "filetype": metadata.get('filetype'),
          "page_number": metadata.get('page_number'),
        }
      )
      documents.append(doc)
    return documents

def indexing(): 
  with open(AppConfig.DSM5_CHUNKS_PATH, 'rb') as f:
    chunks = pickle.load(f)

  documents = format_to_documents(chunks)
  print(f"✓ Formatted {len(documents)} documents for Milvus indexing")

  vectorstore = get_milvus_store(
    collection_name=AppConfig.MILVUS_INDEX, 
    drop_old=True, 
    enable_hybrid=True
  )

  vectorstore.add_documents(documents)
  print(f"✓ Indexed {len(documents)} documents into Milvus collection '{AppConfig.MILVUS_INDEX}'")

  stats = vectorstore.get_stats()
  print(f"✓ Milvus Collection Stats: {stats}")

if __name__ == "__main__":
  indexing()

