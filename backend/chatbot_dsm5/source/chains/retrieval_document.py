import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import pickle
from uuid import uuid4
from typing import Dict, Any
from dataclasses import dataclass
from langchain_community.vectorstores import Chroma, Milvus
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from chunker.custom_chunker import extract_dsm_chunk_hiearchical
from utils.config import AppConfig

@dataclass
class EnsembleQueryEngine:

    def __init__(self, 
                 collection_name: str="chatbot-dsm5", 
                 persist_path: str="./chromadb", 
                 persist_chunk: str="./chunks.pkl",
                 embedder: Embeddings=None,
                 rerank_model: str=None):
        """
        Args: 
            embedder: embedding model 
            df: dataframe 
            weights_ensemble: weights for each search type [similarity, bm25, mmr]
            db_persist_path: db storage directory

        """

        self.client = Chroma(
            collection_name=collection_name,
            embedding_function=embedder or OpenAIEmbeddings(model="text-embedding-3-large"), 
            persist_directory=persist_path
        )
        self.embedder = embedder
        self.persist_path = persist_path
        self.persist_chunk=persist_chunk
        if rerank_model: 
           self.rerank_model = rerank_model
           self.is_reranking = True
        else: 
           self.is_reranking = False

        os.makedirs(persist_path, exist_ok=True)
        self.documents = self.upsert()

    def upsert(self):
      if os.path.exists(self.persist_chunk): 
          with open(self.persist_chunk, "rb") as f:
            documents = pickle.load(f)
            return documents
      
      documents = extract_dsm_chunk_hiearchical(pdf_path=AppConfig.pdf_path)

      with open(self.persist_chunk, "wb") as f:
        pickle.dump(documents, f)
        
      ids = [str(uuid4()) for _ in range(len(documents))]

      if len(os.listdir(self.persist_path)) == 0:
        self.client.from_documents(
            documents=documents, 
            embedding=self.embedder, 
            ids=ids, 
            persist_directory=self.persist_path
        )
        print("Create embedding ...")
      else: 
         print("Vector embedding exists. Skip embedding chunks")

      return documents
    
    def _create_bm25_retriever(self, top_k: int) -> BM25Retriever:
        """Create BM25 retriever"""
        retriever = BM25Retriever.from_documents(self.documents)
        retriever.k = top_k
        return retriever
    
    def _create_mmr_retriever(self, 
                              top_k: int, 
                              lambda_mult: float, 
                              fetch_k: int,  
                              filter_search: Dict[str, Any]=None) -> Chroma: 
        """
        top_k: Amount of documents to return (Default: 3)
        fetch_k: Amount of documents to pass to MMR algorithm (Default: 15)
        lambda_mult: Diversity of results returned by MMR; 
            1 for minimum diversity and 0 for maximum. (Default: 0.25)
        filter: Filter by document metadata

        >>> examples:  
            default: search_kwargs = {'k': 3, 'lambda_mult': 0.25, 'fetch_k': 15}
            custom: search_kwargs = {'k': 3, 'lambda_mult': 0.25, 'filter': {"product_name": "Dieu_hoa"}}
        """
        
        filter_default = {'k': top_k, 
                          'lambda_mult': lambda_mult, 
                          'fetch_k': fetch_k}
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="mmr",
            search_kwargs=filter_default
        )
    
    def _create_vanilla_retriever(self, top_k:int, 
                                  score_threshold: float, 
                                  filter_search: Dict[str, Any]=None) -> Chroma:
        """
        Create vanilla vector similarity retriever
        top_k: Amount of documents to return (Default: 3)
        score_threshold: Minimum relevance threshold for similarity_score_threshold
        filter search: Filter by document metadata

        >>> examples:  
            default: search_kwargs = {'k': 3, 'score_threshold': 0.6}
            custom: search_kwargs = {'k': 3, 'score_threshold': 0.25, 'filter': {"product_name": "Dieu_hoa"}}
        """
        filter_default = {'k': top_k, 
                          'score_threshold': score_threshold}
        
        if filter_search is not None:
            filter_default['filter'] = filter_search

        return self.client.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=filter_default
        )
    
    def _build_ensemble_retriever(self, filter_search: Dict[str, Any]=None, **kwargs):
        """
        FOR MMR ALGORITHM: 
            fetch_k: Amount of documents to pass to MMR algorithm (Default: 15)
            lambda_mult: Diversity of results returned by MMR; 
                1 for minimum diversity and 0 for maximum. (Default: 0.25)
        FOR SIMILAR ALGORITHM: 
            score_threshold: Minimum relevance threshold for similarity_score_threshold
        
        weights_ensemble: weights for each search type [similarity, bm25, mmr]
        top_k: Amount of documents to return (Default: 3)
        filter_search: Filter by document metadata
        """
        top_k = kwargs.get('top_k', 5)
        weights = kwargs.get("weights", [0.5, 0.5])
        score_threshold = kwargs.get("score_threshold", 0.7)
        fetch_k = kwargs.get('fetch_k', 20)
        lambda_mult = kwargs.get('lambda_mult', 0.25)

        bm25_retriever = self._create_bm25_retriever(top_k=top_k)

        # vanilla_retriever = self._create_vanilla_retriever(top_k=top_k,
        #                                                    score_threshold=score_threshold,
        #                                                    filter_search=filter_search)
        mmr_retriever = self._create_mmr_retriever(top_k=top_k, 
                                                   fetch_k=fetch_k, 
                                                   lambda_mult=lambda_mult, 
                                                   filter_search=filter_search)

        ensemble_retriever=  EnsembleRetriever(
            retrievers=[ bm25_retriever, mmr_retriever],
            weights=weights
        )

        if self.is_reranking: 
           model = HuggingFaceCrossEncoder(model_name=self.rerank_model)
           compressor = CrossEncoderReranker(model=model, top_n=top_k)

           compression_retriever = ContextualCompressionRetriever(
              base_compressor=compressor, 
              base_retriever=ensemble_retriever
           )
           return compression_retriever
        else:
          return ensemble_retriever
    
    def search(self, query: str, **kwargs):
        """
        Get relevant context for a query about a specific product
        
        Args:
            query: User query after rewriting
            product_name: Name of the product to search in
            
        Returns:
            Relevant context for the query
        """

        retriever = self._build_ensemble_retriever(**kwargs)

        contents = retriever.invoke(input=query)
        return contents

    def _drop_db(self, path_db: str):
        os.remove(path=path_db)


if __name__ == "__main__": 
  from dotenv import load_dotenv
  load_dotenv('.env.dev')

  query_engine = EnsembleQueryEngine()
  contents = query_engine.search(query="Tôi gặp khó khăn trong viê giao tiếp với mọi người")
  for content in contents: 
    print(content.page_content)
    print("=" * 50)