
from typing import List, Dict, Any, Optional, Union
from langchain_core.documents import Document
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_core.embeddings import Embeddings
from langchain_openai.embeddings import OpenAIEmbeddings
from pymilvus import Collection
from utils.config import AppConfig


class MilvusHybridStore:
    """
    Wrapper class cho langchain_milvus.Milvus với hybrid search (dense + BM25).
    
    Features:
    - Dense embeddings: dangvantuan/vietnamese-embedding (768-dim)
    - BM25 fulltext search: built-in Milvus BM25 function
    - Hybrid search: weighted reranking hoặc RRF
    - Metadata filtering: page_number, filename, filetype, etc.
    - Multimodal support: tables và images trong metadata
    
    Example:
        >>> store = MilvusHybridStore(
        ...     collection_name="multimodal_docs",
        ...     embeddings=WrapperEmbeddings(),
        ...     connection_args={"uri": "http://localhost:19530"}
        ... )
        >>> store.add_documents(documents)
        >>> results = store.hybrid_search("query here", k=10)
    """
    
    def __init__(
        self, 
        collection_name: str,
        embeddings: Embeddings,
        connection_args: Optional[Dict[str, Any]] = None,
        drop_old: bool = False,
        enable_hybrid: bool = True,
    ):
        """
        Khởi tạo Milvus Hybrid Store.
        
        Args:
            collection_name: Tên collection trong Milvus
            embeddings: WrapperEmbeddings instance cho dense vectors
            connection_args: Dict với 'uri' cho Milvus connection
            drop_old: Nếu True, xóa collection cũ và tạo lại
            enable_hybrid: Nếu True, enable BM25 fulltext search
        """
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.enable_hybrid = enable_hybrid
        
        # Connection args - convert to URI format
        if connection_args is None:
            connection_args = {
                "uri": f"http://{AppConfig.MILVUS_HOST}:{AppConfig.MILVUS_PORT}"
            }
        elif "host" in connection_args and "port" in connection_args:
            # Convert old format to new format
            connection_args = {
                "uri": f"http://{connection_args['host']}:{connection_args['port']}"
            }
        
        # Initialize Milvus vector store
        if enable_hybrid:
            # Hybrid search with BM25
            self.vectorstore = Milvus(
                embedding_function=embeddings,
                collection_name=collection_name,
                connection_args=connection_args,
                builtin_function=BM25BuiltInFunction(),
                consistency_level="Strong",
                drop_old=drop_old,
            )
        else:
            # Semantic search only
            self.vectorstore = Milvus(
                embedding_function=embeddings,
                collection_name=collection_name,
                connection_args=connection_args,
                consistency_level="Strong",
                drop_old=drop_old,
            )

    

    def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100,
    ) -> List[str]:
        """
        Thêm documents vào Milvus.
        
        Args:
            documents: List LangChain Documents
            batch_size: Kích thước batch (unused, kept for compatibility)
            
        Returns:
            List document IDs
        """
        if not documents:
            return []
        
        print(f"Adding {len(documents)} documents to Milvus...")
        ids = self.vectorstore.add_documents(documents)
        print(f"✓ Successfully added {len(ids)} documents")

        return ids
        
        
    def hybrid_search(
        self,
        query: str,
        k: int = 10,
        filter_expr: Optional[str] = None,
        ranker_type: str = "weighted",
        ranker_params: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Thực hiện hybrid search với dense + BM25.
        
        Args:
            query: Query text
            k: Số lượng kết quả trả về
            filter_expr: Milvus filter expression, VD: 'page_number > 5 and filename == "test.pdf"'
            ranker_type: "weighted" hoặc "rrf" (reciprocal rank fusion)
            ranker_params: Dict params cho ranker, VD: {"weights": [0.7, 0.3]} cho weighted
            
        Returns:
            List LangChain Documents với metadata
        """
        if not self.enable_hybrid:
            # Fallback to semantic search only
            return self.similarity_search(query, k=k, expr=filter_expr)
        
        # Default ranker params
        if ranker_params is None:
            ranker_params = {"weights": [0.7, 0.3]}  # 70% semantic, 30% BM25
        
        return self.vectorstore.similarity_search(
            query,
            k=k,
            expr=filter_expr,
            ranker_type=ranker_type,
            ranker_params=ranker_params,
        )
    

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Union[Dict[str, Any], str]] = None,
        expr: Optional[str] = None,
        **kwargs
    ) -> List[Document]:
        """
        Semantic search (backward compatible với ChromaDB pattern).
        
        Args:
            query: Query text
            k: Số lượng kết quả
            filter: Dict filter hoặc Milvus expr string
            expr: Milvus expression (alternative to filter)
            
        Returns:
            List Documents
        """
        # Convert dict filter to Milvus expression
        filter_expr = expr
        if filter and isinstance(filter, dict):
            filter_expr = self._dict_to_expr(filter)
        elif filter and isinstance(filter, str):
            filter_expr = filter
        
        return self.vectorstore.similarity_search(
            query,
            k=k,
            expr=filter_expr,
            **kwargs
        )
        
    def _dict_to_expr(self, filter_dict: Dict[str, Any]) -> str:
        """
        Convert dict filter sang Milvus expression.
        
        Example:
            {"filename": "test.pdf", "page_number": 5}
            -> 'filename == "test.pdf" and page_number == 5'
        """
        conditions = []
        for key, value in filter_dict.items():
            if isinstance(value, str):
                conditions.append(f'{key} == "{value}"')
            elif isinstance(value, (int, float)):
                conditions.append(f'{key} == {value}')
            elif isinstance(value, dict):
                # Support operators like {"page_number": {"$gt": 5}}
                for op, val in value.items():
                    if op == "$gt":
                        conditions.append(f"{key} > {val}")
                    elif op == "$gte":
                        conditions.append(f"{key} >= {val}")
                    elif op == "$lt":
                        conditions.append(f"{key} < {val}")
                    elif op == "$lte":
                        conditions.append(f"{key} <= {val}")
                    elif op == "$ne":
                        if isinstance(val, str):
                            conditions.append(f'{key} != "{val}"')
                        else:
                            conditions.append(f"{key} != {val}")
        
        return " and ".join(conditions) if conditions else None
        
    def delete(self, ids: Optional[List[str]] = None, expr: Optional[str] = None):
        """
        Xóa documents từ collection.
        
        Args:
            ids: List document IDs để xóa (nếu có)
            expr: Milvus filter expression để xóa, VD: 'filename == "test.pdf"'
        """
        if ids:
            self.vectorstore.delete(ids)
            print(f"✓ Deleted {len(ids)} documents")
        elif expr:
            self.vectorstore.delete(expr=expr)
            print(f"✓ Deleted documents matching: {expr}")
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê về collection.
        
        Returns:
            Dict với collection info
        """

        return {
            "collection_name": self.collection_name,
            "enable_hybrid": self.enable_hybrid,
        }


def get_milvus_store(
    collection_name: Optional[str] = None,
    drop_old: bool = False,
    enable_hybrid: bool = True,
) -> MilvusHybridStore:
    """
    Factory function tạo MilvusHybridStore với AppConfig mặc định.
    
    Args:
        collection_name: Tên collection (default: AppConfig.MILVUS_INDEX)
        drop_old: Nếu True, xóa collection cũ
        enable_hybrid: Nếu True, enable BM25 fulltext search
        
    Returns:
        MilvusHybridStore instance
        
    Example:
        >>> store = get_milvus_store("multimodal_docs")
        >>> store.add_documents(docs)
        >>> results = store.hybrid_search("query")
    """
    if collection_name is None:
        collection_name = AppConfig.MILVUS_INDEX
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model=AppConfig.OPENAI_EMBEDDING,
        api_key=AppConfig.OPENAI_API_KEY,
        dimensions=AppConfig.VECTOR_SIZE,
    )
    
    # Create store
    store = MilvusHybridStore(
        collection_name=collection_name,
        embeddings=embeddings,
        connection_args={
            "uri": f"http://{AppConfig.MILVUS_HOST}:{AppConfig.MILVUS_PORT}"
        },
        drop_old=drop_old,
        enable_hybrid=enable_hybrid,
    )
    
    return store
