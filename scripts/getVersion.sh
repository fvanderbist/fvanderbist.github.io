#!/bin/bash

# Function to list deployments in a namespace
list_deployments() {
    kubectl get deployments -n "$1"
}

# Function to get the version of a deployment
get_version() {
    kubectl get deployment "$1" -n "$2" -o=jsonpath='{.spec.template.spec.containers[0].image}' | cut -d':' -f2
}

# Main script
while true; do
    if [ "$#" -eq 0 ]; then
        read -p "Enter the namespace: " namespace
    elif [ "$#" -eq 1 ]; then
        namespace="$1"
    else
        echo "Usage: $0 [namespace]"
        exit 1
    fi

    if kubectl get namespaces "$namespace" &>/dev/null; then
        break
    else
        echo "Namespace $namespace not found. Please try again."
    fi
done

echo "Deployments in namespace $namespace:"
list_deployments "$namespace"

read -p "Enter the name of the deployment you want to get the version for: " deployment_name

# Check if the deployment exists
if ! kubectl get deployment "$deployment_name" -n "$namespace" &>/dev/null; then
    echo "Deployment $deployment_name not found in namespace $namespace."
    exit 1
fi

deployment_version=$(get_version "$deployment_name" "$namespace")
echo "Current version of $deployment_name: $deployment_version"