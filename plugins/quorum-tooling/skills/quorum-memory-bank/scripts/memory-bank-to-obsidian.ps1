<#
.SYNOPSIS
    Upgrade a .claude/memory-bank in place to Obsidian-flavored Markdown.

.DESCRIPTION
    The memory bank is plain Markdown; this adapter makes it open as an Obsidian
    vault WITHOUT depending on the Obsidian app/CLI (agents still read it via grep).
    Runs under PowerShell 7 (pwsh) or Windows PowerShell 5.1.

    -Mode migrate (default) walks every note under architecture/ decisions/
    patterns/ troubleshooting/ (skipping _archived/) and:
      1. injects/repairs YAML frontmatter: `kind` is taken from the folder and
         CORRECTED if wrong; `title` (from the H1), `status` (decisions), `created`
         (body date or -Date) and `tags` are added when missing but never clobbered;
         `updated` is bumped to -Date whenever the note is actually rewritten.
      2. rewrites links inside each "## Related" / "## See also" section (any
         heading level) into [[wikilinks]] -relative *.md links and
         `backtick-wrapped` known note names; external URLs are left as Markdown.
      3. regenerates <Path>/_index.md -a Map-of-Content grouped by category,
         newest-first -which plays the role of the `query` command.

    Idempotent: a note is only rewritten when its content actually changes, so a
    second run with the same -Date is a no-op (and `updated` does not advance on
    unchanged notes). Notes are linked by bare filename stem, so stems must be
    unique across categories -duplicates are reported as a warning.

    -Mode lint is read-only: it reports unresolved [[wikilinks]] and orphan notes
    and exits non-zero when any [[wikilink]] is broken.

.EXAMPLE
    pwsh memory-bank-to-obsidian.ps1 -Path .claude/memory-bank

.EXAMPLE
    pwsh memory-bank-to-obsidian.ps1 -Path .claude/memory-bank -Mode lint
#>
[CmdletBinding()]
param(
    [string]$Path = '.claude/memory-bank',
    [ValidateSet('migrate', 'lint')]
    [string]$Mode = 'migrate',
    [string]$Date = (Get-Date).ToString('yyyy-MM-dd')   # stamped into `updated`; fixed in tests for determinism
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$categories = @('architecture', 'decisions', 'patterns', 'troubleshooting')

# ---- Helpers -------------------------------------------------------------
function Write-Utf8([string]$FilePath, [string]$Content) {
    [System.IO.File]::WriteAllText($FilePath, $Content, $utf8)
}

# Split a note into its frontmatter lines (if any) and body.
function Split-Frontmatter([string]$Raw) {
    $lines = $Raw -split "`r?`n"
    if ($lines.Count -ge 1 -and $lines[0].Trim() -eq '---') {
        for ($i = 1; $i -lt $lines.Count; $i++) {
            if ($lines[$i].Trim() -eq '---') {
                $fmLines = if ($i -gt 1) { $lines[1..($i - 1)] } else { @() }
                $body = if ($i + 1 -le $lines.Count - 1) { ($lines[($i + 1)..($lines.Count - 1)] -join "`n") } else { '' }
                return @{ HasFm = $true; FmLines = @($fmLines); Body = $body }
            }
        }
    }
    return @{ HasFm = $false; FmLines = @(); Body = $Raw }
}

# Parse frontmatter lines into an ordered map: key -> all raw lines for that key
# (so block values like `tags:` + indented `  - x` survive round-tripping).
function Get-FmMap([string[]]$FmLines) {
    $map = [ordered]@{}
    $cur = $null
    foreach ($l in $FmLines) {
        if ($l -match '^([A-Za-z0-9_-]+):') { $cur = $matches[1]; $map[$cur] = @($l) }
        elseif ($cur -and $l -match '^\s+\S') { $map[$cur] += $l }   # block continuation
    }
    return $map
}

function ConvertTo-FmLines($Map) {
    $out = @()
    foreach ($k in $Map.Keys) { $out += $Map[$k] }
    return $out
}

# First H1, with the "Pattern:" / "Decision:" / "ARCHIVED:" prefix stripped.
function Get-Title([string]$Body, [string]$Fallback) {
    foreach ($l in ($Body -split "`r?`n")) {
        if ($l -match '^#\s+(.+?)\s*$') {
            return ($matches[1] -replace '^(Pattern|Decision|ARCHIVED):\s*', '').Trim()
        }
    }
    return $Fallback
}

# A date already written into the body (Decision **Date:**, overview **Generated:**).
function Get-BodyDate([string]$Body) {
    if ($Body -match '\*\*(?:Date|Generated|Archived Date):\*\*\s*(\d{4}-\d{2}-\d{2})') { return $matches[1] }
    return $null
}

function Get-BodyStatus([string]$Body) {
    if ($Body -match '\*\*Status:\*\*\s*([A-Za-z]+)') { return $matches[1].ToLower() }
    return $null
}

# Rewrite links inside every "## Related" / "## See also" section (any level)
# into [[wikilinks]]. Other sections and prose are left untouched.
function Convert-RelatedLinks([string]$Body, [hashtable]$Index) {
    $mdEval = [System.Text.RegularExpressions.MatchEvaluator] {
        param($m)
        $text = $m.Groups[1].Value
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($m.Groups[2].Value)
        $key = $stem.ToLower()
        if ($Index.ContainsKey($key)) {
            $real = $Index[$key]
            if ($text -eq $real -or $text -eq $stem) { return "[[$real]]" }
            return "[[$real|$text]]"
        }
        return $m.Value
    }
    $tickEval = [System.Text.RegularExpressions.MatchEvaluator] {
        param($m)
        $key = $m.Groups[1].Value.ToLower()
        if ($Index.ContainsKey($key)) { return "[[$($Index[$key])]]" }
        return $m.Value
    }

    $lines = $Body -split "`r?`n"
    $inSection = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^#{1,6}\s+(.+?)\s*$') {
            $inSection = ($matches[1] -imatch '^(Related|See also)$')
            continue
        }
        if ($inSection) {
            $lines[$i] = [regex]::Replace($lines[$i], '\[([^\]]+)\]\(([^)]+\.md)\)', $mdEval)
            $lines[$i] = [regex]::Replace($lines[$i], '`([a-z0-9][a-z0-9._-]*)`', $tickEval)
        }
    }
    return ($lines -join "`n")
}

# ---- Resolve the bank ----------------------------------------------------
if (-not (Test-Path $Path)) { throw "Memory bank not found at '$Path'." }
$root = (Resolve-Path $Path).Path

# Index every active note (stem -> canonical stem). Stems must be unique across
# categories because wikilinks resolve by filename; warn on collisions.
$index = @{}
$notes = @()
$collisions = @()
foreach ($cat in $categories) {
    $catDir = Join-Path $root $cat
    if (-not (Test-Path $catDir)) { continue }
    Get-ChildItem -Path $catDir -Filter *.md -File | Where-Object {
        $_.Name -notlike '_*' -and $_.FullName -notmatch '[\\/]_archived[\\/]'
    } | ForEach-Object {
        $stem = $_.BaseName
        $key = $stem.ToLower()
        if ($index.ContainsKey($key)) { $collisions += $stem }
        $index[$key] = $stem
        $notes += [pscustomobject]@{ Category = $cat; File = $_.FullName; Stem = $stem }
    }
}
foreach ($c in ($collisions | Select-Object -Unique)) {
    Write-Warning "Duplicate note stem '$c' across categories - [[wikilinks]] to it resolve ambiguously (last one wins). Rename so stems are globally unique."
}

# ---- LINT mode -----------------------------------------------------------
if ($Mode -eq 'lint') {
    $broken = @(); $linkedTargets = @{}
    foreach ($n in $notes) {
        $raw = Get-Content -Path $n.File -Raw -Encoding utf8
        foreach ($m in [regex]::Matches($raw, '\[\[([^\]\|#]+)(?:[#\|][^\]]*)?\]\]')) {
            $tgt = $m.Groups[1].Value.Trim()
            $linkedTargets[$tgt.ToLower()] = $true
            if (-not $index.ContainsKey($tgt.ToLower())) {
                $broken += [pscustomobject]@{ Note = $n.Stem; Target = $tgt }
            }
        }
    }
    $orphans = @($notes | Where-Object { -not $linkedTargets.ContainsKey($_.Stem.ToLower()) })

    Write-Host "Memory bank: $root"
    Write-Host "Notes: $(@($notes).Count) | Broken links: $(@($broken).Count) | Orphans: $(@($orphans).Count)"
    foreach ($b in $broken) { Write-Host "  [broken] [[$($b.Target)]] in $($b.Note).md" }
    foreach ($o in $orphans) { Write-Host "  [orphan] nothing links to $($o.Stem).md" }
    if ($broken.Count -gt 0) { exit 1 }
    exit 0
}

# ---- MIGRATE mode --------------------------------------------------------
$changedFiles = @(); $unchanged = @()
foreach ($n in $notes) {
    $raw = Get-Content -Path $n.File -Raw -Encoding utf8
    $rawLF = ($raw -replace "`r`n", "`n")
    $fm = Split-Frontmatter $raw

    $kind = if ($n.Category -eq 'architecture') { 'architecture' } else { $n.Category.TrimEnd('s') }
    $title = Get-Title $fm.Body $n.Stem
    $bodyDate = Get-BodyDate $fm.Body
    $status = if ($n.Category -eq 'decisions') { Get-BodyStatus $fm.Body } else { $null }
    $newBody = Convert-RelatedLinks $fm.Body $index

    # Build the structural frontmatter (everything except `updated`): kind is
    # enforced; other keys are added only when missing (never clobbered).
    $map = Get-FmMap $fm.FmLines
    $map['kind'] = @("kind: $kind")
    if (-not $map.Contains('title')) { $map['title'] = @("title: $title") }
    if ($status -and -not $map.Contains('status')) { $map['status'] = @("status: $status") }
    if (-not $map.Contains('created')) {
        $created = if ($bodyDate) { $bodyDate } else { $Date }
        $map['created'] = @("created: $created")
    }
    if (-not $map.Contains('tags')) {
        $tagLines = @('tags:'); foreach ($t in @($kind, $n.Stem)) { $tagLines += "  - $t" }
        $map['tags'] = $tagLines
    }

    $structOut = "---`n" + ((ConvertTo-FmLines $map) -join "`n") + "`n---`n`n" + $newBody.TrimStart("`n")
    if (-not $structOut.EndsWith("`n")) { $structOut += "`n" }

    if ($structOut -eq $rawLF) { $unchanged += $n.File; continue }

    # The note is changing this run, so advance `updated` (created is preserved above).
    $map['updated'] = @("updated: $Date")
    $finalOut = "---`n" + ((ConvertTo-FmLines $map) -join "`n") + "`n---`n`n" + $newBody.TrimStart("`n")
    if (-not $finalOut.EndsWith("`n")) { $finalOut += "`n" }
    Write-Utf8 $n.File $finalOut
    $changedFiles += $n.File
}

# ---- Regenerate _index.md (Map of Content) -------------------------------
$headings = @{
    architecture    = '## Architecture'
    decisions       = '## Decisions'
    patterns        = '## Patterns'
    troubleshooting = '## Troubleshooting'
}
$sb = New-Object System.Text.StringBuilder
[void]$sb.Append("---`nkind: index`ntitle: Memory Bank`ntags:`n  - index`n---`n`n")
[void]$sb.Append("# Memory Bank - Index`n`n")
[void]$sb.Append("Map of content for this memory bank. Regenerated by ``/quorum-memory-bank obsidian``; newest-first per category. Open any ``[[note]]`` to jump in.`n")
foreach ($cat in $categories) {
    $catNotes = $notes | Where-Object { $_.Category -eq $cat }
    if (-not $catNotes) { continue }
    $rows = foreach ($n in $catNotes) {
        $b = (Split-Frontmatter (Get-Content -Path $n.File -Raw -Encoding utf8)).Body
        [pscustomobject]@{ Stem = $n.Stem; Title = (Get-Title $b $n.Stem); Date = (Get-BodyDate $b) }
    }
    $rows = $rows | Sort-Object @{ Expression = { if ($_.Date) { $_.Date } else { '0000-00-00' } }; Descending = $true }, Stem
    [void]$sb.Append("`n$($headings[$cat])`n`n")
    foreach ($r in $rows) { [void]$sb.Append("- [[$($r.Stem)]] - $($r.Title)`n") }
}
$indexPath = Join-Path $root '_index.md'
$indexContent = $sb.ToString()
$indexChanged = $true
if (Test-Path $indexPath) {
    if ((Get-Content -Path $indexPath -Raw -Encoding utf8) -eq $indexContent) { $indexChanged = $false }
}
if ($indexChanged) { Write-Utf8 $indexPath $indexContent }

# ---- Report --------------------------------------------------------------
Write-Host "Memory bank: $root"
Write-Host "Notes processed: $($notes.Count) | rewritten: $($changedFiles.Count) | unchanged: $($unchanged.Count)"
foreach ($c in $changedFiles) { Write-Host "  rewritten: $c" }
Write-Host ("  _index.md: " + $(if ($indexChanged) { 'regenerated' } else { 'unchanged' }))
Write-Host ""
Write-Host "Done. Open '$root' as a vault in Obsidian to see backlinks + graph. Agents keep reading it via grep."
