#!/bin/bash
set -e

# ✅ Variables
PVC_NAME="pipelinerun-pvc"
PIPELINE_NAME="cd-pipeline"
REPO_URL="https://github.com/Umairkhan603/devops-capstone-project.git"
BRANCH="main"
BUILD_IMAGE="image-registry.openshift-image-registry.svc:5000/$SN_ICR_NAMESPACE/accounts:1"

echo "🚀 Step 1: Cleaning or recreating PVC..."
# Delete PVC if it exists
if oc get pvc $PVC_NAME &>/dev/null; then
  echo "Deleting existing PVC: $PVC_NAME"
  oc delete pvc $PVC_NAME
fi

# Recreate PVC
echo "Creating fresh PVC: $PVC_NAME"
oc apply -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $PVC_NAME
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# Wait a few seconds for PVC to be bound
echo "Waiting for PVC to be ready..."
sleep 5

echo "✅ Step 2: Starting Tekton pipeline..."
tkn pipeline start $PIPELINE_NAME \
  -p repo-url="$REPO_URL" \
  -p branch="$BRANCH" \
  -p build-image="$BUILD_IMAGE" \
  -w name=pipeline-workspace,claimName=$PVC_NAME \
  -s pipeline \
  --showlog

echo "🎉 Pipeline started successfully!"
