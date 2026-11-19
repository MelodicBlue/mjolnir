# Mjolnir: install or remove the daily automatic run on Windows (Task Scheduler).
# Usage (PowerShell, from the repo folder):
#   powershell -ExecutionPolicy Bypass -File scripts\schedule-windows.ps1 install [-Time 10:00]
#   powershell -ExecutionPolicy Bypass -File scripts\schedule-windows.ps1 status
#   powershell -ExecutionPolicy Bypass -File scripts\schedule-windows.ps1 run-now
#   powershell -ExecutionPolicy Bypass -File scripts\schedule-windows.ps1 uninstall
#
# Each run: sources fresh postings, ranks them, tailors and submits up to
# run.max_applications_per_run applications in Edge, logs everything, closes its tabs.
# The laptop must be on (or waking from sleep) with Edge open and the Claude extension connected.
# A run missed because the laptop was off starts as soon as it is back on.

param(
  [Parameter(Position = 0)][ValidateSet('install', 'uninstall', 'status', 'run-now')][string]$Action = 'status',
  [string]$Time = '10:00'
)

$ErrorActionPreference = 'Stop'
$Repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$TaskName = 'Mjolnir daily applications'

function Find-Bash {
  foreach ($p in @("$env:ProgramFiles\Git\bin\bash.exe", "${env:ProgramFiles(x86)}\Git\bin\bash.exe", "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe")) {
    if (Test-Path $p) { return $p }
  }
  throw 'Git Bash not found. Install it with: winget install --id Git.Git -e'
}

function Ensure-Python3 {
  # run.sh and the sweep scripts call python3; the python.org installer only ships python.exe.
  $py = Get-Command python.exe -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1
  if (-not $py) { throw 'Python not found. Install it with: winget install --id Python.Python.3.12 -e' }
  $py3 = Join-Path (Split-Path $py.Source) 'python3.exe'
  if (-not (Test-Path $py3)) { Copy-Item $py.Source $py3; Write-Host "Created $py3" }
}

switch ($Action) {
  'install' {
    $bash = Find-Bash
    Ensure-Python3
    New-Item -ItemType Directory -Force -Path (Join-Path $Repo 'logs') | Out-Null
    $repoUnix = $Repo -replace '\\', '/'
    $cmd = "cd '$repoUnix' && ./run.sh >> logs/scheduled-runs.log 2>&1"
    $action = New-ScheduledTaskAction -Execute $bash -Argument "-lc `"$cmd`"" -WorkingDirectory $Repo
    $trigger = New-ScheduledTaskTrigger -Daily -At $Time
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries `
      -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 4) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
      -Description 'Mjolnir: source, rank, tailor and submit design applications' -Force | Out-Null
    Write-Host "Installed: '$TaskName' runs daily at $Time (local time). Missed runs start when the laptop is next on."
    Write-Host "Log: $Repo\logs\scheduled-runs.log"
  }
  'uninstall' {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Removed '$TaskName'."
  }
  'run-now' {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Started '$TaskName'. Watch $Repo\logs\scheduled-runs.log"
  }
  'status' {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $t) { Write-Host 'Not installed.'; break }
    $i = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Host "State: $($t.State)  Last run: $($i.LastRunTime)  Result: $($i.LastTaskResult)  Next run: $($i.NextRunTime)"
  }
}
