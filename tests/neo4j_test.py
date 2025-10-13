import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv(".env.dev")


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GRAPHDB_NAME = os.getenv("GRAPHDB_NAME")
STRUCTURED_DATA_PATH = "data/english/visits.csv"


visits_df = pd.read_csv(STRUCTURED_DATA_PATH)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def test_insert_data(): 
  # số lượng bác sĩ được bệnh tuyển bởi bệnh viện có id=14
  count_physicians_sql = visits_df[visits_df['hospital_id'] == 14]['physician_id'].nunique()
  with driver.session(database=GRAPHDB_NAME) as session: 
    query = """
    MATCH (h:Hospital {id: $hid})-[r:EMPLOYS]->(p:Physician)
    RETURN count(DISTINCT p) AS cnt
    """
    result = session.run(query, hid=14)
    record = result.single()
    count_physicians_cypher = record["cnt"] if record else 0
  assert count_physicians_cypher == count_physicians_sql, f"expected {count_physicians_sql}, got {count_physicians_cypher}"
  print(f"Hospital 14 employs {count_physicians_cypher} physicians (expected {count_physicians_sql})")


if __name__ == "__main__": 
  test_insert_data()

