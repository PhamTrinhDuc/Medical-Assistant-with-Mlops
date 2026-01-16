import pandas as pd

df = pd.read_csv(
    "/home/ducpham/workspace/LLM-Chatbot-with-LangChain-and-Neo4j/data/evaluate/results/agent_result_eval.csv"
)
print(df.iloc[10:20])
