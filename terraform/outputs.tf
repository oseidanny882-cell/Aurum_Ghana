output "namespace" {
  description = "Kubernetes namespace Aurum Ghana was deployed to"
  value       = helm_release.aurum_ghana.namespace
}

output "release_name" {
  description = "Helm release name"
  value       = helm_release.aurum_ghana.name
}

output "release_status" {
  description = "Helm release status"
  value       = helm_release.aurum_ghana.status
}

output "ingress_hostname_api" {
  description = "Public hostname for the API"
  value       = "api.aurumghana.com"
}

output "ingress_hostname_web" {
  description = "Public hostname for the web app"
  value       = "aurumghana.com"
}
