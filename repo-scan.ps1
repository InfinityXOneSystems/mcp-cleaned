# List repos under C:\AI\repos with git info + size
# Save as: repo-scan.ps1
# Run:    powershell -ExecutionPolicy Bypass -File .\repo-scan.ps1
# Optional: .\repo-scan.ps1 -Path "C:\AI\repos" -OutCsv "C:\AI\repo-scan.csv"

param(
  [string]$Path = "C:\AI\repos",
  [string]$OutCsv = ""
)

function Get-FolderSizeBytes {
  param([string]$Folder)
  try {
    (Get-ChildItem -LiteralPath $Folder -Recurse -Force -File -ErrorAction SilentlyContinue |
      Measure-Object -Property Length -Sum).Sum
  } catch {
    $null
  }
}

function Format-Bytes {
  param([Nullable[double]]$Bytes)
  if ($null -eq $Bytes) { return "" }
  $units = @("B","KB","MB","GB","TB")
  $i = 0
  while ($Bytes -ge 1024 -and $i -lt $units.Count-1) {
    $Bytes /= 1024
    $i++
  }
  "{0:N2} {1}" -f $Bytes, $units[$i]
}

$root = (Resolve-Path -LiteralPath $Path).Path

# Candidate repos = immediate subfolders (and the root itself if it’s a repo)
$folders = @()
$folders += Get-Item -LiteralPath $root

$folders += Get-ChildItem -LiteralPath $root -Directory -Force -ErrorAction SilentlyContinue

$results = foreach ($f in $folders) {
  $gitDir = Join-Path $f.FullName ".git"
  if (-not (Test-Path -LiteralPath $gitDir)) { continue }

  $branch = ""
  $dirty  = ""
  $aheadBehind = ""
  $remote = ""

  # Gather git info (only if git is available)
  if (Get-Command git -ErrorAction SilentlyContinue) {
    pushd $f.FullName
    try {
      $branch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
      $porcelain = (git status --porcelain 2>$null)
      $dirty = if ($porcelain) { "dirty" } else { "clean" }

      # upstream + ahead/behind
      $remote = (git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null).Trim()
      if ($remote) {
        $ab = (git rev-list --left-right --count "$remote...HEAD" 2>$null).Trim()
        # ab format: "behind ahead"
        if ($ab) {
          $parts = $ab -split "\s+"
          if ($parts.Count -ge 2) {
            $behind = $parts[0]
            $ahead  = $parts[1]
            $aheadBehind = "ahead:$ahead behind:$behind"
          }
        }
      }
    } catch {
      # ignore git errors
    } finally {
      popd
    }
  }

  $sizeBytes = Get-FolderSizeBytes -Folder $f.FullName

  [pscustomobject]@{
    Repo         = $f.Name
    Path         = $f.FullName
    LastWrite    = $f.LastWriteTime
    Size         = Format-Bytes $sizeBytes
    Branch       = $branch
    Status       = $dirty
    Upstream     = $remote
    AheadBehind  = $aheadBehind
  }
}

# Pretty console output
$results |
  Sort-Object LastWrite -Descending |
  Format-Table Repo, Branch, Status, Size, LastWrite, AheadBehind -AutoSize

# Optional CSV export
if ($OutCsv -and $results) {
  $results |
    Sort-Object Repo |
    Export-Csv -NoTypeInformation -Encoding UTF8 -Path $OutCsv
  Write-Host "`nSaved CSV -> $OutCsv"
}
