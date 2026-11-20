<#
.SYNOPSIS
User-operated launcher for the frozen 12-cell SF1 benchmark.
.DESCRIPTION
Default is a read-only DryRun. Only -Action Run starts the formal benchmark.
Run stays in the foreground of YOUR PowerShell, outside a Codex tool session.
Press Ctrl+C ONCE and wait for Python to exit before attempting recovery.
Progress reads completed artifacts once; it never opens the live journal.
Recover validates ownership and archives the pre-recovery journal first.
#>
[CmdletBinding()]
param(
    [ValidateSet('DryRun', 'Run', 'Progress', 'RecoverPreview', 'Recover')]
    [string]$Action = 'DryRun'
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskPlan = Join-Path $taskRoot 'benchmark\results\3c-single-round-v1\plan.json'
$taskRunId = '9e13de9e0e1a'
$taskPlanHash = 'a2966405ec34bb28dc01d7e45ff8484598d56245d876214a166bc391e9dc102d'
$taskRunDir = Join-Path $taskRoot 'benchmark\results\strategy-run-9e13de9e0e1a-single'
$taskLogDir = Join-Path $taskRoot 'benchmark\results\strategy-logs-9e13de9e0e1a-single'

function Invoke-CheckedPython {
    param([string[]]$PythonArguments)
    & $taskPython @PythonArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python stopped with exit code $LASTEXITCODE. Do not automatically retry the benchmark."
    }
}

Push-Location -LiteralPath $taskRoot
try {
    $taskPlanDocument = Get-Content -LiteralPath $taskPlan -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($taskPlanDocument.run_id -ne $taskRunId -or $taskPlanDocument.plan_sha256 -ne $taskPlanHash) {
        throw 'Reviewed plan identity mismatch. No experiment will be started.'
    }
    switch ($Action) {
        'DryRun' {
            $taskStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
            $taskSuffix = [Guid]::NewGuid().ToString('N').Substring(0, 8)
            $taskOutput = Join-Path (Split-Path -Parent $taskPlan) "dry-run-local-$taskStamp-$taskSuffix.json"
            Invoke-CheckedPython -PythonArguments @('-B', '-m', 'strategy_benchmark', 'dry-run',
                '--plan', $taskPlan, '--output', $taskOutput)
            Write-Host "Read-only dry-run saved to $taskOutput"
        }
        'Run' {
            if ((Test-Path -LiteralPath $taskRunDir) -or (Test-Path -LiteralPath $taskLogDir)) {
                throw 'Run or log directory already exists. Preserve it; do not overwrite or resume with this launcher.'
            }
            New-Item -ItemType Directory -Path $taskLogDir | Out-Null
            $taskStdout = Join-Path $taskLogDir 'stdout.log'
            $taskStderr = Join-Path $taskLogDir 'stderr.log'
            Write-Host "Target: advisor_benchmark; 12 cells; warmup=2; repeats=5"
            Write-Host "Run: $taskRunDir"
            Write-Host "Logs: $taskLogDir"
            Write-Host 'Foreground execution. Ctrl+C once, then wait for cleanup. Use another PowerShell for Progress.'
            $taskPreviousPreference = $ErrorActionPreference
            try {
                # Windows PowerShell 5.1 can wrap redirected native stderr as
                # error records. Let Python finish its own cleanup before exit.
                $ErrorActionPreference = 'Continue'
                & $taskPython -u -B -m strategy_benchmark run --plan $taskPlan --run-dir $taskRunDir --approve-plan-sha256 $taskPlanHash 1> $taskStdout 2> $taskStderr
                $taskExitCode = $LASTEXITCODE
            }
            finally {
                $ErrorActionPreference = $taskPreviousPreference
            }
            Write-Host "Python exit code: $taskExitCode"
            Write-Host "Inspect stdout.log, stderr.log and the saved artifacts. No automatic rerun or recovery."
            if ($taskExitCode -ne 0) {
                throw 'Benchmark stopped. After the process exits, use RecoverPreview before Recover.'
            }
        }
        'Progress' {
            Invoke-CheckedPython -PythonArguments @('-B', '-m', 'analysis.strategy_progress', '--run-dir', $taskRunDir)
        }
        'RecoverPreview' {
            Invoke-CheckedPython -PythonArguments @('-B', '-m', 'strategy_benchmark', 'recover', '--run-dir', $taskRunDir)
        }
        'Recover' {
            $taskJournal = Join-Path $taskRunDir 'journal.json'
            $taskArchive = Join-Path $taskRunDir ('journal.before-recovery.' + [Guid]::NewGuid().ToString('N') + '.json')
            [System.IO.File]::Copy($taskJournal, $taskArchive, $false)
            Write-Host "Pre-recovery journal preserved: $taskArchive"
            Invoke-CheckedPython -PythonArguments @('-B', '-m', 'strategy_benchmark', 'recover',
                '--run-dir', $taskRunDir, '--execute', '--approve-run-id', $taskRunId)
        }
    }
}
finally {
    Pop-Location
}
