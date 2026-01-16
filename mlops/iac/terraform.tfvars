environment = "dev"

app_namespace           = "default"
ingress_nginx_namespace = "ingress-nginx"
logging_namespace       = "loki-stack"
monitoring_namespace    = "monitoring"
jaeger_namespace        = "jaeger"
phoenix_namespace       = "phoenix"

ingress_config = {
  app_namespace  = "default"
  jaeger_namespace = "jaeger"
  phoenix_namespace = "phoenix"

  frontend_host  = "chatbot-medical.local"
  backend_host   = "api.chatbot-medical.local"
  jaeger_host    = "jaeger.local"
  phoenix_host   = "phoenix.local"

  frontend_port  = 8501
  backend_port   = 8000
  jaeger_port    = 16686
  phoenix_port   = 6006

  # Ingress chỉ nhận tên service đơn giản
  frontend_svc   = "chatbot-frontend"
  backend_svc    = "chatbot-backend"
  jaeger_svc     = "jaeger"
  phoenix_svc    = "phoenix"
}
