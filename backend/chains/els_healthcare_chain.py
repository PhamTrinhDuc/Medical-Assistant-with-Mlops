import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
from google import generativeai as genai
from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Literal, Optional
import asyncio
from utils import AppConfig, logger


class HealthcareRetriever:
    """
    Hybrid Search Retriever với Elasticsearch.
    Tương thích với structure từ unstructured library:
    - element_id: Unique ID
    - text: Nội dung văn bản
    - metadata: {filename, page_number, file_directory, filetype, languages, last_modified}
    
    Chiến lược search:
    ─────────────────────────────────────────────────────────────────
    1. KEYWORD SEARCH (BM25):
       - Multi-match trên text (boost cao), filename, file_directory
       - Dùng Vietnamese analyzer (đã bỏ dấu, lowercase)
       - Phrase matching cho exact matches
       
    2. SEMANTIC SEARCH (kNN):
       - Dense vector search với cosine similarity
       - Tốt cho câu hỏi dài, paraphrase, đồng nghĩa
       
    3. HYBRID + RRF:
       - Reciprocal Rank Fusion kết hợp 2 phương pháp
       - Ưu tiên documents xuất hiện trong cả 2 results
    ─────────────────────────────────────────────────────────────────
    """
    
    def __init__(
        self,
        model_name: Literal["openai", "google"] = "openai",
    ):
        self.index_name = AppConfig.INDEX_NAME_ELS
        self.model_name = model_name
        self.vector_size = AppConfig.VECTOR_SIZE

        # Elasticsearch client
        self.els_client = Elasticsearch([f"http://{AppConfig.ELS_HOST}:{AppConfig.ELS_PORT}"])

        # Embedding client
        if model_name == "google": 
            self.embed_model = AppConfig.GOOGLE_EMBEDDING
            genai.configure(api_key=AppConfig.GOOGLE_API_KEY)
        else:
            self.embed_model = AppConfig.OPENAI_EMBEDDING
            self.openai_client = OpenAI(api_key=AppConfig.OPENAI_API_KEY)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for query"""
        if self.model_name == "openai":
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embed_model,
                dimensions=self.vector_size
            )
            return response.data[0].embedding
        else: 
            response = genai.embed_content(
                content=text,
                model=self.embed_model, 
                output_dimensionality=self.vector_size)
            return response['embedding']

    def _build_keyword_query(
        self, 
        query: str, 
        size: int = 20,
        boost_text: float = 2.0,
        boost_filename: float = 3.0,
        boost_directory: float = 1.5
    ) -> Dict:
        """
        Build BM25 keyword query với multi-match strategy.
        
        Strategy:
        - text^2: Full-text search với Vietnamese analyzer
        - filename^3: Boost cao cho filename matches
        - file_directory^1.5: Boost cho directory matches
        """
        return {
            "query": {
                "bool": {
                    "should": [
                        # Multi-match trên text content
                        {
                          "multi_match": {
                              "query": query,
                              "fields": [
                                  f"text^{boost_text}",
                                  f"filename^{boost_filename}",
                                  f"file_directory^{boost_directory}"
                              ],
                              "type": "best_fields",
                              "operator": "or",
                              "minimum_should_match": "30%"
                          }
                        },
                        # Phrase match cho exact phrases
                        {
                          "multi_match": {
                              "query": query,
                              "fields": ["text^2"],
                              "type": "phrase",
                              "slop": 2  # Cho phép 2 từ xen giữa
                          }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": size,
            "_source": ["element_id", "text", "filename", "page_number", 
                       "file_directory", "filetype", "languages", "last_modified"]
        }

    def _build_vector_query(
        self, 
        query_vector: List[float], 
        size: int = 20,
        num_candidates: int = 100
    ) -> Dict:
        """
        Build kNN vector search query.
        
        Strategy:
        - k: Số results trả về
        - num_candidates: Số candidates xem xét (cao hơn = chính xác hơn nhưng chậm hơn)
        """
        return {
          "knn": {
              "field": "embedding",
              "query_vector": query_vector,
              "k": size,
              "num_candidates": num_candidates
          },
          "_source": ["element_id", "text", "filename", "page_number",
                      "file_directory", "filetype", "languages", "last_modified"]
        }

    def _reciprocal_rank_fusion(
        self,
        keyword_hits: List[Dict],
        vector_hits: List[Dict],
        k: int = 60,
        keyword_weight: float = 1.0,
        vector_weight: float = 1.0
    ) -> Dict[str, Dict]:
        """
        RRF với weighted scores.
        
        Công thức: score = w1/(k + rank_keyword) + w2/(k + rank_vector)
        
        Args:
            k: RRF constant (60 là standard, cao hơn = ít phân biệt rank)
            keyword_weight: Weight cho BM25 results
            vector_weight: Weight cho semantic results
        """
        doc_scores = {}
        doc_data = {}
        
        # Process keyword results
        for rank, hit in enumerate(keyword_hits, start=1):
            doc_id = hit["_id"]
            score = keyword_weight / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score
            doc_data[doc_id] = hit["_source"]
            doc_data[doc_id]["_keyword_rank"] = rank
            doc_data[doc_id]["_keyword_score"] = hit.get("_score", 0)
        
        # Process vector results
        for rank, hit in enumerate(vector_hits, start=1):
            doc_id = hit["_id"]
            score = vector_weight / (k + rank)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score
            if doc_id not in doc_data:
                doc_data[doc_id] = hit["_source"]
            doc_data[doc_id]["_vector_rank"] = rank
            doc_data[doc_id]["_vector_score"] = hit.get("_score", 0)
        
        # Add RRF score to doc_data
        for doc_id, score in doc_scores.items():
            doc_data[doc_id]["_rrf_score"] = score
            # Bonus nếu xuất hiện trong cả 2 results
            if "_keyword_rank" in doc_data[doc_id] and "_vector_rank" in doc_data[doc_id]:
                doc_data[doc_id]["_rrf_score"] *= 1.2  # 20% boost
        
        return doc_data

    def search_by_filename(
        self,
        filename: str,
        page_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm theo tên file và page number cụ thể.
        Ví dụ: search_by_filename("document.pdf", 5)
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"filename": filename}}
                    ]
                }
            },
            "size": 20,
            "_source": ["element_id", "text", "filename", "page_number",
                       "file_directory", "filetype", "languages", "last_modified"]
        }
        
        # Add page_number filter if provided
        if page_number is not None:
            query["query"]["bool"]["must"].append(
                {"term": {"page_number": page_number}}
            )
        
        try:
            response = self.els_client.search(index=self.index_name, body=query)
            return [
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    **hit["_source"]
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.warning(f"Error searching by filename: {str(e)}")
            return []

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        rrf_k: int = 60,
        keyword_weight: float = 1.0,
        vector_weight: float = 1.2,  # Slight boost cho semantic
        num_candidates: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search với RRF fusion.
        
        Args:
            query: Search query
            top_k: Số results trả về
            rrf_k: RRF constant
            keyword_weight: Weight cho BM25
            vector_weight: Weight cho semantic search
            num_candidates: Số candidates cho kNN
            
        Returns:
            List of ranked results với scores và metadata
        """
        # Generate query embedding
        query_vector = self._get_embedding(text=query)
        
        # Lấy nhiều hơn top_k để RRF có đủ candidates
        fetch_size = min(top_k * 3, 50)
        
        # Execute both searches
        keyword_query = self._build_keyword_query(query, size=fetch_size)
        vector_query = self._build_vector_query(query_vector, size=fetch_size, num_candidates=num_candidates)
        
        try:
            keyword_response = self.els_client.search(index=self.index_name, body=keyword_query)
            vector_response = self.els_client.search(index=self.index_name, body=vector_query)
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {str(e)}")
            raise
        
        keyword_hits = keyword_response["hits"]["hits"]
        vector_hits = vector_response["hits"]["hits"]
        
        # Log search stats
        logger.info(f"Keyword hits: {len(keyword_hits)}, Vector hits: {len(vector_hits)}")
        
        # Apply RRF fusion
        doc_data = self._reciprocal_rank_fusion(
            keyword_hits=keyword_hits,
            vector_hits=vector_hits,
            k=rrf_k,
            keyword_weight=keyword_weight,
            vector_weight=vector_weight
        )
        
        # Sort by RRF score
        sorted_docs = sorted(
            doc_data.items(), 
            key=lambda x: x[1].get("_rrf_score", 0), 
            reverse=True
        )[:top_k]
        
        # Format results
        results = []
        
        for doc_id, data in sorted_docs:
            result = {
                "id": doc_id,
                "element_id": data.get("element_id", doc_id),
                "text": data.get("text", ""),
                "filename": data.get("filename", ""),
                "page_number": data.get("page_number"),
                "file_directory": data.get("file_directory", ""),
                "filetype": data.get("filetype", ""),
                "languages": data.get("languages", []),
                "last_modified": data.get("last_modified"),
                "scores": {
                    "rrf": round(data.get("_rrf_score", 0), 4),
                    "keyword_rank": data.get("_keyword_rank"),
                    "vector_rank": data.get("_vector_rank"),
                }
            }
            results.append(result)
        
        return results

    def search_by_page_range(
        self,
        filename: str,
        page_start: int,
        page_end: int
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm theo file và khoảng trang cụ thể.
        Ví dụ: search_by_page_range("document.pdf", 1, 10)
        """
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"filename": filename}},
                        {"range": {"page_number": {"gte": page_start, "lte": page_end}}}
                    ]
                }
            },
            "size": 100,
            "sort": [{"page_number": {"order": "asc"}}],
            "_source": ["element_id", "text", "filename", "page_number",
                       "file_directory", "filetype", "languages", "last_modified"]
        }
        
        try:
            response = self.els_client.search(index=self.index_name, body=query)
            return [
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    **hit["_source"]
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.warning(f"Error searching by page range: {str(e)}")
            return []

    def invoke(
        self, 
        query: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
      """
      LangChain-compatible synchronous invoke.
      """
      config = config or {}
      return self.hybrid_search(
        query=query,
        top_k=config.get("top_k", 10),
        rrf_k=config.get("rrf_k", 60),
        keyword_weight=config.get("keyword_weight", 1.0),
        vector_weight=config.get("vector_weight", 1.2)
      )
    
    async def ainvoke(
        self, 
        query: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        LangChain-compatible async invoke.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.invoke, query, config)

if __name__ == "__main__":
    retriever = HealthcareRetriever(model_name="openai")
    
    # Test hybrid search
    query = "Rối loạn ngôn ngữ ở trẻ em là gì?"
    print(f"\n🔍 Query: '{query}'\n") 
    
    results = retriever.invoke(query, config={"top_k": 5})
    
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results, 1):
      print(f"#{i} [{result['element_id']}]")
      print(f"   File: {result.get('filename', 'N/A')} (page {result.get('page_number', 'N/A')})")
      print(f"   Scores: {result['scores']}")
      print(f"   Content: {result['text'][:150]}...")
      print()
    
    # # Test format context for LLM
    # print("\n" + "="*80)
    # print("FORMATTED CONTEXT FOR LLM:")
    # print("="*80)
    # print(retriever.format_context_for_llm(results, max_chars=2000))   