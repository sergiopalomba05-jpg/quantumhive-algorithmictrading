# guardrail_terminal.ps1 — CEPO DE SEGURIDAD QUANTUMHIVE
# Bloquea comandos destructivos: git clone, git clean, Remove-Item -Recurse -Force, rm -rf, del
# Solo Sergio (Nivel 0) puede desbloquear con una clave secreta.
# Cargar al inicio de cada sesión: . .\automatizacion\utils\guardrail_terminal.ps1

$global:QH_BLOQUEADO = $true

$QH_SECRETO = $env:QH_GUARDRAIL_KEY
if (-not $QH_SECRETO) {
    Write-Host "[GUARDRAIL] ⚠️  Variable QH_GUARDRAIL_KEY no detectada. Usando clave por defecto." -ForegroundColor Yellow
    $QH_SECRETO = "QUANTUMHIVE_SHIELD_2026"
}

function Test-QHKey {
    param([string]$Key)
    return ($Key -eq $QH_SECRETO)
}

function Unlock-QHGuardrail {
    param([string]$Key)
    if (Test-QHKey -Key $Key) {
        $global:QH_BLOQUEADO = $false
        Write-Host "[GUARDRAIL] 🟢 CEPO DESACTIVADO para esta sesión." -ForegroundColor Green
    } else {
        Write-Host "[GUARDRAIL] 🔴 CLAVE INCORRECTA. Operación bloqueada." -ForegroundColor Red
    }
}

function Lock-QHGuardrail {
    $global:QH_BLOQUEADO = $true
    Write-Host "[GUARDRAIL] 🔒 CEPO REACTIVADO." -ForegroundColor Yellow
}

# ── Interceptar Remove-Item (y por tanto del / rm -rf) ──

function Remove-Item {
    [CmdletBinding(SupportsShouldProcess=$true, ConfirmImpact='High')]
    param(
        [Parameter(ValueFromPipeline=$true, ValueFromPipelineByPropertyName=$true)]
        [string[]]$Path,
        [switch]$Recurse,
        [switch]$Force,
        [switch]$LiteralPath,
        [Parameter(ParameterSetName='LiteralPath')]
        [string]$LiteralPathValue,
        [switch]$Confirm,
        [switch]$WhatIf
    )
    
    $effectivePath = if ($PSBoundParameters.ContainsKey('LiteralPath')) { $LiteralPathValue } else { $Path }
    
    if ($global:QH_BLOQUEADO -and $Recurse -and $Force) {
        Write-Host "[GUARDRAIL] 🔴 BLOQUEADO: Remove-Item -Recurse -Force no está permitido sin autorización." -ForegroundColor Red
        Write-Host "[GUARDRAIL] Para desbloquear: Unlock-QHGuardrail -Key 'TU_CLAVE'" -ForegroundColor Yellow
        return
    }
    
    if ($global:QH_BLOQUEADO -and $Recurse) {
        Write-Host "[GUARDRAIL] 🔴 BLOQUEADO: Remove-Item con -Recurse requiere autorización." -ForegroundColor Red
        return
    }
    
    Microsoft.PowerShell.Management\Remove-Item @PSBoundParameters
}

# ── Interceptar git clone y git clean ──

function git {
    param(
        [Parameter(ValueFromRemainingArguments=$true)]
        $ArgumentList
    )
    
    $argsStr = "$ArgumentList".ToLower()
    
    if ($global:QH_BLOQUEADO -and ($argsStr -match "clone" -or $argsStr -match "clean")) {
        Write-Host "[GUARDRAIL] 🔴 BLOQUEADO: 'git $ArgumentList' no está permitido." -ForegroundColor Red
        Write-Host "[GUARDRAIL] Puede sobrescribir archivos no trackeados." -ForegroundColor Red
        Write-Host "[GUARDRAIL] Para desbloquear: Unlock-QHGuardrail -Key 'TU_CLAVE'" -ForegroundColor Yellow
        return
    }
    
    & "C:\Program Files\Git\cmd\git.exe" @ArgumentList
}

# ── Interceptar del (alias) ──
Remove-Item Alias:del -ErrorAction SilentlyContinue
Set-Alias del Remove-Item

# ── Interceptar rm (si está como alias) ──
Remove-Item Alias:rm -ErrorAction SilentlyContinue
Set-Alias rm Remove-Item

Write-Host "[GUARDRAIL] 🛡️  CEPO DE SEGURIDAD ACTIVO" -ForegroundColor Cyan
Write-Host "[GUARDRAIL] Comandos bloqueados: git clone, git clean, Remove-Item -Recurse -Force, del -Recurse -Force" -ForegroundColor Cyan
Write-Host "[GUARDRAIL] Para desbloquear: Unlock-QHGuardrail -Key 'TU_CLAVE'" -ForegroundColor Yellow
Write-Host "[GUARDRAIL] Para bloquear de nuevo: Lock-QHGuardrail" -ForegroundColor Yellow
