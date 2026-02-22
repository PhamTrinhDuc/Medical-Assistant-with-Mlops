import time
import os
import pandas as pd
from typing import List, Tuple
from tqdm import tqdm
from loguru import logger
from datasets import Dataset
from concurrent.futures import ThreadPoolExecutor, as_completed
from ragas import evaluate
from ragas.metrics import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    # FactualCorrectness,
    Faithfulness,
    LLMContextRecall,
)
from chains.milvus_healthcare_chain import get_milvus_store
from chains.els_healthcare_chain import HealthcareRetriever
from utils import AppConfig, ModelFactory

DSM5_DATASET_EVAL_PATH = AppConfig.DSM5_DATASET_EVAL_PATH
DSM5_RESULT_EVAL_PATH = AppConfig.DSM5_RESULT_EVAL_PATH

els_retriever = HealthcareRetriever(model_name='openai')
milvus_retriever = get_milvus_store(collection_name=AppConfig.MILVUS_INDEX, drop_old=False, enable_hybrid=True)

# Thay đổi từ "groq" sang "google" hoặc "openai" để tránh lỗi version conflict
model = ModelFactory.get_llm_model("google")  # hoặc "openai"


def rag_with_elasticsearch(question: str, mode: str = "all"):
    """
    Process single question with RAG - used for batch processing
    
    Args:
        question: The question to process
        mode: "retriever" (only retrieve contexts) or "all" (retrieve + generate answer)
    
    Returns:
        answer, contexts tuple (answer is None if mode="retriever")
    """
    # Get relevant contexts from retriever
    try:
        retrieved_docs = els_retriever.invoke(query=question)
        contexts = ["\n".join([doc["text"]]) for doc in retrieved_docs]

        # If only evaluating retriever, skip generation
        if mode == "retriever":
            return None, contexts

        # Format contexts as list of strings for Ragas
        prompt = f"""You are a medical expert assistant specializing in mental health disorders based on DSM-5.
        Use the following context to answer the question accurately and professionally.
        {contexts}
        Question: {question}
        Instructions:
        - Answer based ONLY on the provided context
        - Be accurate and cite relevant diagnostic criteria when applicable
        - If the context doesn't relate to the question, respond with "I don't know"
        - Provide a clear, professional response
        - Only using Vietnamese language to generate

        Answer:"""

        # Invoke model
        response = model.invoke(prompt)
        time.sleep(1)  # To avoid rate limits
        answer = response.content.strip()

        return answer, contexts

    except Exception as e:
        logger.error(f"Error in rag_with_elasticsearch: {e}")
        raise ValueError(f"Error in rag_with_elasticsearch: {e}")


def rag_with_milvus(question: str, mode: str = "all", k: int = 10):
    """
    Process single question with RAG using Milvus hybrid search.

    Args:
        question: The question to process
        mode: "retriever" (only retrieve contexts) or "all" (retrieve + generate answer)
        k: Number of documents to retrieve

    Returns:
        answer, contexts tuple (answer is None if mode="retriever")
    """
    try:
        retrieved_docs = milvus_retriever.hybrid_search(question, k=k)
        contexts = [doc.page_content for doc in retrieved_docs]

        if mode == "retriever":
            return None, contexts

        prompt = f"""You are a medical expert assistant specializing in mental health disorders based on DSM-5.
        Use the following context to answer the question accurately and professionally.
        {contexts}
        Question: {question}
        Instructions:
        - Answer based ONLY on the provided context
        - Be accurate and cite relevant diagnostic criteria when applicable
        - If the context doesn't relate to the question, respond with "I don't know"
        - Provide a clear, professional response
        - Only using Vietnamese language to generate

        Answer:"""

        response = model.invoke(prompt)
        time.sleep(1)  # To avoid rate limits
        answer = response.content.strip()

        return answer, contexts

    except Exception as e:
        logger.error(f"Error in rag_with_milvus: {e}")
        raise ValueError(f"Error in rag_with_milvus: {e}")


def batch_rag_evaluation(
    questions: List[str], batch_size: int = 5, mode: str = "all", source: str = "els"
) -> List[Tuple[str, List[str]]]:
    """
    Process multiple questions in batches with concurrent execution.

    Args:
        questions: List of questions to evaluate
        batch_size: Number of concurrent workers
        mode: "retriever" (only retrieve) or "all" (retrieve + generate)
        source: "els" (Elasticsearch) or "milvus" (Milvus hybrid search)

    Returns:
        List of (answer, contexts) tuples (answer is None if mode="retriever")
    """
    rag_fn = rag_with_milvus if source == "milvus" else rag_with_elasticsearch
    results = []

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all tasks
        future_to_question = {
            executor.submit(rag_fn, q, mode): q for q in questions
        }

        # Process completed tasks with progress bar
        for future in tqdm(
            as_completed(future_to_question),
            total=len(questions),
            desc="Processing questions",
        ):
            try:
                answer, contexts = future.result()
                results.append((answer, contexts))
            except Exception as e:
                logger.error(f"Error processing question: {e}")
                raise ValueError(f"Error processing question: {e}")

    return results


def evaluate_rag(testset_df: pd.DataFrame, batch_size: int = 5, mode: str = "all", source: str = "els"):
    """
    Evaluate RAG with batching for better performance.

    Args:
        testset_df: DataFrame with 'user_input' and optional 'reference' columns
        batch_size: Number of concurrent workers (default: 5)
        mode: "retriever" (only evaluate retrieval) or "all" (evaluate full pipeline)
        source: "els" (Elasticsearch) or "milvus" (Milvus hybrid search)
    """
    logger.info(f"Starting RAG evaluation with mode='{mode}', source='{source}', batch_size={batch_size}...")

    # Extract questions
    questions = testset_df["user_input"].tolist()  # limit for groq free tier

    # Process in batches using concurrent execution
    results = batch_rag_evaluation(questions, batch_size=batch_size, mode=mode, source=source)

    # Prepare evaluation data
    eval_data = {
        "question": [],
        "retrieved_contexts": [],
        "reference": [],
    }
    
    # Only add answer field if mode is "all"
    if mode == "all":
        eval_data["answer"] = []

    for idx, (gen_answer, contexts) in enumerate(results):
        eval_data["question"].append(questions[idx])
        eval_data["retrieved_contexts"].append(contexts)
        eval_data["reference"].append(testset_df.iloc[idx].get("reference", ""))
        if mode == "all":
            eval_data["answer"].append(gen_answer)

    # Select metrics based on mode
    if mode == "retriever":
        # Only context-based metrics for retriever evaluation
        metrics = [
            LLMContextRecall(),
            ContextPrecision(),
            ContextRecall(),
        ]
        logger.info("Evaluating retriever only (context metrics)...")
    else:  # mode == "all"
        # All metrics including generation quality
        metrics = [
            LLMContextRecall(),
            Faithfulness(),
            # FactualCorrectness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
        ]
        logger.info("Evaluating full RAG pipeline (all metrics)...")

    # Evaluate with Ragas metrics
    logger.info("Starting Ragas metrics evaluation...")
    eval_dataset = Dataset.from_dict(eval_data)
    result = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
    )
    return result


if __name__ == "__main__":
    # Choose evaluation mode: "retriever" or "all"
    EVAL_MODE = "retriever"  # Change to "retriever" to only evaluate retrieval
    # Choose retriever source: "els" (Elasticsearch) or "milvus" (Milvus hybrid search)
    EVAL_SOURCE = "milvus"  # Change to "els" to use Elasticsearch
    
    testset_df = pd.read_csv(DSM5_DATASET_EVAL_PATH)

    # Run evaluation with batching and selected mode
    results = evaluate_rag(testset_df=testset_df, batch_size=5, mode=EVAL_MODE, source=EVAL_SOURCE)
    # results.to_pandas().to_csv(DSM5_RESULT_EVAL_PATH, index=False)

    # Adjust result path based on mode and source
    result_path = DSM5_RESULT_EVAL_PATH
    suffix = f"_{EVAL_SOURCE}"
    if EVAL_MODE == "retriever":
        result_path = DSM5_RESULT_EVAL_PATH.replace(".csv", f"_retriever{suffix}.csv")
    else:
        result_path = DSM5_RESULT_EVAL_PATH.replace(".csv", f"{suffix}.csv")
    
    if os.path.exists(result_path):
        df_result = pd.read_csv(result_path)
        logger.info("Appending new results to existing results...")
        df_result = pd.concat([df_result, results.to_pandas()], ignore_index=True)
    else:
        df_result = results.to_pandas()
        logger.info("Creating new results DataFrame...")

    df_result.to_csv(result_path, index=False)
    logger.info(f"RAG evaluation results saved to {result_path} (source={EVAL_SOURCE}, mode={EVAL_MODE})")


# python -m evaluator.rag_dsm5
