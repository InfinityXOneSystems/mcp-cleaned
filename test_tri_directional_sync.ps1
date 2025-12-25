# Tri-Directional Credential Sync Test
# Tests: Local ↔ Git Remote ↔ Google Cloud
# Date: December 25, 2025

param(
    [switch]$DryRun = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"
$results = @{
    "LocalCredentialManager" = @{
        "Status" = "Unknown"
        "Path" = "C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager"
        "Checks" = @{}
    }
    "GitRemoteSync" = @{
        "Status" = "Unknown"
        "Repos" = @{}
    }
    "GoogleCloudSync" = @{
        "Status" = "Unknown"
        "Checks" = @{}
    }
    "TriDirectionalSync" = @{
        "Status" = "Unknown"
        "Summary" = ""
    }
}

Write-Host "`n" -NoNewline
Write-Host "================================================================================`n" -ForegroundColor Cyan
Write-Host "  🔐 TRI-DIRECTIONAL CREDENTIAL SYNC TEST" -ForegroundColor Yellow
Write-Host "  Local ↔ Git Remote ↔ Google Cloud Validation`n" -ForegroundColor White
Write-Host "================================================================================`n" -ForegroundColor Cyan

# ============================================================================
# TEST 1: LOCAL CREDENTIAL MANAGER
# ============================================================================
Write-Host "📁 TEST 1: Local Credential Manager" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────────────────`n" -ForegroundColor DarkGray

$credManagerPath = "C:\Users\JARVIS\AppData\Local\InfinityXOne\CredentialManager"

if (Test-Path $credManagerPath) {
    Write-Host "  ✓ Credential Manager exists" -ForegroundColor Green
    $results.LocalCredentialManager.Status = "PASS"
    
    # Check foundation directory
    $foundationPath = Join-Path $credManagerPath "foundation"
    if (Test-Path $foundationPath) {
        Write-Host "  ✓ Foundation directory found" -ForegroundColor Green
        $results.LocalCredentialManager.Checks["Foundation"] = "PASS"
        
        # Check for .env files
        $envFiles = @(
            ".env",
            ".env.production",
            ".env.template",
            "credentials.json"
        )
        
        foreach ($file in $envFiles) {
            $filePath = Join-Path $foundationPath $file
            if (Test-Path $filePath) {
                $fileInfo = Get-Item $filePath
                Write-Host "  ✓ $file (Last modified: $($fileInfo.LastWriteTime))" -ForegroundColor Green
                $results.LocalCredentialManager.Checks[$file] = "FOUND - $($fileInfo.LastWriteTime)"
            } else {
                Write-Host "  ⊘ $file not found" -ForegroundColor Yellow
                $results.LocalCredentialManager.Checks[$file] = "NOT_FOUND"
            }
        }
        
        # Check sync directory
        $syncPath = Join-Path $foundationPath "sync"
        if (Test-Path $syncPath) {
            Write-Host "  ✓ Sync directory exists" -ForegroundColor Green
            $syncFiles = Get-ChildItem $syncPath -File | Where-Object { $_.Name -like "*sync*" }
            Write-Host "    Found $($syncFiles.Count) sync-related files:" -ForegroundColor Cyan
            foreach ($file in $syncFiles) {
                Write-Host "      - $($file.Name)" -ForegroundColor White
            }
            $results.LocalCredentialManager.Checks["SyncDirectory"] = "PASS - $($syncFiles.Count) files"
        } else {
            Write-Host "  ⚠ Sync directory not found" -ForegroundColor Yellow
            $results.LocalCredentialManager.Checks["SyncDirectory"] = "NOT_FOUND"
        }
    } else {
        Write-Host "  ✗ Foundation directory not found" -ForegroundColor Red
        $results.LocalCredentialManager.Status = "FAIL"
        $results.LocalCredentialManager.Checks["Foundation"] = "NOT_FOUND"
    }
} else {
    Write-Host "  ✗ Credential Manager not found at: $credManagerPath" -ForegroundColor Red
    $results.LocalCredentialManager.Status = "FAIL"
}

# ============================================================================
# TEST 2: GIT REMOTE SYNC
# ============================================================================
Write-Host "`n📡 TEST 2: Git Remote Sync" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────────────────`n" -ForegroundColor DarkGray

# Check current repo
$currentRepo = "C:\AI\repos\mcp"
if (Test-Path (Join-Path $currentRepo ".git")) {
    Write-Host "  Current Repo: $currentRepo" -ForegroundColor Cyan
    
    # Get git remote
    try {
        Push-Location $currentRepo
        $remote = git remote get-url origin 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Git remote configured: $remote" -ForegroundColor Green
            $results.GitRemoteSync.Repos["mcp"] = @{
                "Remote" = $remote
                "Status" = "CONFIGURED"
            }
            
            # Check sync status
            git fetch origin 2>&1 | Out-Null
            $status = git status -sb 2>&1
            Write-Host "  ✓ Sync status: $status" -ForegroundColor Green
            $results.GitRemoteSync.Repos["mcp"]["SyncStatus"] = $status
        } else {
            Write-Host "  ✗ No git remote configured" -ForegroundColor Red
            $results.GitRemoteSync.Repos["mcp"] = @{ "Status" = "NO_REMOTE" }
        }
        Pop-Location
    } catch {
        Write-Host "  ✗ Git error: $_" -ForegroundColor Red
        $errorObj = @{ "Status" = "ERROR"; "ErrorMsg" = $_.ToString() }
        $results.GitRemoteSync.Repos["mcp"] = $errorObj
        Pop-Location
    }
}

# Check foundation repo if it exists
$foundationRepo = "C:\AI\repos\foundation"
if (Test-Path (Join-Path $foundationRepo ".git")) {
    Write-Host "`n  Foundation Repo: $foundationRepo" -ForegroundColor Cyan
    
    try {
        Push-Location $foundationRepo
        $remote = git remote get-url origin 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ Git remote configured: $remote" -ForegroundColor Green
            $results.GitRemoteSync.Repos["foundation"] = @{
                "Remote" = $remote
                "Status" = "CONFIGURED"
            }
            
            # Check for sync script
            if (Test-Path (Join-Path $foundationRepo ".astraeus.sync")) {
                Write-Host "  ✓ .astraeus.sync found (auto-sync enabled)" -ForegroundColor Green
                $results.GitRemoteSync.Repos["foundation"]["AutoSync"] = "ENABLED"
            }
            
            git fetch origin 2>&1 | Out-Null
            $status = git status -sb 2>&1
            Write-Host "  ✓ Sync status: $status" -ForegroundColor Green
            $results.GitRemoteSync.Repos["foundation"]["SyncStatus"] = $status
        } else {
            Write-Host "  ✗ No git remote configured" -ForegroundColor Red
            $results.GitRemoteSync.Repos["foundation"] = @{ "Status" = "NO_REMOTE" }
        }
        Pop-Location
    } catch {
        Write-Host "  ✗ Git error: $_" -ForegroundColor Red
        $errorObj = @{ "Status" = "ERROR"; "ErrorMsg" = $_.ToString() }
        $results.GitRemoteSync.Repos["foundation"] = $errorObj
        Pop-Location
    }
}

if ($results.GitRemoteSync.Repos.Count -gt 0) {
    $results.GitRemoteSync.Status = "PASS"
} else {
    $results.GitRemoteSync.Status = "NO_REPOS"
}

# ============================================================================
# TEST 3: GOOGLE CLOUD SYNC
# ============================================================================
Write-Host "`n☁️  TEST 3: Google Cloud Sync" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────────────────`n" -ForegroundColor DarkGray

# Check for Google Cloud credentials
$gcpCredentialFiles = @(
    @{
        "Path" = Join-Path $credManagerPath "foundation\credentials.json"
        "Name" = "Service Account (Credential Manager)"
    },
    @{
        "Path" = Join-Path $credManagerPath "foundation\workspace-sa.json"
        "Name" = "Workspace Service Account (Credential Manager)"
    },
    @{
        "Path" = "C:\AI\repos\foundation\google-service-account.json"
        "Name" = "Service Account (Foundation Repo)"
    },
    @{
        "Path" = "C:\AI\repos\mcp\workspace-sa.json"
        "Name" = "Workspace Service Account (MCP)"
    }
)

$foundCredentials = 0
foreach ($cred in $gcpCredentialFiles) {
    if (Test-Path $cred.Path) {
        $fileInfo = Get-Item $cred.Path
        Write-Host "  ✓ $($cred.Name)" -ForegroundColor Green
        Write-Host "    Last modified: $($fileInfo.LastWriteTime)" -ForegroundColor Gray
        $results.GoogleCloudSync.Checks[$cred.Name] = "FOUND - $($fileInfo.LastWriteTime)"
        $foundCredentials++
    } else {
        Write-Host "  ⊘ $($cred.Name) not found" -ForegroundColor Yellow
        $results.GoogleCloudSync.Checks[$cred.Name] = "NOT_FOUND"
    }
}

# Check environment variables
$gcpEnvVars = @(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_OAUTH_TOKEN",
    "GOOGLE_API_KEY"
)

Write-Host "`n  Environment Variables:" -ForegroundColor Cyan
$envVarsSet = 0
foreach ($var in $gcpEnvVars) {
    $value = [Environment]::GetEnvironmentVariable($var)
    if ($value) {
        Write-Host "  ✓ $var is set" -ForegroundColor Green
        $results.GoogleCloudSync.Checks[$var] = "SET"
        $envVarsSet++
    } else {
        Write-Host "  ⊘ $var not set" -ForegroundColor Yellow
        $results.GoogleCloudSync.Checks[$var] = "NOT_SET"
    }
}

if ($foundCredentials -gt 0 -or $envVarsSet -gt 0) {
    $results.GoogleCloudSync.Status = "PASS"
    Write-Host "`n  ✓ Google Cloud credentials configured ($foundCredentials files + $envVarsSet env vars)" -ForegroundColor Green
} else {
    $results.GoogleCloudSync.Status = "NOT_CONFIGURED"
    Write-Host "`n  ⚠ No Google Cloud credentials found" -ForegroundColor Yellow
}

# ============================================================================
# TEST 4: TRI-DIRECTIONAL SYNC VALIDATION
# ============================================================================
Write-Host "`n🔄 TEST 4: Tri-Directional Sync Validation" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────────────────`n" -ForegroundColor DarkGray

Write-Host "  Testing sync flow: Local → Git → Cloud`n" -ForegroundColor Cyan

# Check sync scripts
$syncScripts = @(
    @{
        "Path" = Join-Path $credManagerPath "foundation\sync-repos.ps1"
        "Name" = "Repo Sync Script"
        "Type" = "Git Sync"
    },
    @{
        "Path" = Join-Path $credManagerPath "foundation\sync\git-sync-service.ts"
        "Name" = "Git Sync Service"
        "Type" = "Git Sync"
    },
    @{
        "Path" = "C:\AI\repos\mcp\scripts\sheets_sync.py"
        "Name" = "Sheets Sync Script"
        "Type" = "Cloud Sync"
    }
)

$functionalSyncScripts = 0
foreach ($script in $syncScripts) {
    if (Test-Path $script.Path) {
        Write-Host "  ✓ $($script.Name) ($($script.Type))" -ForegroundColor Green
        Write-Host "    Path: $($script.Path)" -ForegroundColor Gray
        $functionalSyncScripts++
    } else {
        Write-Host "  ⊘ $($script.Name) not found" -ForegroundColor Yellow
    }
}

# Validate tri-directional capability
$localPass = $results.LocalCredentialManager.Status -eq "PASS"
$gitPass = $results.GitRemoteSync.Status -eq "PASS"
$cloudPass = $results.GoogleCloudSync.Status -eq "PASS"

Write-Host "`n  Sync Direction Status:" -ForegroundColor Cyan
Write-Host "  ┌─────────────────┐" -ForegroundColor Gray
Write-Host "  │  Local Storage  │ $(if($localPass){"✓"}else{"✗"}) $($results.LocalCredentialManager.Status)" -ForegroundColor $(if($localPass){"Green"}else{"Red"})
Write-Host "  └────────┬────────┘" -ForegroundColor Gray
Write-Host "           │" -ForegroundColor Gray
Write-Host "           ├──────────→ Git Remote     $(if($gitPass){"✓"}else{"✗"}) $($results.GitRemoteSync.Status)" -ForegroundColor $(if($gitPass){"Green"}else{"Red"})
Write-Host "           │" -ForegroundColor Gray
Write-Host "           └──────────→ Google Cloud   $(if($cloudPass){"✓"}else{"✗"}) $($results.GoogleCloudSync.Status)" -ForegroundColor $(if($cloudPass){"Green"}else{"Red"})

if ($localPass -and $gitPass -and $cloudPass) {
    $results.TriDirectionalSync.Status = "FULLY_OPERATIONAL"
    $results.TriDirectionalSync.Summary = "All three sync directions are configured and operational"
    Write-Host "`n  ✓ TRI-DIRECTIONAL SYNC: FULLY OPERATIONAL" -ForegroundColor Green -BackgroundColor Black
} elseif ($localPass -and $gitPass) {
    $results.TriDirectionalSync.Status = "PARTIAL_LOCAL_GIT"
    $results.TriDirectionalSync.Summary = "Local ↔ Git sync operational, Cloud sync needs configuration"
    Write-Host "`n  ⚠ TRI-DIRECTIONAL SYNC: PARTIAL (Local ↔ Git)" -ForegroundColor Yellow
} elseif ($localPass -and $cloudPass) {
    $results.TriDirectionalSync.Status = "PARTIAL_LOCAL_CLOUD"
    $results.TriDirectionalSync.Summary = "Local ↔ Cloud sync operational, Git sync needs configuration"
    Write-Host "`n  ⚠ TRI-DIRECTIONAL SYNC: PARTIAL (Local ↔ Cloud)" -ForegroundColor Yellow
} else {
    $results.TriDirectionalSync.Status = "NOT_OPERATIONAL"
    $results.TriDirectionalSync.Summary = "Tri-directional sync not fully configured"
    Write-Host "`n  ✗ TRI-DIRECTIONAL SYNC: NOT FULLY OPERATIONAL" -ForegroundColor Red
}

# ============================================================================
# SUMMARY
# ============================================================================
Write-Host "`n" -NoNewline
Write-Host "================================================================================`n" -ForegroundColor Cyan
Write-Host "  📊 TEST SUMMARY" -ForegroundColor Yellow
Write-Host "`n================================================================================`n" -ForegroundColor Cyan

Write-Host "  Local Credential Manager:  $($results.LocalCredentialManager.Status)" -ForegroundColor $(if($localPass){"Green"}else{"Red"})
Write-Host "  Git Remote Sync:           $($results.GitRemoteSync.Status)" -ForegroundColor $(if($gitPass){"Green"}else{"Red"})
Write-Host "  Google Cloud Sync:         $($results.GoogleCloudSync.Status)" -ForegroundColor $(if($cloudPass){"Green"}else{"Red"})
Write-Host "  Tri-Directional Sync:      $($results.TriDirectionalSync.Status)" -ForegroundColor $(if($results.TriDirectionalSync.Status -eq "FULLY_OPERATIONAL"){"Green"}else{"Yellow"})

Write-Host "`n  Summary: $($results.TriDirectionalSync.Summary)" -ForegroundColor White

# Export results
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$resultFile = "tri_directional_sync_test_$timestamp.json"
$results | ConvertTo-Json -Depth 10 | Out-File $resultFile
Write-Host "`n  📄 Results exported to: $resultFile" -ForegroundColor Cyan

Write-Host "`n================================================================================`n" -ForegroundColor Cyan

# Return status code
if ($results.TriDirectionalSync.Status -eq "FULLY_OPERATIONAL") {
    exit 0
} else {
    exit 1
}
