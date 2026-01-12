import socket
import redis
from typing import Dict
from utils import logger, AppConfig
from urllib.parse import urlparse
from elasticsearch import Elasticsearch
from neo4j import GraphDatabase
from langfuse import Langfuse


def _is_jaeger_available(endpoint: str, timeout: int = 2):
    try:
        parsed = urlparse(endpoint)
        host = parsed.hostname
        port = parsed.port

        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError) as e:
        logger.warning(f"⚠️  Jaeger OTLP not reachable at {host}:{port} - {e}")
        return False


async def _check_external_services() -> Dict[str, bool]:
    """
    Check health of external services before app starts accepting requests.
    Returns dict with service status.
    """
    status = {}

    # Check Elasticsearch
    try:
        es_client = Elasticsearch([f"http://{AppConfig.ELS_HOST}:{AppConfig.ELS_PORT}"])
        if es_client.ping():
            logger.info("✅ Elasticsearch is healthy")
            status["elasticsearch"] = True
        else:
            logger.warning("❌ Elasticsearch ping failed")
            status["elasticsearch"] = False
    except Exception as e:
        logger.error(f"❌ Elasticsearch connection error: {e}")
        status["elasticsearch"] = False

    # Check Neo4j
    try:
        driver = GraphDatabase.driver(
            AppConfig.NEO4J_URI,
            auth=(AppConfig.NEO4J_USER, AppConfig.NEO4J_PASSWORD),
        )
        driver.verify_connectivity()
        logger.info("✅ Neo4j is healthy")
        status["neo4j"] = True
        driver.close()
    except Exception as e:
        logger.error(f"❌ Neo4j connection error: {e}")
        status["neo4j"] = False

    # Check Redis
    try:
        redis_client = redis.from_url(AppConfig.REDIS_URL)
        redis_client.ping()
        logger.info("✅ Redis is healthy")
        status["redis"] = True
    except Exception as e:
        logger.error(f"❌ Redis connection error: {e}")
        status["redis"] = False

    # Check Langfuse
    try:
        langfuse = Langfuse(
            public_key=AppConfig.LANGFUSE_PUBLIC_KEY,
            secret_key=AppConfig.LANGFUSE_SECRET_KEY,
            host=AppConfig.LANGFUSE_ENDPOINT,
        )

        result = langfuse.auth_check()
        if result:
            logger.info("✅ Langfuse is healthy")
            status["langfuse"] = True
        else:
            logger.warning("❌ Langfuse auth check failed")
            status["langfuse"] = False

    except Exception:
        logger.error("❌ Langfuse connection error")
        status["langfuse"] = False

    return status
