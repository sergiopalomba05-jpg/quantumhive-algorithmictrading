# Instalar plugin SQLite en Grafana
$grafanaPath = "C:\Program Files\GrafanaLabs\grafana\bin"

Write-Host "Instalando plugin SQLite..." -ForegroundColor Yellow
& "$grafanaPath\grafana-cli.exe" plugins install frser-sqlite-datasource

Write-Host "Reiniciando Grafana..." -ForegroundColor Yellow
Restart-Service -Name "Grafana"

Write-Host "Plugin SQLite instalado correctamente" -ForegroundColor Green