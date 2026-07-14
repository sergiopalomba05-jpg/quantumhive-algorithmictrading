# setup_ollama_windows.ps1
# Script de instalación rápida de Ollama + modelo Llama 3.3 para QuantumHive
# Ejecutar en PowerShell como Administrador: .\scripts\setup_ollama_windows.ps1

$ErrorActionPreference = "Stop"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QuantumHive — Setup Ollama (Local LLM)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Detectar Ollama
$ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaPath) {
    Write-Host "[OK] Ollama ya instalado: $($ollamaPath.Source)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Ollama no detectado. Descargando..." -ForegroundColor Yellow
    $url = "https://ollama.com/download/OllamaSetup.exe"
    $out = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri $url -OutFile $out
    Write-Host "[INFO] Instalando Ollama (aceptar UAC)..." -ForegroundColor Yellow
    Start-Process -FilePath $out -Wait
    Remove-Item $out
    Write-Host "[OK] Ollama instalado. Reiniciá PowerShell y volvé a correr." -ForegroundColor Green
    exit
}

# 2. Verificar servicio corriendo
try {
    $res = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
    Write-Host "[OK] Servicio Ollama corriendo en localhost:11434" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Ollama no responde. ¿Está corriendo? Iniciá Ollama desde el menú inicio." -ForegroundColor Yellow
}

# 3. Descargar modelo recomendado
Write-Host "[INFO] Descargando Llama 3.3 (4.9GB aprox, puede tardar)..." -ForegroundColor Cyan
ollama pull llama3.3
Write-Host "[OK] Modelo Llama 3.3 listo." -ForegroundColor Green

# 4. Test rápido
Write-Host "[INFO] Test de inferencia rápido..." -ForegroundColor Cyan
$body = '{"model":"llama3.3","prompt":"Responde solo: Ollama listo para QuantumHive","stream":false}' | ConvertTo-Json -Compress
$response = Invoke-WebRequest -Uri "http://localhost:11434/api/generate" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
$json = $response.Content | ConvertFrom-Json
Write-Host "[TEST] Respuesta: $($json.response.Trim())" -ForegroundColor Green

Write-Host "" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OLLAMA LISTO PARA QUANTUMHIVE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Modelo: llama3.3 (localhost:11434)" -ForegroundColor White
Write-Host "  Uso:  python automatizacion/agentes/division_bi/agente_orquestador_llm.py diagnostico" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
