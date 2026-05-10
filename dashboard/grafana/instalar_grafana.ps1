# Script de instalación Grafana para QuantumHive
# Ejecutar en PowerShell como Administrador

Write-Host "Instalando Grafana para QuantumHive..." -ForegroundColor Green

# Descargar Grafana OSS (versión estable)
$url = "https://dl.grafana.com/oss/release/grafana-11.0.0.windows-amd64.msi"
$output = "$env:TEMP\grafana-installer.msi"

Write-Host "Descargando Grafana..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $url -OutFile $output

# Instalar silenciosamente
Write-Host "Instalando..." -ForegroundColor Yellow
Start-Process msiexec.exe -Wait -ArgumentList "/i $output /quiet"

Write-Host "Grafana instalado en C:\Program Files\GrafanaLabs\grafana\" -ForegroundColor Green
Write-Host "Iniciando servicio..." -ForegroundColor Yellow

# Iniciar servicio
Start-Service -Name "Grafana"

Write-Host "Grafana corriendo en http://localhost:3000" -ForegroundColor Green
Write-Host "Usuario: admin | Password: admin (cambiar en primer login)" -ForegroundColor Cyan