"""
Metrics for the research paper, computed from the logits cached by scripts/paper_eval.py.

  - accuracy, macro precision / recall / F1, per-corruption accuracy and mCA
  - calibration: ECE (15 bins), mean confidence, NLL and Brier score, before and after
    temperature scaling fitted on the clean validation set
  - selective prediction on the pooled corrupted test set (risk-coverage, AURC,
    accuracy at fixed coverage, misclassification-detection AUROC)
  - 95% bootstrap confidence intervals and paired significance tests (exact McNemar,
    paired bootstrap for mCA / ECE differences)
  - per-class F1 and the most frequent confusions
Output: results/paper/metrics.json
Run from crop-disease-detection/:  python -m scripts.paper_analysis
"""
import json
import os

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import log_softmax, softmax
from scipy.stats import binomtest
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

OUT_DIR = 'results/paper'
RUNS = ('baseline', 'cbam', 'msaf', 'baseline_field', 'msaf_field')
PAIRS = (('baseline', 'msaf'), ('baseline', 'cbam'), ('cbam', 'msaf'),
         ('baseline_field', 'msaf_field'), ('baseline', 'msaf_field'))
BOOT = 1000
COVERAGES = (0.9, 0.8)


def ece(probs, labels, bins=15):
    conf, pred = probs.max(-1), probs.argmax(-1)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs((pred[m] == labels[m]).mean() - conf[m].mean())
    return total


def reliability(probs, labels, bins=15):
    conf, correct = probs.max(-1), probs.argmax(-1) == labels
    edges = np.linspace(0, 1, bins + 1)
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            rows.append({'lo': lo, 'hi': hi, 'count': int(m.sum()), 'conf': float(conf[m].mean()), 'acc': float(correct[m].mean())})
    return rows


def nll(logits, labels, t=1.0):
    return float(-log_softmax(logits / t, axis=-1)[np.arange(len(labels)), labels].mean())


def brier(probs, labels):
    onehot = np.eye(probs.shape[-1])[labels]
    return float(((probs - onehot) ** 2).sum(-1).mean())


def fit_temperature(logits, labels):
    res = minimize_scalar(lambda s: nll(logits, labels, np.exp(s)), bounds=(-3, 3), method='bounded')
    return float(np.exp(res.x))


def risk_coverage(conf, correct):
    order = np.argsort(-conf, kind='stable')
    hits = correct[order].astype(np.float64)
    n = np.arange(1, len(hits) + 1)
    risk = 1 - np.cumsum(hits) / n
    return n / len(hits), risk


def pct(x, d=2):
    return round(100 * float(x), d)


def ci(samples):
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [pct(lo), pct(hi)]


def main():
    D = np.load(os.path.join(OUT_DIR, 'logits.npz'))
    y, yv, yf = D['labels_test'], D['labels_val'], D['labels_field']
    conditions = [str(c) for c in D['conditions']]
    class_names = [str(c) for c in D['class_names']]
    n = len(y)
    rng = np.random.default_rng(0)
    boot_idx = rng.integers(0, n, size=(BOOT, n))

    out = {'test_images': int(n), 'val_images': int(len(yv)), 'conditions': conditions, 'runs': {}, 'pairs': {}}
    correct_all, conf_all = {}, {}
    for run in RUNS:
        L = D[f'{run}_test']                       # [7, N, C]
        P = softmax(L, axis=-1)
        pred = P.argmax(-1)
        correct = pred == y
        T = fit_temperature(D[f'{run}_val'], yv)
        PT = softmax(L / T, axis=-1)
        correct_all[run], conf_all[run] = correct, P.max(-1)

        prec, rec, f1, _ = precision_recall_fscore_support(y, pred[0], average='macro', zero_division=0)
        per_class = precision_recall_fscore_support(y, pred[0], average=None, zero_division=0)[2]
        r = {
            'temperature': round(T, 3),
            'clean': {
                'acc': pct(correct[0].mean()), 'precision': pct(prec), 'recall': pct(rec), 'f1': pct(f1),
                'nll': round(nll(L[0], y), 4), 'nll_ts': round(nll(L[0], y, T), 4),
                'brier': round(brier(P[0], y), 4), 'brier_ts': round(brier(PT[0], y), 4),
            },
            'acc': {c: pct(correct[i].mean()) for i, c in enumerate(conditions)},
            'mean_conf': {c: pct(P[i].max(-1).mean()) for i, c in enumerate(conditions)},
            'ece': {c: pct(ece(P[i], y)) for i, c in enumerate(conditions)},
            'ece_ts': {c: pct(ece(PT[i], y)) for i, c in enumerate(conditions)},
            'reliability_clean': reliability(P[0], y),
            'reliability_corrupted': reliability(P[1:].reshape(-1, P.shape[-1]), np.tile(y, len(conditions) - 1)),
            'per_class_f1': {class_names[k]: pct(v) for k, v in enumerate(per_class)},
        }
        r['mCA'] = pct(correct[1:].mean())
        r['ece_corrupted_mean'] = round(float(np.mean([r['ece'][c] for c in conditions[1:]])), 2)
        r['ece_ts_corrupted_mean'] = round(float(np.mean([r['ece_ts'][c] for c in conditions[1:]])), 2)

        # Selective prediction on the pooled corrupted test set (6 x N predictions)
        conf_c, corr_c = P[1:].max(-1).ravel(), correct[1:].ravel()
        cov, risk = risk_coverage(conf_c, corr_c)
        r['selective'] = {
            'aurc': round(float(risk.mean()) * 100, 3),
            'auroc_error_detection': pct(roc_auc_score(~corr_c, -conf_c)),
            **{f'acc_at_{int(c * 100)}': pct(1 - risk[int(c * len(risk)) - 1]) for c in COVERAGES},
            'curve': [[round(float(cov[i]), 4), round(float(risk[i]), 5)] for i in np.linspace(0, len(cov) - 1, 200).astype(int)],
        }

        # Bootstrap 95% CIs (resampling test images; corruptions stay paired with their image)
        r['ci'] = {
            'clean_acc': ci(correct[0][boot_idx].mean(1)),
            'mCA': ci(correct[1:][:, boot_idx].mean(axis=(0, 2))),
            'ece_clean': ci([ece(P[0][b], y[b]) for b in boot_idx[:300]]),
        }

        # Field photos
        Pf, PfT = softmax(D[f'{run}_field'], -1), softmax(D[f'{run}_field'] / T, -1)
        r['field'] = {
            'correct': int((Pf.argmax(-1) == yf).sum()), 'total': int(len(yf)),
            'true_class_conf': pct(Pf[np.arange(len(yf)), yf].mean(), 1),
            'predictions': [class_names[k] for k in Pf.argmax(-1)],
            'true_class_conf_ts': pct(PfT[np.arange(len(yf)), yf].mean(), 1),
        }

        # Most frequent confusions on clean images
        conf_pairs = {}
        for t, p in zip(y[~correct[0]], pred[0][~correct[0]]):
            key = f'{class_names[t]} -> {class_names[p]}'
            conf_pairs[key] = conf_pairs.get(key, 0) + 1
        r['top_confusions_clean'] = sorted(conf_pairs.items(), key=lambda kv: -kv[1])[:8]
        r['errors_clean'] = int((~correct[0]).sum())
        out['runs'][run] = r
        print(f"{run:15s} acc {r['clean']['acc']}  F1 {r['clean']['f1']}  mCA {r['mCA']}  ECE {r['ece']['Clean']} -> TS {r['ece_ts']['Clean']} "
              f"(T={T:.3f})  ECEcorr {r['ece_corrupted_mean']} -> {r['ece_ts_corrupted_mean']}  AURC {r['selective']['aurc']}  "
              f"AUROC {r['selective']['auroc_error_detection']}", flush=True)

    # Paired comparisons A vs B
    for a, b in PAIRS:
        ca, cb = correct_all[a], correct_all[b]
        tests = {}
        for i, c in enumerate(conditions):
            only_a, only_b = int((ca[i] & ~cb[i]).sum()), int((~ca[i] & cb[i]).sum())
            p = binomtest(min(only_a, only_b), only_a + only_b, 0.5).pvalue if only_a + only_b else 1.0
            tests[c] = {'a_only_correct': only_a, 'b_only_correct': only_b, 'mcnemar_p': float(f'{p:.3g}')}
        d_mca = cb[1:][:, boot_idx].mean(axis=(0, 2)) - ca[1:][:, boot_idx].mean(axis=(0, 2))
        Pa, Pb = softmax(D[f'{a}_test'][0], -1), softmax(D[f'{b}_test'][0], -1)
        d_ece = [ece(Pb[s], y[s]) - ece(Pa[s], y[s]) for s in boot_idx[:300]]
        out['pairs'][f'{a}_vs_{b}'] = {
            'per_condition': tests,
            'delta_mCA': pct(cb[1:].mean() - ca[1:].mean()), 'delta_mCA_ci': ci(d_mca),
            'delta_ece_clean': pct(ece(Pb, y) - ece(Pa, y)), 'delta_ece_clean_ci': ci(d_ece),
        }
        print(f'{a} vs {b}: dmCA {out["pairs"][f"{a}_vs_{b}"]["delta_mCA"]} {ci(d_mca)}  '
              + '  '.join(f'{c[:6]} p={t["mcnemar_p"]}' for c, t in tests.items()), flush=True)

    # Efficiency and training time
    with open(os.path.join(OUT_DIR, 'efficiency.json')) as f:
        out['efficiency'] = json.load(f)
    out['training'] = {}
    for run in RUNS:
        with open(f'results/history_{run}.json') as f:
            h = json.load(f)
        out['training'][run] = {'epochs': h['epochs'], 'minutes': round(sum(h['epoch_seconds']) / 60, 1),
                                'best_val_acc': round(h['best_val_acc'], 2), 'val_acc': h['val_accs'],
                                'train_loss': h['train_losses'], 'val_loss': h['val_losses']}

    with open(os.path.join(OUT_DIR, 'metrics.json'), 'w') as f:
        json.dump(out, f, indent=1, default=float)
    print('wrote', os.path.join(OUT_DIR, 'metrics.json'))


if __name__ == '__main__':
    main()
