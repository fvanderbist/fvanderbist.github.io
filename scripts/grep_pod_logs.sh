#!/bin/bash
# Recherche une chaîne dans les logs de tous les pods d'un namespace Kubernetes,
# y compris le sidecar Istio (istio-proxy)

# Usage : ./grep_pod_logs.sh "mot_à_chercher" [namespace]
# Exemple : ./grep_pod_logs.sh "error" psd2

if [ -z "$1" ]; then
  echo "❌ Usage: $0 <mot_à_chercher> [namespace]"
  exit 1
fi

SEARCH_TERM="$1"
NAMESPACE="${2:-psd2}"  # Namespace par défaut = psd2

echo "🔎 Recherche de \"$SEARCH_TERM\" dans les logs du namespace \"$NAMESPACE\"..."
echo

# Récupère tous les pods du namespace
pods=$(kubectl get pods -n "$NAMESPACE" --no-headers -o custom-columns=":metadata.name")

if [ -z "$pods" ]; then
  echo "  Aucun pod trouvé dans le namespace \"$NAMESPACE\"."
  exit 0
fi

# Boucle sur chaque pod
for pod in $pods; do
  echo "  Pod: $pod"
  echo "----------------------------------------"

  # Liste les containers du pod (y compris istio-proxy s'il existe)
  containers=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.spec.containers[*].name}')

  for container in $containers; do
    echo "🧩 Container: $container"
    echo "----------------------------------------"
    kubectl logs -n "$NAMESPACE" "$pod" -c "$container" 2>/dev/null | grep -F --color=always -i "$SEARCH_TERM"
    echo
  done
done

echo "✅ Recherche terminée."