
from utils.config import AppConfig

from chains.milvus_healthcare_chain import get_milvus_store

def main(): 
  store = get_milvus_store(collection_name=AppConfig.MILVUS_INDEX, drop_old=False, enable_hybrid=True)
  query = "Rối loạn ngôn ngữ là gì?"
  results = store.hybrid_search(query, k=5)
  
  for rs in results: 
    print(rs.page_content)

if __name__ == "__main__":
   main()