"""Tool evaluator for analyzing agent tool calls without execution."""

import pandas as pd
from tqdm import tqdm
from agents import HospitalRAGAgent
from utils import logger, AppConfig

AGENT_DATASET_EVAL_PATH = AppConfig.AGENT_DATASET_EVAL_PATH
AGENT_RESULT_EVAL_PATH = AppConfig.AGENT_RESULT_EVAL_PATH


def evaluate_tools(agent: HospitalRAGAgent, eval_dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Compare tool selections for multiple queries.
    Useful for analyzing patterns in tool usage.
    Args:
        queries: List of queries to analyze

    Returns:
        Dictionary with tool selection analysis
    """
    results = []

    for idx, row in tqdm(
        eval_dataset.iterrows(),
        total=len(eval_dataset),
        desc="Evaluating tool selections for agent",
    ):

        query = row["question"]
        label = (
            row["category"] if isinstance(row["category"], list) else [row["category"]]
        )

        result = agent.get_tools_call(query)
        results.append(
            {
                "query": query,
                "tool_label": label,
                "tool_calls": result["tool_calls"],
                "score": 1 if label == result["tool_calls"] else 0,
            }
        )

    return pd.DataFrame(results)


if __name__ == "__main__":
    # python -m evaluator.agent_tools

    agent = HospitalRAGAgent(
        llm_model="openai",
        embedding_model="openai",
        user_id="test_user",
    )

    eval_dataset = pd.read_csv(AGENT_DATASET_EVAL_PATH).head()

    df_results = evaluate_tools(agent=agent, eval_dataset=eval_dataset)
    df_results.to_csv(AGENT_RESULT_EVAL_PATH, index=False)
