#!/bin/sh
# Ejecutar EN EL MASTER. Genera los secretos al vuelo (no quedan en ningún archivo)
# y copia la API key desde el Secret ya existente vton-api (nunca se imprime).
K="sudo /srv/magnum/bin/kubectl --kubeconfig /etc/kubernetes/admin.conf"
rnd() { head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c "$1"; }
APIKEY=$($K -n vton get secret vton-api -o jsonpath="{.data.${KEYNAME:-VTON_API_KEYS}}" | base64 -d)
ADMINPW=$(rnd 16)
$K -n vton-web create secret generic vtonweb \
  --from-literal=DJANGO_SECRET_KEY="$(rnd 50)" \
  --from-literal=POSTGRES_PASSWORD="$(rnd 24)" \
  --from-literal=VTON_API_KEY="$APIKEY" \
  --from-literal=DJANGO_SUPERUSER_USERNAME=admin \
  --from-literal=DJANGO_SUPERUSER_PASSWORD="$ADMINPW"
echo "Contraseña inicial de /admin (guárdala): $ADMINPW"
