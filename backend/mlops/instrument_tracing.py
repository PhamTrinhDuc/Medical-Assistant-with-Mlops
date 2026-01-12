from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from utils import logger, _is_jaeger_available


def setup_tracing(app: FastAPI, service_name: str, jaeger_endpoint: str):
    if not _is_jaeger_available(jaeger_endpoint):
        logger.warning("❌ Jaeger unavailable - Tracing will be disabled for this run.")
        return
    logger.info(f"🚀 Setting up tracing for: {service_name}")

    try:
        # 1. Khai báo Resource (Định danh service)
        resource = Resource(attributes={SERVICE_NAME: service_name})

        # 2. Cấu hình OTLP Exporter (Gửi dữ liệu qua gRPC)
        otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)

        # 3. Thiết lập Tracer Provider
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # 4. Đăng ký toàn cục
        trace.set_tracer_provider(provider)

        # 5. Tự động theo dõi các request của FastAPI
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics",  # Không trace các request kiểm tra hệ thống
        )

        logger.info(f"✅ Tracing setup successfully connected to {jaeger_endpoint}")
    except Exception as e:
        logger.error(f"❌ Error during tracing setup: {e}")
