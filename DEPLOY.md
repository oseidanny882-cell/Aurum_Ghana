# Deploying Aurum Ghana

This guide covers three environments: **local Docker**, **staging (GCP GKE)**, and **production**.

---

## 1. Local Development with Docker Compose

```bash
# 1. Copy env and fill in values
cp .env.example .env
# Edit .env — at minimum set:
#   JWT_SECRET_KEY=$(openssl rand -base64 64)
#   POSTGRES_PASSWORD=$(openssl rand -base64 32)

# 2. Start the stack
docker compose up -d

# 3. Run migrations (in the backend container)
docker compose exec backend flask db upgrade

# 4. Seed the database
docker compose exec backend python -m backend.seed

# 5. Verify
curl http://localhost:5000/health
curl http://localhost:8080/   # frontend

# Tear down (preserves DB data)
docker compose down

# Tear down + destroy DB data
docker compose down -v
```

---

## 2. Build & Push Docker Images

```bash
# Authenticate to your registry (example: GHCR)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and push backend
docker build -t ghcr.io/aurumghana/aurum-ghana:latest .
docker push ghcr.io/aurumghana/aurum-ghana:latest

# Build and push frontend
docker build -t ghcr.io/aurumghana/aurum-ghana-frontend:latest -f Dockerfile.frontend .
docker push ghcr.io/aurumghana/aurum-ghana-frontend:latest
```

---

## 3. Staging / Production — GKE (Google Cloud)

### Prerequisites
- Google Cloud SDK (`gcloud`)
- Terraform >= 1.5.0
- Helm >= 3.10
- kubectl
- A GCP project with billing enabled

### Step 1 — Create the GKE cluster

```bash
cd terraform/modules/gke
terraform init
terraform apply -var="project_id=YOUR_GCP_PROJECT_ID" -var="region=us-central1"
gcloud container clusters get-credentials $(terraform output cluster_name)
kubectl get nodes
```

### Step 2 — Install cert-manager (for TLS)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
kubectl wait --for=condition=Ready pods -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
kubectl apply -f - <<'EOF'
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: dev@aurumghana.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
EOF
```

### Step 3 — Deploy with Terraform

```bash
cd terraform
terraform init
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with real secret values
terraform plan
terraform apply
```

### Step 4 — Run migrations

```bash
# Forward port to backend pod
BACKEND_POD=$(kubectl get pods -n aurum-ghana -l app.kubernetes.io/name=aurum-ghana-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n aurum-ghana $BACKEND_POD -- flask db upgrade
kubectl exec -n aurum-ghana $BACKEND_POD -- python -m backend.seed
```

### Step 5 — Verify

```bash
kubectl get all -n aurum-ghana
kubectl get ingress -n aurum-ghana
curl https://api.aurumghana.com/health
```

---

## 4. Helm Values Reference

| Key | Description | Default |
|---|---|---|
| `replicaCount` | Backend replicas | `3` |
| `image.repository` | Backend image | `aurumghana/api` |
| `image.tag` | Backend tag | `latest` |
| `backend.resources` | CPU/memory requests/limits | see `values.yaml` |
| `postgresql.enabled` | Deploy bundled PostgreSQL | `true` |
| `postgresql.persistence.size` | PVC size | `20Gi` |
| `ingress.enabled` | Create Ingress | `true` |
| `ingress.className` | Ingress class | `nginx` |

Override any value at deploy time:

```bash
helm upgrade --install aurum-ghana ./helm \
  --namespace aurum-ghana \
  --set image.tag=v1.2.3 \
  --set replicaCount=5 \
  --set 'secret.postgresPassword=MY_PASSWORD'
```

---

## 5. Secrets Management

Never commit real secrets to the repository. Recommended approaches:

### Option A — Terraform `tfvars` (simplest)
```bash
# terraform.tfvars
jwt_secret_key          = "sk_live_..."
postgres_password       = "pg_password"
paystack_secret_key     = "sk_live_..."
paystack_webhook_secret = "whsec_..."
smtp_user               = "user@gmail.com"
smtp_pass               = "app_password"
```

### Option B — Kubernetes Secrets (pre-created)
```bash
kubectl create secret generic aurum-postgres-secret \
  --from-literal=postgres-password=YOUR_PASSWORD \
  -n aurum-ghana

# Then in terraform:
#   secret.postgresPassword = ""  (disabled — uses pre-created secret)
```

### Option C — Vault / GCP Secret Manager
Reference secrets via External Secrets Operator in the Helm chart.

---

## 6. Database Migrations in Production

Migrations run as a Kubernetes Job before each Helm upgrade:

```bash
# Manual migration
BACKEND_POD=$(kubectl get pods -n aurum-ghana -l app.kubernetes.io/name=aurum-ghana-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n aurum-ghana $BACKEND_POD -- flask db upgrade
```

---

## 7. Rollback

```bash
# Helm rollback
helm rollback aurum-ghana -n aurum-ghana

# Rollback database (if needed)
kubectl exec -n aurum-ghana $BACKEND_POD -- flask db downgrade -1
```

---

## 8. Monitoring & Logs

```bash
# Follow backend logs
kubectl logs -n aurum-ghana -l app.kubernetes.io/name=aurum-ghana-api -f

# Check pod status
kubectl get pods -n aurum-ghana -w

# Port-forward for local debugging
kubectl port-forward -n aurum-ghana svc/aurum-ghana-backend 5000:80
```
