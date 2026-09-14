# MySQL Database

This directory contains the Kubernetes configuration for the MySQL database used by the FoodHub three-tier application.

## Files

- storageclass.yaml - Local storage class for MySQL
- mysql-pv.yaml - Persistent Volume
- mysql-pvc.yaml - Persistent Volume Claim
- mysql.yaml - MySQL Service and StatefulSet
- mysql-secret.example.yaml - Example Secret configuration

## Create the MySQL Secret

The real MySQL Secret is intentionally NOT stored in GitHub.

Create it manually:

    kubectl create secret generic mysql-secret --from-literal=MYSQL_DATABASE=three_tier_db --from-literal=MYSQL_USER=YOUR_DB_USER --from-literal=MYSQL_PASSWORD=YOUR_DB_PASSWORD --from-literal=MYSQL_ROOT_PASSWORD=YOUR_ROOT_PASSWORD

## Deploy

Apply the resources in this order:

    kubectl apply -f database/storageclass.yaml
    kubectl apply -f database/mysql-pv.yaml
    kubectl apply -f database/mysql-pvc.yaml
    kubectl apply -f database/mysql.yaml

## Check MySQL

    kubectl get pods -l app=mysql
    kubectl get pvc mysql-pvc
    kubectl get pv mysql-pv

MySQL is available internally to the Flask backend at:

    mysql-service:3306

Do not commit real passwords or Kubernetes Secret manifests containing real credentials.
