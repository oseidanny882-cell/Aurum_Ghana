# ============================================================
# Aurum Ghana - GKE Cluster Module
# ============================================================
# Usage:
#   module "gke" {
#     source = "./modules/gke"
#     project_id = "my-gcp-project"
#     region     = "us-central1"
#   }
# ============================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for the cluster"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "aurum-ghana"
}

variable "node_machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-2"
}

variable "min_nodes" {
  description = "Minimum number of nodes"
  type        = number
  default     = 1
}

variable "max_nodes" {
  description = "Maximum number of nodes"
  type        = number
  default     = 5
}

data "google_client_config" "current" {}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "google_container_cluster" "primary" {
  name               = "${var.cluster_name}-${random_id.suffix.hex}"
  location           = var.region
  initial_node_count = 1
  deletion_protection = false  # set true for production

  network    = "default"
  subnetwork = "default"

  node_pool {
    name               = "default-pool"
    initial_node_count = 1
    node_config {
      machine_type    = var.node_machine_type
      oauth_scopes = [
        "https://www.googleapis.com/auth/cloud-platform"
      ]
      labels = {
        "environment" = "production"
        "app"         = "aurum-ghana"
      }
    }
    autoscaling {
      min_node_count = var.min_nodes
      max_node_count = var.max_nodes
    }
  }

  ip_allocation_policy {}

  timeouts {
    create = "30m"
    update = "40m"
  }
}

resource "google_container_node_pool" "app_pool" {
  name       = "app-pool"
  cluster    = google_container_cluster.primary.id
  node_count = 2

  node_config {
    machine_type = var.node_machine_type
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    labels = {
      "environment" = "production"
      "app"         = "aurum-ghana"
      "tier"        = "app"
    }
    taint {
      key    = "app"
      value  = "aurum-ghana"
      effect = "NO_SCHEDULE"
    }
  }

  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }
}

# Generate kubeconfig for Terraform use
resource "local_file" "kubeconfig" {
  content  = <<-EOT
    apiVersion: v1
    clusters:
    - cluster:
        certificate-authority-data: ${google_container_cluster.primary.master_auth[0].cluster_ca_certificate}
        server: https://${google_container_cluster.primary.endpoint}
      name: ${google_container_cluster.primary.name}
    contexts:
    - context:
        cluster: ${google_container_cluster.primary.name}
        user: ${google_container_cluster.primary.name}
      name: ${google_container_cluster.primary.name}
    current-context: ${google_container_cluster.primary.name}
    kind: Config
    preferences: {}
    users:
    - name: ${google_container_cluster.primary.name}
      user:
        exec:
          apiVersion: client.authentication.k8s.io/v1beta1
          command: gke-gcloud-auth-plugin
          installHint: Install gke-gcloud-auth-plugin: https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
          provideClusterInfo: true
    EOT
  filename = "./kubeconfig-${google_container_cluster.primary.name}"
}

output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "kubeconfig_path" {
  value = "./kubeconfig-${google_container_cluster.primary.name}"
}
