# 1. PRÉ-REQUISITOS
# Certifique-se de ter instalado:
 - Kubernetes
 - Helm
 - metrics-server

# 2. CLONAR REPOSITÓRIO
git clone https://github.com/manoelpg/steam.git
cd steam/master

# 3. INSTALAR O PROJETO
helm install steam ./helm-chart \
  --set image.repository=manoelpg/steam \
  --set image.tag=latest \
  --set service.type=LoadBalancer

# 4. INSTALAR METRICS-SERVER (para coleta de métricas) ! opcional.
helm upgrade --install metrics-server metrics-server \
  --repo https://kubernetes-sigs.github.io/metrics-server/ \
  --namespace kube-system \
  --set args={--kubelet-insecure-tls}

# 5. VERIFICAR INSTALAÇÃO
kubectl get pods,svc -l app=steam

# 6. CRIAR JOB DE TESTE DE CARGA
make start-producer ou stop-producer

# 7. MONITORAR AUTOSCALING (em outro terminal)
watch -n 2 "kubectl get hpa steam-autoscaler && kubectl get pods"

# 8. DEMONSTRAÇÃO PASSO-A-PASSO:
 - Mostrar pods iniciais (1 réplica)
 - Mostrar HPA status inicial
 - Iniciar o job de carga
 - Mostrar aumento gradual de CPU
 - Mostrar escalonamento para até 5 pods
 - Parar o job após demonstração:
kubectl delete job load-test

# 9. MOSTRAR ESCALONAMENTO PARA BAIXO
- Após término da carga, mostrar redução gradual de pods
- Leva alguns minutos para normalizar

# 10. EXTRA: Verificar eventos do HPA
kubectl describe hpa steam-autoscaler