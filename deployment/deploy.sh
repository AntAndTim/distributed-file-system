kubectl apply -f redis_deployment.yml
sleep 5
kubectl apply -f naming_deployment.yml
sleep 7
kubectl apply -f file_server_deployment.yml