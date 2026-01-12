import ast
import pandas as pd
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from groq import Groq
from loguru import logger
from neo4j import GraphDatabase
from pydantic import BaseModel, Field

from prompt.evaluate import (
    SYSTEM_CYPHER_GENERATION_TEMPLATE,
    USER_CYPHER_GENERATION_TEMPLATE,
)
from utils import AppConfig


driver = GraphDatabase.driver(
    uri=AppConfig.NEO4J_URI, auth=(AppConfig.NEO4J_USER, AppConfig.NEO4J_PASSWORD)
)
groq = Groq(api_key=AppConfig.GROQ_API_KEY)


# for model have method response_format of Groq
class CypherPairGeneration(BaseModel):
    question: str = Field(..., description="Question narual of human")
    cypher_gt: str = Field(..., description="Cypher generated following question")


class CypherDataset(BaseModel):
    dataset: List[CypherPairGeneration]


# for model don't method response_format of Groq
RESPONSE_FORMAT = {
    "dataset": [
        {"question": "string", "cypher_gt": "string"},
        {"question": "string next", "cypher_gt": "string next"},
    ]
}


TOPICS_SPECIFICS = {
    "Hospital Analytics": [
        "Hospital",
        "Physician",
        "Visit",
    ],  # Quản trị & Hiệu suất Bệnh viện
    "Patient Journey": [
        "Patient",
        "Visit",
        "Hospital",
        "Physician",
    ],  # Hành trình & Hồ sơ Bệnh nhân
    "Healthcare Economics": ["Visit", "Payer", "Physician"],  # Tài chính & Bảo hiểm
    "Advanced Reasoning": [],
    "Physician Career & Background": [
        "Physician",
        "Hospital",
    ],  # Phân tích Sự nghiệp & Nhân sự
    "Admission Efficiency": [
        "Visit",
        "Hospital",
        "Patient",
    ],  # Quy trình Nhập viện & Hiệu quả Vận hành
    "Data Validation & Integrity": [
        "Review",
        "Visit",
        "Physician",
        "Patient",
    ],  # Đối soát Dữ liệu & Tính nhất quán
    "Clinical Grouping": ["Patient", "Visit"],  # Phân tích Nhóm bệnh & Dịch tễ
}


def get_graph_schema():
    with driver.session() as session:
        # 1. Lấy thông tin Nodes & Properties
        nodes_info = session.run("CALL db.schema.nodeTypeProperties()").data()

        # 2. Lấy thông tin Relationships & Properties
        rels_info = session.run("CALL db.schema.relTypeProperties()").data()

        # 3. Lấy Topology (Mối quan hệ giữa các Node)
        topology = session.run(
            """
        MATCH (n)-[r]->(m)
        RETURN DISTINCT labels(n) as source, type(r) as rel, labels(m) as target
    """
        ).data()

        # Format thành chuỗi văn bản cho LLM
        schema_text = "Node Labels & Properties:\n"
        for node in nodes_info:
            schema_text += f"- {node['nodeLabels']}: {node['propertyName']} ({node['propertyTypes']})\n"

        schema_text += "\nRelationship Properties:\n"
        for rel in rels_info:
            schema_text += (
                f"- {rel['relType']}: {rel['propertyName']} ({rel['propertyTypes']})\n"
            )

        schema_text += "\nRelationship Topology:\n"
        for top in topology:
            schema_text += f"- ({top['source']}) -[:{top['rel']}]-> ({top['target']})\n"

    driver.close()
    return schema_text


def generate_cypher_query(
    schema_text: str,
    topic: str,
    focus_nodes: Optional[List[str]] = None,
    num_pairs: int = 5,
):

    system_prompt = SYSTEM_CYPHER_GENERATION_TEMPLATE.format(schema=schema_text)
    user_prompt = USER_CYPHER_GENERATION_TEMPLATE.format(
        topic=topic,
        focus_nodes=focus_nodes,
        num_pairs=num_pairs,
        format_schema=RESPONSE_FORMAT,
    )

    response = groq.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=AppConfig.GROQ_LLM,
        temperature=0.1,
    )
    raw_response = response.choices[0].message.content or "{}"
    response_json = ast.literal_eval(raw_response)

    return response_json


def generate_dataset(num_pairs: int = 3, batch_size: int = 3) -> pd.DataFrame:
    dataset = []
    schema_info = get_graph_schema()

    logger.info("Generating Cypher query dataset with batching...")
    topics_list = list(TOPICS_SPECIFICS.items())

    # Batch processing với 3 workers
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        futures = {
            executor.submit(
                generate_cypher_query, schema_info, topic, focus_nodes, num_pairs
            ): (idx, topic)
            for idx, (topic, focus_nodes) in enumerate(topics_list)
        }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Generating topics"
        ):
            try:
                idx, topic = futures[future]
                data = future.result()
                dataset.extend(data.get("dataset", []))

            except Exception as e:
                logger.error(f"Error generating for topic: {e}")

    df = pd.DataFrame(dataset)
    logger.info(f"Generated dataset with {len(df)} samples.")
    return df


if __name__ == "__main__":
    df_dataset = generate_dataset(num_pairs=5)
    df_dataset.to_csv(AppConfig.CYPHER_DATASET_EVAL_PATH, index=False)

    print(df_dataset.head())
