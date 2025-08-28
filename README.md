# Document Processing System

This project is a **Document Processing System** built with **Flask API**, **Azure Blob Storage**, **MongoDB**, **Prometheus metrics**, and **KEDA for scaling**. It supports **automatic scaling on Azure Kubernetes Service (AKS)** and includes a **CI/CD pipeline using GitHub Actions** for containerized deployments with **Azure Container Registry (ACR)**.

---

## ✅ Features
- **Flask API** to handle document processing requests.
- **MongoDB** as the database for storing job and document metadata.
- **Azure Blob Storage** for storing uploaded files.
- **Prometheus** for metrics collection and **Grafana** for visualization.
- **KEDA** for event-driven scaling of background worker jobs.
- **Fully automated CI/CD pipeline** using GitHub Actions for:
  - Building Docker images.
  - Pushing images to **Azure Container Registry (ACR)**.
  - Deploying to **Azure Kubernetes Service (AKS)**.

---
## Project structure

```
├── api
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── api_dashboard_with_alerts.json
├── downloader_dashboard_with_alerts.json
├── k8s
│   ├── api-deployment.yaml          # API Deployment + Service
│   ├── configmap.yaml               # Non-secret config (e.g., AZURE_CONTAINER)
│   ├── keda-scaledjob.yaml          # Worker as a KEDA ScaledJob
│   ├── secrets.yaml                 # (Do NOT commit; created by CI instead)
│   └── service.yaml                 # Service that exposes worker metrics for Prometheus
└── worker
    ├── Dockerfile
    ├── downloader.py                # Exposes /metrics on :9100 and runs the job
    ├── requirements.txt
    └── run_with_job_id.py
```
## 🛠️ Project Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web UI        │    │   MongoDB        │    │  Azure Blob     │
│   (Port 5001)   │◄──►│   - jobs         │◄──►│   Storage       │
│                 │    │   - documents    │    │   (text files)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       ▲
         ▼                        ▼                       │
┌─────────────────┐    ┌──────────────────┐               │
│   API Service   │    │  KEDA ScaledJob  │─────────────-─┘
│   /create-job   │    │  Worker Pods     │
│   /metrics      │    │  /metrics:9100   │
└─────────────────┘    └──────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   Prometheus    │    │    Grafana       │
│   (Scraping)    │◄──►│   (Dashboard)    │
└─────────────────┘    └──────────────────┘
```

---

## 📦 Tech Stack
- **Backend:** Python (Flask)
- **Database:** MongoDB
- **Storage:** Azure Blob Storage
- **Containerization:** Docker
- **Orchestration:** Kubernetes (AKS)
- **Scaling:** KEDA
- **Monitoring:** Prometheus & Grafana
- **CI/CD:** GitHub Actions
- **Registry:** Azure Container Registry (ACR)

---

## ⚙️ Prerequisites

- **Azure account** with:
  - AKS cluster created
  - ACR (Azure Container Registry) created
- **kubectl** and **Azure CLI** installed and configured
- **Docker** installed
- **GitHub repository secrets** configured:
  - `AZURE_CREDENTIALS` → Azure service principal JSON
  - `ACR_NAME` → Your Azure Container Registry name
  - `RESOURCE_GROUP` → Resource group for AKS
  - `AKS_CLUSTER_NAME` → AKS cluster name
  - `MONGO_URI` → Your MongoDB connection string
  - `AZURE_BLOB_CONN` → Azure Blob Storage connection string

---

## 🔑 GitHub Actions Secrets Setup
Set the following secrets in **Repository → Settings → Secrets and variables → Actions**:

| Secret Name       | Description                                   |
|--------------------|-----------------------------------------------|
| `AZURE_CREDENTIALS`| Azure service principal credentials in JSON format |
| `ACR_NAME`         | Azure Container Registry name               |
| `RESOURCE_GROUP`   | AKS resource group name                     |
| `AKS_CLUSTER_NAME` | AKS cluster name                            |
| `MONGO_URI`        | MongoDB URI for the application             |
| `AZURE_BLOB_CONN`  | Azure Blob Storage connection string        |

---

## 🚀 Deployment Workflow
This project uses **GitHub Actions** for CI/CD. The workflow:
1. Logs in to **Azure** using `azure/login@v1`.
2. Logs in to **ACR** and pushes Docker images for:
   - `api` service
   - `document-downloader` worker
3. Connects to the **AKS cluster** using `az aks get-credentials`.
4. Creates Kubernetes **Secrets** dynamically (no YAML secrets committed to repo).
5. Applies all Kubernetes manifests from the `k8s/` directory.

---

### ✅ Example GitHub Actions Workflow (`.github/workflows/aks-deploy.yml`)
```yaml
name: CI/CD for AKS Deployment

on:
  push:
    branches:
      - main

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Azure Container Registry Login
        run: az acr login --name ${{ secrets.ACR_NAME }}

      - name: Build and Push API Docker Image
        run: |
          IMAGE_API=${{ secrets.ACR_NAME }}.azurecr.io/api:latest
          cd api
          docker build -t $IMAGE_API .
          docker push $IMAGE_API

      - name: Build and Push Worker Docker Image
        run: |
          IMAGE_WORKER=${{ secrets.ACR_NAME }}.azurecr.io/worker:latest
          cd worker
          docker build -t $IMAGE_WORKER .
          docker push $IMAGE_WORKER

      - name: Get AKS Credentials
        run: |
          az aks get-credentials --resource-group ${{ secrets.RESOURCE_GROUP }}                                  --name ${{ secrets.AKS_CLUSTER_NAME }}                                  --overwrite-existing

      - name: Create namespace if not exists
        run: |
          kubectl get namespace my-project || kubectl create namespace my-project

      - name: Create Kubernetes Secret for App
        run: |
          kubectl create secret generic app-secrets             --from-literal=MONGO_URI="${{ secrets.MONGO_URI }}"             --from-literal=AZURE_BLOB_CONN="${{ secrets.AZURE_BLOB_CONN }}"             --dry-run=client -o yaml | kubectl apply -f -

      - name: Deploy to AKS
        run: |
          kubectl apply -f k8s/
```

---

## 🗂️ Kubernetes Manifests (`k8s/` folder)
- `api-deployment.yaml` → API Deployment + Service
- `worker-scaledjob.yaml` → KEDA ScaledJob for document downloader
- `mongodb.yaml` → MongoDB StatefulSet & Service
- `prometheus-service.yaml` → Service for Prometheus scraping metrics

---

## ✅ How to Access MongoDB on AKS
1. **Port-forward MongoDB service:**
   ```bash
   kubectl port-forward svc/mongodb-service 27017:27017
   ```
2. **Connect using MongoDB Compass:**
   ```
   mongodb://<username>:<password>@127.0.0.1:27017/
   ```

---

## ✅ Monitoring Setup
- **Prometheus** deployed using Helm.
- **Grafana** for visualization of metrics.
- Metrics exposed at `/metrics` on `9100` port in API and worker.

---

## 🔍 Troubleshooting
- **ImagePullBackOff:** Ensure ACR role assignment is done:
  ```bash
  az aks update -n <AKS_CLUSTER_NAME> -g <RESOURCE_GROUP> --attach-acr <ACR_NAME>
  ```
- **Authentication failed in MongoDB:** Verify username/password and secret creation.

---

## 📜 License
This project is licensed under the MIT License.
