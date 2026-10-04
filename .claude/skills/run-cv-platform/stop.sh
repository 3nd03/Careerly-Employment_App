#!/usr/bin/env bash
# Stop whatever uvicorn / vite process is listening on :8000 / :5173.
# Killing the npm wrapper is not enough on Windows - the vite node process keeps the port.
powershell.exe -NoProfile -Command '
  foreach ($port in 8000, 5173) {
    $conns = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($procId in ($conns.OwningProcess | Sort-Object -Unique)) {
      $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$procId").CommandLine
      if ($cmd -match "uvicorn|vite") { Stop-Process -Id $procId -Force; "stopped :$port (pid $procId)" }
      else { "left :$port alone (pid $procId is not uvicorn/vite)" }
    }
  }'
