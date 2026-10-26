# Publish the reviewed local project to an already-created public repository.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$gh = Join-Path $PWD '.tools\gh.exe'
if (!(Test-Path -LiteralPath $gh)) { $gh = 'gh' }
$repo = 'spatsariya/OpenDownload'
function Check-Result {
    if ($LASTEXITCODE -ne 0) { throw "Publication command failed: $LASTEXITCODE" }
}
& $gh repo view $repo --json nameWithOwner,visibility
Check-Result
$visibility = & $gh repo view $repo --json visibility --jq '.visibility'
if ($visibility -ne 'PUBLIC') { throw 'This publication expects an existing public OpenDownload repository.' }
$remote = $null
if (@(git remote) -contains 'origin') { $remote = git remote get-url origin }
if (!$remote) {
    git remote add origin 'https://github.com/spatsariya/OpenDownload.git'
    Check-Result
} elseif ($remote -ne 'https://github.com/spatsariya/OpenDownload.git') {
    throw 'Origin points to a different repository. Inspect it before publishing.'
}
& $gh auth setup-git
Check-Result
git push -u origin main
Check-Result
$tags = & $gh release list --repo $repo --json tagName --jq '.[].tagName'
Check-Result
if (@($tags) -notcontains 'v0.1.0') {
    & $gh release create v0.1.0 'release\OpenDownload-0.1.0-x64.msi' 'release\SHA256SUMS.txt' 'release\INSTALLING.txt' --repo $repo --target main --title 'OpenDownload 0.1.0 — Windows preview' --notes-file 'release\RELEASE-NOTES.md' --prerelease
    Check-Result
}
$ErrorActionPreference = 'Continue'
& $gh api "repos/$repo/pages" --jq '.html_url' 2>$null
$pagesExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($pagesExit -ne 0) {
    '{"source":{"branch":"main","path":"/docs"}}' | & $gh api "repos/$repo/pages" --method POST --input -
    Check-Result
}
Write-Output 'Release published. GitHub Pages deployment may take a few minutes.'
