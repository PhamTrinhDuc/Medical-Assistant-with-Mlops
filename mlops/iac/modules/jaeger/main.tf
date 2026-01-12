# Jaeger Module - Placeholder
# TODO: Implement Jaeger (distributed tracing) configuration

resource "kubernetes_namespace" "jaeger" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/name" = "jaeger"
      environment              = var.environment
    }
  }
}

resource "helm_release" "jaeger" {
  name       = "jaeger"
  repository = "https://jaegertracing.github.io/helm-charts"
  chart      = "jaeger"
  namespace  = kubernetes_namespace.jaeger.metadata[0].name

  values = [
    file("${path.module}/jaeger-values.yaml")
  ]
}