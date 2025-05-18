#! /usr/bin/env bash

set -e

echo start
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version 4.8.2 -f nginx.values.yaml
kubectl apply -f additional-objects/*
echo done fuck you
