#!/bin/bash
set -e

ollama serve &

# Aguarda o Ollama estar disponível
until curl -s http://localhost:11434 > /dev/null; do
  echo "[INFO] Esperando o Ollama iniciar..."
  sleep 1
done

# Baixa o modelo
ollama pull gemma3:1b

# Mantém processo em foreground
wait
