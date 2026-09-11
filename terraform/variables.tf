# ============================================================
# Aurum Ghana - Terraform Variables
# ============================================================

variable "kubeconfig_path" {
  description = "Path to kubeconfig file for the target cluster"
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Kubernetes namespace to deploy into"
  type        = string
  default     = "aurum-ghana"
}

# --- Images ---

variable "backend_image_repository" {
  description = "Docker image repository for the backend"
  type        = string
  default     = "ghcr.io/aurumghana/aurum-ghana"
}

variable "backend_image_tag" {
  description = "Docker image tag for the backend"
  type        = string
  default     = "latest"
}

variable "frontend_image_repository" {
  description = "Docker image repository for the frontend"
  type        = string
  default     = "ghcr.io/aurumghana/aurum-ghana-frontend"
}

variable "frontend_image_tag" {
  description = "Docker image tag for the frontend"
  type        = string
  default     = "latest"
}

# --- Application ---

variable "replica_count" {
  description = "Number of backend replicas"
  type        = number
  default     = 3
}

variable "frontend_url" {
  description = "Public frontend URL"
  type        = string
  default     = "https://aurumghana.com"
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins"
  type        = string
  default     = "https://aurumghana.com,https://www.aurumghana.com"
}

variable "ingress_enabled" {
  description = "Enable the ingress resource"
  type        = bool
  default     = true
}

# --- Secrets (sensitive — set via terraform.tfvars, env vars, or secret manager) ---

variable "jwt_secret_key" {
  description = "Secret key for signing JWTs (min 32 chars)"
  type        = string
  sensitive   = true
  default     = "" # MUST be overridden
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
  default     = "" # MUST be overridden
}

variable "paystack_secret_key" {
  description = "Paystack secret key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "paystack_public_key" {
  description = "Paystack public key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "paystack_webhook_secret" {
  description = "Paystack webhook signing secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_user" {
  description = "SMTP username for transactional email"
  type        = string
  sensitive   = true
  default     = ""
}

variable "smtp_pass" {
  description = "SMTP password"
  type        = string
  sensitive   = true
  default     = ""
}
