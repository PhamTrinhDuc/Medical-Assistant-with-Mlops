# Jaeger Module - Outputs

output "namespace" {
  description = "Namespace where Phonix is deployed"
  value       = kubernetes_namespace.phoenix.metadata[0].name
}
