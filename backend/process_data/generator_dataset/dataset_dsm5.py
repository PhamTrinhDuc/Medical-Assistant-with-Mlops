import json
import ast
import random
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from loguru import logger
from groq import Groq
from langchain_core.documents import Document
from pydantic import BaseModel, Field
from tqdm import tqdm
from prompt.evaluate import DSM5_SYSTEM_GENERATION_TEMPLATE
from utils import AppConfig

DSM5_CHUNKS_PATH = AppConfig.DSM5_CHUNKS_PATH
DSM5_DATASET_EVAL_PATH = AppConfig.DSM5_DATASET_EVAL_PATH
groq = Groq(api_key=AppConfig.GROQ_API_KEY)


# for model have method response_format of Groq
class Dsm5Generation(BaseModel):
    question: str = Field(..., description="Question for user")
    ground_truth: str = Field(
        ..., description="the correct answer to the question based on the context"
    )


class Dsm5Dataset(BaseModel):
    dataset: List[Dsm5Generation]


JSON_SCHEMA = {  # for model don't method response_format of Groq
    "dataset": [
        {"question": "string", "ground_truth": "string"},
        {"question": "string next", "ground_truth": "string next"},
    ]
}


def transform_chunks(chunks: list[dict]) -> list[Document]:
    documents = []

    for chunk in chunks:
        doc = Document(
            page_content=chunk["title"] + chunk["content"],
            metadata={
                "chunk_idx": chunk["chunk_idx"],
                "section_id": chunk["section_id"],
                "title": chunk["title"],
                "parent_section_id": chunk["parent_section_id"],
                "parent_section_title": chunk["parent_section_title"],
                "context_headers": chunk["context_headers"],
            },
        )
        documents.append(doc)
    return documents


def generate_qa_for_chunk(chunk: Document, num_pairs: int = 2) -> List[Dict]:
    """
    Generate QA pairs for a single chunk.
    Used for concurrent/batch processing.
    """
    results = []

    try:
        system_prompt = DSM5_SYSTEM_GENERATION_TEMPLATE.format(
            num_pairs=num_pairs,
            passage=chunk,
            format_schema=JSON_SCHEMA,
        )
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        response = groq.chat.completions.create(
            model=AppConfig.GROQ_LLM,
            messages=messages,
            temperature=0.3,
        )

        raw_response = response.choices[0].message.content or "{}"

        # Use robust JSON parsing
        response_json = ast.literal_eval(raw_response)

        for qa_data in response_json.get("dataset", []):
            if "question" in qa_data and "ground_truth" in qa_data:
                results.append(
                    {
                        "user_input": qa_data["question"],
                        "reference": qa_data["ground_truth"],
                        "truth_contexts": [chunk.page_content],
                    }
                )

        if results:
            logger.info(f"✅ Generated {len(results)} QA pairs from chunk")
        else:
            logger.warning(f"⚠️  No valid QA pairs parsed from response")

    except Exception as e:
        logger.error(f"❌ Error generating QA for chunk: {e}")

    return results


def generate_dataset(
    chunks: list[Document],
    num_samples: int = 100,
    num_pairs_generated: int = 2,
    batch_size: int = 3,
):
    """
    Generate dataset with batching for concurrent API calls.

    Args:
        chunks: List of Document chunks
        num_samples: Number of chunks to sample
        num_pairs_generated: QA pairs per chunk
        batch_size: Concurrent workers
    """
    logger.info(f"🔄 Starting dataset generation (batch_size={batch_size})...")
    dataset = []

    if len(chunks) > num_samples:
        selected_chunks = random.sample(chunks, num_samples)
    else:
        selected_chunks = chunks

    # Batch processing with ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {
            executor.submit(generate_qa_for_chunk, chunk, num_pairs_generated): idx
            for idx, chunk in enumerate(selected_chunks)
        }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Generating QA"
        ):
            try:
                qa_results = future.result()
                dataset.extend(qa_results)
            except Exception as e:
                logger.error(f"Worker error: {e}")

    testset_df = pd.DataFrame(data=dataset)
    logger.info(f"✅ Generated {len(testset_df)} total QA pairs")
    return testset_df


if __name__ == "__main__":
    # python -m  process_data.generator_dataset.dataset_dsm5

    with open(DSM5_CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    documents = transform_chunks(chunks=chunks_data)
    testset_df = generate_dataset(
        chunks=documents, num_samples=50, num_pairs_generated=2, batch_size=3
    )
    print(testset_df.head())
    testset_df.to_csv(DSM5_DATASET_EVAL_PATH, index=False)
