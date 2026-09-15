# 🍔 FoodHub - Three-Tier Food Ordering Application

FoodHub is a three-tier food ordering web application deployed on
AWS EC2 using Kubernetes.

The project demonstrates how a frontend, backend, and database can
be containerized and deployed using Docker and Kubernetes.

---

## 🚀 Project Overview

FoodHub allows users to:

- View available food items
- Search and filter food
- Add food items to cart
- Place orders
- View order information
- Contact the application through messages

The project also includes an Admin Dashboard for managing:

- Food items
- Orders
- Users
- Messages
- Notifications
- Application statistics

---

## 🏗️ Architecture

```text
                         USER
                           |
                           v
                    AWS EC2 INSTANCE
                           |
                           v
                    Kubernetes Cluster
                           |
                    +------+------+
                    |             |
                    v             v
               NGINX :30080
               FRONTEND
                    |
                    | HTTP API
                    v
          Flask Backend :30050
                    |
                    v
             MySQL :3306
                    |
                    v
          Persistent Storage
             MySQL PV/PVC

