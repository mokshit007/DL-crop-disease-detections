"""Live view of run_ablation.ps1 (results/ablation_log.txt). Refreshes every 3 s; Ctrl-C to quit."""
import os
import re
import sys
import json
import time
import subprocess

LOG = 'results/ablation_log.txt'
DONE = 'results/ablation_done.txt'
RUNS = ['baseline', 'msaf', 'cbam', 'baseline_field', 'msaf_field']
EPOCHS = 8
COMPARE_MIN_PER_RUN = 7   # rough minutes the comparison spends on each newly trained model

def gpu_status():
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                              '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=5).stdout.strip()
        util, used, total, temp = [x.strip() for x in out.split(',')]
        return f"GPU {util:>3}%  |  VRAM {int(used)/1024:.1f}/{int(total)/1024:.1f} GB  |  {temp} C"
    except Exception:
        return 'GPU status unavailable'

def bar(frac, width=30):
    n = int(round(frac * width))
    return '#' * n + '-' * (width - n)

def history(run):
    path = f'results/history_{run}.json'
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None

def render():
    text = open(LOG, encoding='utf-8', errors='replace').read() if os.path.exists(LOG) else ''
    lines = [l.strip() for l in re.split(r'[\r\n]+', text) if l.strip()]
    current = None
    for l in lines:
        m = re.match(r"Training '(\w+)'", l)
        if m:
            current = m.group(1)
    bars = [l for l in lines if '[Train]' in l and '%|' in l]
    last_bar = bars[-1] if bars else ''
    m = re.search(r'Epoch (\d+)/(\d+) \[Train\]:\s+(\d+)%\|.*\| (\d+)/(\d+) \[([\d:]+)<([\d:?]+)', last_bar)

    out = [f"CropSense training monitor  |  {time.strftime('%H:%M:%S')}  |  Ctrl-C to quit", '', gpu_status(), '']
    remaining_min = 0.0
    epoch_min = []
    for run in RUNS:
        h = history(run)
        if h and h.get('epoch_seconds'):
            epoch_min.append(sum(h['epoch_seconds']) / len(h['epoch_seconds']) / 60)
    avg_epoch = (sum(epoch_min) / len(epoch_min)) if epoch_min else 5.5
    pending_compare = 0

    for run in RUNS:
        h = history(run)
        done_epochs = len(h['val_accs']) if h else 0
        last_pt = os.path.exists(f'models/{run}_last.pt')
        if done_epochs >= EPOCHS and not last_pt:
            state = f"done        best val {h['best_val_acc']:.2f}%"
        elif run == current:
            state = f"TRAINING    epoch {done_epochs + 1}/{EPOCHS}" + (f"   best val so far {h['best_val_acc']:.2f}%" if h else '')
            frac = int(m.group(4)) / int(m.group(5)) if m and int(m.group(1)) == done_epochs + 1 else 0.0
            remaining_min += (EPOCHS - done_epochs - frac) * avg_epoch
            pending_compare += 1
        else:
            state = 'waiting'
            remaining_min += EPOCHS * avg_epoch
            pending_compare += 1
        out.append(f"  {run:16s} {state}")

    if m and not os.path.exists(DONE):
        ep, n_ep, pct, it, n_it, elapsed, eta = m.groups()
        out += ['', f"  Current epoch {ep}/{n_ep}  [{bar(int(it) / int(n_it))}] {pct}%  ({it}/{n_it} batches, {elapsed} elapsed, ~{eta} left)"]

    if lines and lines[-1].startswith('[') or any(l.startswith('[') and 'clean acc' in l for l in lines[-60:]):
        out += ['', '  Comparison output:'] + ['    ' + l for l in lines if l.startswith('[') or l.startswith('Reusing')][-12:]

    if os.path.exists(DONE):
        out += ['', 'Finished: ' + open(DONE, encoding='utf-8', errors='replace').read().strip()]
    else:
        remaining_min += pending_compare * COMPARE_MIN_PER_RUN
        finish = time.strftime('%H:%M', time.localtime(time.time() + remaining_min * 60))
        out += ['', f"  Estimated time left: ~{remaining_min:.0f} min  ->  finishes around {finish} (training + comparison)"]
    return '\n'.join(out)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        while True:
            screen = render()
            os.system('cls' if os.name == 'nt' else 'clear')
            print(screen)
            sys.stdout.flush()
            if os.path.exists(DONE):
                break
            time.sleep(3)
    except KeyboardInterrupt:
        pass
