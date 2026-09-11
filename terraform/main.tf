terraform {
  required_version = ">= 1.5.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# Deploy the Aurum Ghana Helm chart
resource "helm_release" "aurum_ghana" {
  name             = "aurum-ghana"
  chart            = "../helm"
  namespace        = var.namespace
  create_namespace = true

  # Image overrides
  set {
    name  = "image.repository"
    value = var.backend_image_repository
  }

  set {
    name  = "image.tag"
    value = var.backend_image_tag
  }

  set {
    name  = "imageFrontend.repository"
    value = var.frontend_image_repository
  }

  set {
    name  = "imageFrontend.tag"
    value = var.frontend_image_tag
  }

  set {
    name  = "replicaCount"
    value = tostring(var.replica_count)
  }

  # Backend env
  set {
    name  = "backend.env.FLASK_ENV"
    value = "production"
  }

  # Config
  set {
    name  = "config.frontendUrl"
    value = var.frontend_url
  }

  set {
    name  = "config.corsOrigins"
    value = var.cors_origins
  }

  # Secret values (sensitive)
  set_sensitive {
    name  = "secret.jwtSecretKey"
    value = var.jwt_secret_key
  }

  set_sensitive {
    name  = "secret.postgresPassword"
    value = var.postgres_password
  }

  set_sensitive {
    name  = "secret.paystackSecretKey"
    value = var.paystack_secret_key
  }

  set_sensitive {
    name  = "secret.paystackPublicKey"
    value = var.paystack_public_key
  }

  set_sensitive {
    name  = "secret.paystackWebhookSecret"
    value = var.paystack_webhook_secret
  }

  set_sensitive {
    name  = "secret.smtpUser"
    value = var.smtp_user
  }

  set_sensitive {
    name  = "secret.smtpPass"
    value = var.smtp_pass
  }

  # Ingress
  set {
    name  = "ingress.enabled"
    value = tostring(var.ingress_enabled)
  }

  depends_on = []
}
