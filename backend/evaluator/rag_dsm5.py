import time
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
    FactualCorrectness,
    Faithfulness,
    LLMContextRecall,
)
from chains.healthcare_chain import HealthcareRetriever
from utils import AppConfig, ModelFactory

DSM5_DATASET_EVAL_PATH = AppConfig.DSM5_DATASET_EVAL_PATH
DSM5_RESULT_EVAL_PATH = AppConfig.DSM5_RESULT_EVAL_PATH

retriever = HealthcareRetriever()
model = ModelFactory.get_llm_model("groq")


def rag_with_elasticsearch(question: str):
    """Process single question with RAG - used for batch processing"""
    # Get relevant contexts from retriever
    retrieved_docs = retriever.invoke(query=question)

    # Format contexts as list of strings for Ragas
    contexts = [
        "\n".join([doc["title"], doc["context_headers"], doc["content"]])
        for doc in retrieved_docs
    ]

    prompt = f"""You are a medical expert assistant specializing in mental health disorders based on DSM-5.

    Use the following context to answer the question accurately and professionally.

    {contexts}

    Question: {question}

    Instructions:
    - Answer based ONLY on the provided context
    - Be accurate and cite relevant diagnostic criteria when applicable
    - If the context doesn't contain enough information, state that clearly
    - Provide a clear, professional response
    - Only using Vietnamese language to generate

    Answer:"""

    # Invoke model
    response = model.invoke(prompt)
    time.sleep(1)  # To avoid rate limits
    answer = response.content.strip()

    return answer, contexts


def batch_rag_evaluation(
    questions: List[str], batch_size: int = 5
) -> List[Tuple[str, List[str]]]:
    """
    Process multiple questions in batches with concurrent execution.

    Args:
        questions: List of questions to evaluate
        batch_size: Number of concurrent workers

    Returns:
        List of (answer, contexts) tuples
    """
    results = []

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all tasks
        future_to_question = {
            executor.submit(rag_with_elasticsearch, q): q for q in questions
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
                results.append(("", []))

    return results


def evaluate_rag(testset_df: pd.DataFrame, batch_size: int = 5):
    """
    Evaluate RAG with batching for better performance.

    Args:
        testset_df: DataFrame with 'user_input' and optional 'reference' columns
        batch_size: Number of concurrent workers (default: 5)
    """
    logger.info(f"Starting RAG evaluation with batch_size={batch_size}...")

    # Extract questions
    questions = testset_df["user_input"].tolist()

    # Process in batches using concurrent execution
    results = batch_rag_evaluation(questions, batch_size=batch_size)

    # Prepare evaluation data
    eval_data = {
        "user_input": [],
        "response": [],
        "retrieved_contexts": [],
        "reference": [],
    }

    for idx, (answer, contexts) in enumerate(results):
        eval_data["user_input"].append(questions[idx])
        eval_data["response"].append(answer)
        eval_data["retrieved_contexts"].append(contexts)
        eval_data["reference"].append(testset_df.iloc[idx].get("reference", ""))
        eval_data["truth_contexts"].append(
            testset_df.iloc[idx].get("truth_contexts", [])
        )

    # Evaluate with Ragas metrics
    logger.info("Starting Ragas metrics evaluation...")
    eval_dataset = Dataset.from_dict(eval_data)
    result = evaluate(
        dataset=eval_dataset,
        metrics=[
            LLMContextRecall(),
            Faithfulness(),
            FactualCorrectness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
        ],
    )
    return result


if __name__ == "__main__":
    testset_df = pd.read_csv(DSM5_DATASET_EVAL_PATH)

    # Run evaluation with batching
    results = evaluate_rag(testset_df=testset_df, batch_size=5)

    df_result = results.to_pandas()
    df_result.to_csv(DSM5_RESULT_EVAL_PATH, index=False)
    logger.info(f"Results saved to {DSM5_RESULT_EVAL_PATH}")

# python -m evaluator.rag_dsm5
