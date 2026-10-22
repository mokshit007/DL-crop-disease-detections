# Trains the architectures with an identical recipe on the leaf-disjoint split,
# then runs the clean / corruption / field-photo comparison. Log: results/ablation_log.txt
# "<arch>_field" runs add blur / sensor-noise training augmentation (src/train.py --field-aug).
# Safe to re-run after an interruption: finished runs are skipped and an unfinished run
# resumes from its last completed epoch (models/<run>_last.pt).
# Python output is redirected through cmd: Windows PowerShell 5.1 turns native stderr
# (tqdm progress bars) into error records.
$epochs = 8
$workers = 2   # each DataLoader worker reserves ~1 GB of page-file memory on Windows
$log = "results\ablation_log.txt"
Remove-Item results\ablation_done.txt -ErrorAction SilentlyContinue
foreach ($run in @("baseline", "msaf", "cbam", "baseline_field", "msaf_field")) {
    $arch = $run.Split("_")[0]
    $extra = if ($run.EndsWith("_field")) { "--field-aug" } else { "" }
    $hist = "results\history_$run.json"
    if ((Test-Path $hist) -and ((Get-Content $hist -Raw | ConvertFrom-Json).val_accs.Count -ge $epochs) -and -not (Test-Path "models\${run}_last.pt")) {
        "Skipping $run (already trained)" | Out-File -Append -Encoding ascii $log
        continue
    }
    # Retry: a crash (e.g. Windows running out of page-file memory) resumes from the last saved epoch
    $attempt = 0
    do {
        $attempt++
        cmd /c "python -u -W ignore -m src.train --arch $arch $extra --epochs $epochs --workers $workers >> $log 2>&1"
    } while ($LASTEXITCODE -ne 0 -and $attempt -lt 3)
    if ($LASTEXITCODE -ne 0) { "FAILED $run" | Out-File -Encoding ascii results\ablation_done.txt; exit 1 }
}
cmd /c "python -u -W ignore -m src.compare --workers $workers >> $log 2>&1"
"DONE exit=$LASTEXITCODE" | Out-File -Encoding ascii results\ablation_done.txt
