

resource "kubernetes_namespace" "phoenix" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/name" = "phoenix"
      environment              = var.environment
    }
  }
}

# 2. Khai báo Deployment cho Phoenix
resource "kubernetes_deployment" "phoenix" {
  metadata {
    name = "phoenix"
    namespace = kubernetes_namespace.phoenix.metadata[0].name
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "phoenix"
      }
    }

    template {
      metadata {
        labels = {
          app = "phoenix"
        }
      }

      spec {
        container {
          name = "phoenix"
          image = "arizephoenix/phoenix:latest"

          port {
            name = "http"
            container_port = 6006
          }

          port {
            name = "grpc"
            container_port = 4317
          }

          env {
            name  = "PHOENIX_PORT"
            value = "6006"
          }
          
          resources {
            requests = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }
        }
      }
    }
  }
}

# 3. Tạo Service để truy cập (NodePort cho Minikube)
resource "kubernetes_service" "phoenix_svc" {
  metadata {
    name      = "phoenix-service"
    namespace = kubernetes_namespace.phoenix.metadata[0].name
  }

  spec {
    selector = {
      app = kubernetes_deployment.phoenix.spec[0].template[0].metadata[0].labels.app
    }

    port {
      name        = "ui"
      port        = 6006
      target_port = 6006
      node_port   = 30006
    }

    port {
      name        = "otlp"
      port        = 4317
      target_port = 4317
      node_port   = 30317
    }

    type = "NodePort"
  }
}