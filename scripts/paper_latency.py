"""Latency for the paper: median of 5 interleaved rounds per architecture (batch 1, FP32), GPU and CPU.
Updates results/paper/efficiency.json. Run: python -m scripts.paper_latency"""
import json, time
import numpy as np, torch
from src.model import get_model

def timed(model, x, runs):
    sync = torch.cuda.synchronize if x.is_cuda else (lambda: None)
    with torch.no_grad():
        for _ in range(10):
            model(x)
        sync(); t = time.perf_counter()
        for _ in range(runs):
            model(x)
        sync()
    return (time.perf_counter() - t) / runs * 1000

def main():
    torch.set_num_threads(4)
    archs = ('baseline', 'cbam', 'msaf')
    models = {a: get_model(38, arch=a, pretrained=False).eval() for a in archs}
    res = {a: {'gpu': [], 'cpu': []} for a in archs}
    for _ in range(5):
        for a, m in models.items():
            res[a]['cpu'].append(timed(m.cpu(), torch.randn(1, 3, 224, 224), 15))
            res[a]['gpu'].append(timed(m.cuda(), torch.randn(1, 3, 224, 224, device='cuda'), 100))
            m.cpu()
    with open('results/paper/efficiency.json') as f:
        eff = json.load(f)
    for a in archs:
        eff[a]['gpu_latency_ms'] = round(float(np.median(res[a]['gpu'])), 2)
        eff[a]['cpu_latency_ms'] = round(float(np.median(res[a]['cpu'])), 1)
        eff[a]['cpu_threads'] = 4
        print(a, eff[a], [round(v, 1) for v in res[a]['cpu']])
    with open('results/paper/efficiency.json', 'w') as f:
        json.dump(eff, f, indent=2)

if __name__ == '__main__':
    main()
