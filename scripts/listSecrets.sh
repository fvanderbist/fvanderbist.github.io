#!/bin/bash

# Set the namespace
NAMESPACE=$1

# Get all deployments in the namespace
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}')

# Loop through each deployment
for DEPLOYMENT in $DEPLOYMENTS
do
  # Check if the deployment exists
  kubectl get deployments $DEPLOYMENT -n $NAMESPACE &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Deployment $DEPLOYMENT doesn't exist in namespace $NAMESPACE, skipping..."
    continue
  fi

  # Get the secrets used by the deployment
  SECRETS=$(kubectl get deployment $DEPLOYMENT --namespace $NAMESPACE -o jsonpath='{.spec.template.spec.containers[*].envFrom[*].secretRef.name}')

  # Print the secrets, if any
  if [ -n "$SECRETS" ]; then
    echo "Secrets used by deployment $DEPLOYMENT in namespace $NAMESPACE:"
    echo $SECRETS
  fi
done