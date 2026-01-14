import pandas as pd
from utils import AppConfig


AGENT_RESULT_EVAL_PATH = AppConfig.AGENT_RESULT_EVAL_PATH
CYPHER_RESULT_EVAL_PATH = AppConfig.CYPHER_RESULT_EVAL_PATH
DSM5_RESULT_EVAL_PATH = AppConfig.DSM5_RESULT_EVAL_PATH

df_agent = pd.read_csv(AGENT_RESULT_EVAL_PATH)
df_cypher = pd.read_csv(CYPHER_RESULT_EVAL_PATH)
df_dsm5 = pd.read_csv(DSM5_RESULT_EVAL_PATH)


def summarize_evaluation_results():
    accuracy_agent = (df_agent["accuracy"].sum() / len(df_agent)) * 100

    jaccard_cypher = (df_cypher["jacc"].sum() / len(df_cypher)) * 100

    context_recall_dsm5 = (df_dsm5["context_recall"].sum() / len(df_dsm5)) * 100
    faithfulness_dsm5 = (df_dsm5["faithfulness"].sum() / len(df_dsm5)) * 100
    #   factual_correctness_dsm5 = (df_dsm5['factual_correctness(mode=f1)'].sum() / len(df_dsm5)) * 100
    answer_relevancy_dsm5 = (df_dsm5["answer_relevancy"].sum() / len(df_dsm5)) * 100
    context_precision_dsm5 = (df_dsm5["context_precision"].sum() / len(df_dsm5)) * 100

    df_summary = pd.DataFrame(
        {
            "Metric": [
                "Agent Accuracy",
                "Cypher Jaccard Similarity",
                "DSM5 Context Recall",
                "DSM5 Faithfulness",
                "DSM5 Factual Correctness",
                "DSM5 Answer Relevancy",
                "DSM5 Context Precision",
            ],
            "Score (%)": [
                accuracy_agent,
                jaccard_cypher,
                context_recall_dsm5,
                faithfulness_dsm5,
                answer_relevancy_dsm5,
                context_precision_dsm5,
            ],
        }
    )
    summary_path = AppConfig.EVALUATION_SUMMARY_PATH
    df_summary.to_csv(summary_path, index=False)
