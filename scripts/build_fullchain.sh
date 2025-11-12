#!/usr/bin/env bash
set -e

TMP_CERT=$(mktemp /tmp/cert.XXXXXX.pem)
OUT="fullchain.pem"

echo "👉 Collez le contenu du certificat PEM ci-dessous (terminez avec Ctrl+D) :"
cat > "$TMP_CERT"

echo "🔍 Recherche de la chaîne de certificats à partir du certificat collé..."
cp "$TMP_CERT" "$OUT"
CERT="$TMP_CERT"

while true; do
  URL=$(openssl x509 -in "$CERT" -noout -text | grep -A1 "CA Issuers" | grep -o 'http[^ ]*' | head -n1)
  if [ -z "$URL" ]; then
    echo "✅ Aucun autre certificat intermédiaire trouvé."
    break
  fi

  echo "→ Téléchargement de l’émetteur : $URL"
  curl -fsSL "$URL" -o issuer.der || { echo "⚠️ Impossible de télécharger $URL"; break; }

  if openssl x509 -in issuer.der -inform DER -out issuer.pem -outform PEM 2>/dev/null; then
    cat issuer.pem >> "$OUT"
    CERT=issuer.pem
    SUBJ=$(openssl x509 -in "$CERT" -noout -subject)
    ISSR=$(openssl x509 -in "$CERT" -noout -issuer)
    if [ "$SUBJ" = "$ISSR" ]; then
      echo "🏁 Certificat auto-signé atteint (racine)."
      break
    fi
  else
    echo "⚠️ Impossible de décoder le certificat $URL"
    break
  fi
done

echo "✅ Chaîne complète enregistrée dans : $OUT"