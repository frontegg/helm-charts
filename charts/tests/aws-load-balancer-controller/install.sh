#!/usr/bin/env/bash

set -e

echo start
helm repo add eks https://aws.github.io/eks-charts
helm repo update
helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller --version 1.12 --namespace load-balancer --create-namespace -f aws-load-balancer-controller.yaml
echo done
