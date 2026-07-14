# shadow_backup.ps1 — Backup automático QuantumHive
# Corre cada hora: copia el proyecto completo a D:/QH_BACKUP_SISTEMA/ o al pendrive
# Se ejecuta en segundo plano, no debe desactivarse sin orden de Sergio (Nivel 0)

param(
    [switch]$Daemon  # Modo demonio: corre cada hora hasta que se mate el proceso
)

$ORIGEN = "C:\Users\sergio\QUANTUMHIVE_ALGORITHMICTRADING"
$FECHA = Get-Date -Format "yyyy-MM-dd_HHmmss"
$LOG = "$ORIGEN\logs\shadow_backup.log"

# Intentar D: primero, luego pendrive, luego fallback a usuario
$DESTINO_BASE = $null
$candidatos = @(
    "D:\QH_BACKUP_SISTEMA",
    "E:\QH_BACKUP_SISTEMA",
    "F:\QH_BACKUP_SISTEMA",
    "$env:USERPROFILE\QH_BACKUP_SISTEMA"
)
foreach ($c in $candidatos) {
    $parent = Split-Path $c -Parent
    if (Test-Path $parent) {
        $DESTINO_BASE = $c
        break
    }
}
if (-not $DESTINO_BASE) {
    $DESTINO_BASE = "$env:USERPROFILE\QH_BACKUP_SISTEMA"
}

$DESTINO = "$DESTINO_BASE\$FECHA"

function Write-Log {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -Path $LOG -Value $line -ErrorAction SilentlyContinue
}

function Do-Backup {
    if (-not (Test-Path $DESTINO_BASE)) {
        New-Item -ItemType Directory -Path $DESTINO_BASE -Force | Out-Null
    }
    New-Item -ItemType Directory -Path $DESTINO -Force | Out-Null

    Write-Log "Iniciando backup → $DESTINO"

    # Excluir node_modules, .git, __pycache__
    $exclude = @('node_modules', '.git', '__pycache__', '.venv', 'venv')

    try {
        Copy-Item -Path "$ORIGEN\*" -Destination $DESTINO -Recurse -Force -ErrorAction SilentlyContinue `
            -Exclude $exclude

        # Verificar
        $count = (Get-ChildItem $DESTINO -Recurse -File -ErrorAction SilentlyContinue).Count
        $size = "{0:N2}" -f ((Get-ChildItem $DESTINO -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB)
        Write-Log "Backup COMPLETO: $count archivos, ${size}MB"
    } catch {
        Write-Log "ERROR en backup: $_"
    }

    # Limpiar backups viejos (>7 días)
    $limite = (Get-Date).AddDays(-7)
    Get-ChildItem $DESTINO_BASE -Directory | Where-Object { $_.CreationTime -lt $limite } | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Log "Backup viejo eliminado: $($_.Name)"
    }

    Write-Log "Backup finalizado."
}

# ── Ejecutar inmediatamente ──
Do-Backup

# ── Modo demonio: loop cada hora ──
if ($Daemon) {
    Write-Log "MODO DAEMON: backup cada 1 hora. PID: $pid"
    while ($true) {
        Start-Sleep -Seconds 3600
        Do-Backup
    }
}
