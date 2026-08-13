"""Fit the learned emitter to real's r(k) ladder by gradient descent.

## Why this is tractable, contrary to what I claimed earlier

I previously said the geometry battery is non-differentiable and a learned
generator would need a surrogate objective. That is wrong, and the correction
is what makes this experiment cheap.

`s(r)` is derived **entirely** from `r(k)`, the median distance to the k-th
neighbour. Matching `r(k)` across the k grid at every rung *is* matching the
profile, by construction — no surrogate. And `torch.topk` is differentiable
(gradient flows to the selected entries), so exact k-NN distances sit inside
the autograd graph. The objective is therefore the geometry itself:

    L = w_shape * sum over rungs, over consecutive k of
            ( dlog r_gen - dlog r_real )^2
      + w_level * sum over rungs of ( mean log r_gen - mean log r_real )^2

**w_level defaults to ZERO, and that is a correctness point, not a tuning
choice.** The registered statistic is scale-invariant: under r -> c*r, log r
shifts by a constant, dlog r is unchanged, so s(r) and the ratio are unchanged.
PROFILE.md scores the ratio and its trend, neither of which depends on the
absolute radius. A level term is therefore unnecessary — and at w_level = 0.05
it was actively harmful: real's log-radius span is only ~0.15 across the k
grid, so each dlog r is ~0.010 and the shape term is ~1e-4, while the level
mismatch contributed ~2e-3. The nominally weak term was 25x the one that
mattered, and the cheapest way to satisfy it was to shrink the radii, which
squashed the profile. The optimiser duly moved the ratio from 0.6 at init to
0.21 while the loss fell 60x.

**The loss is on DIFFERENCES of log r, not levels, and that is not a detail.**
A first attempt scored ``sum (log r_gen(k) - log r_real(k))^2`` and failed for
an instructive reason: that objective is dominated by the overall *scale* of
the radii, so a near-constant offset in log r contributes most of the loss
while contributing nothing to the profile. The optimiser duly reduced the loss
3x (0.105 -> 0.032) while the trend rose to +0.619 at step 40 and then
*collapsed* to -0.282 — it walked away from a good profile because the
objective did not reward it. Since ``s = dlog k / dlog r`` and ``dlog k`` is
fixed by the grid, matching ``dlog r`` *is* matching ``s(r)``; the level is
then pinned separately and weakly.

## What a result would and would not mean

The map has ~131k parameters fitted against 48 targets, which is
Goodhart-maximal — `GENERATOR_SEARCH.md` §5 exists for exactly this. So:

* **Fit succeeds** -> establishes only that *some* memoryless per-row map can
  produce the profile. That is a real and currently-unknown fact, since six
  hand-designed families cannot, but it is not evidence the mechanism is right.
  Adversarial validation and RC-2 would carry the entire burden.
* **Fit fails** -> much stronger. If 131k parameters optimised directly against
  the geometry cannot produce a rising ramp, the target needs structure no
  per-row map of hash noise can express — which would point at row-to-row
  dependence (hierarchy, near-duplicates) as *necessary*, not merely one option
  among several.

Either way it is information the family search does not currently have.

Targets are real's measured `r(k)` at matched rungs under the same protocol
(`small_rung_targets.json`), so both sides see identical treatment.

Env: FL_DIM, FL_HIDDEN, FL_RUNGS, FL_NQ, FL_STEPS, FL_LR, FL_OUT, FL_TARGETS.
"""

from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import torch  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openvector_bench.learned_gen import (  # noqa: E402
    flops_per_row,
    forward_np,
    hash_noise,
    init_params,
    save_params,
)

TARGETS = os.environ.get("FL_TARGETS", "results/small_rung_targets.json")
OUT = os.environ.get("FL_OUT", "results/learned_gen_fit.json")
PARAM_OUT = os.environ.get("FL_PARAM_OUT", "results/learned_gen_params.npz")
DIM = int(os.environ.get("FL_DIM", "1024"))
HIDDEN = int(os.environ.get("FL_HIDDEN", "64"))
RUNGS = json.loads(os.environ.get("FL_RUNGS", "[5000, 10000, 20000]"))
NQ = int(os.environ.get("FL_NQ", "512"))
STEPS = int(os.environ.get("FL_STEPS", "150"))
LR = float(os.environ.get("FL_LR", "3e-3"))
W_SHAPE = float(os.environ.get("FL_W_SHAPE", "1.0"))
W_LEVEL = float(os.environ.get("FL_W_LEVEL", "0.0"))
SEED = 1234

torch.set_num_threads(int(os.environ.get("FL_THREADS", "6")))


def rk_torch(base: torch.Tensor, q: torch.Tensor, kgrid: list[int]) -> torch.Tensor:
    """Median distance to the k-th neighbour, differentiable in base/q."""
    d2 = torch.cdist(q, base) ** 2
    kmax = max(kgrid)
    vals, _ = torch.topk(d2, kmax, dim=1, largest=False)
    vals = torch.sqrt(torch.clamp(vals, min=1e-12))
    return torch.stack([vals[:, k - 1].median() for k in kgrid])


def main() -> int:
    tg = json.load(open(TARGETS))
    kgrid = tg["kgrid"]
    rungs = [n for n in RUNGS if str(n) in tg]
    target_rk = {n: torch.tensor(tg[str(n)]["r_k"], dtype=torch.float32) for n in rungs}
    print(f"dim={DIM} hidden={HIDDEN} rungs={rungs} nq={NQ} steps={STEPS}", flush=True)
    print(
        f"emitter cost {flops_per_row(DIM, HIDDEN)/1e6:.3f} MFLOPs/row "
        f"(bound ~4 MFLOPs for regeneration to beat a network fetch)",
        flush=True,
    )
    for n in rungs:
        print(
            f"  target n={n:6d} ratio {tg[str(n)]['ratio']:.3f} "
            f"G1 {tg[str(n)]['g1']:.2f}",
            flush=True,
        )

    p0 = init_params(DIM, HIDDEN, seed=SEED)
    tp = {
        k: torch.tensor(np.asarray(v), dtype=torch.float32, requires_grad=True)
        for k, v in p0.items()
    }
    opt = torch.optim.Adam(tp.values(), lr=LR)

    nmax = max(rungs)
    # Noise is FIXED across steps: gradients flow to the map only, and the
    # optimiser cannot chase resampling noise between iterations.
    z_all = torch.tensor(hash_noise(np.arange(nmax + NQ), DIM, SEED))

    def fwd(z):
        h = torch.tanh(z @ tp["W1"] + tp["b1"])
        x = tp["alpha"] * z + h @ tp["W2"]
        return x / torch.clamp(x.norm(dim=1, keepdim=True), min=1e-12)

    # FIXED rung draws. Resampling these every step made the objective itself
    # noisy: with few queries the median r(k) targets moved between steps, so
    # the optimiser chased noise and reached loss 5e-5 while the true ratio sat
    # at 0.27. One draw per rung, held for the whole fit.
    fixed_idx = {n: torch.randperm(nmax)[:n] for n in rungs}

    hist = []
    t0 = time.time()
    for step in range(STEPS):
        opt.zero_grad()
        xa = fwd(z_all)
        q = xa[nmax:]
        loss = 0.0
        for n in rungs:
            idx = fixed_idx[n]
            rk = rk_torch(xa[idx], q, kgrid)
            lg, lt = torch.log(rk), torch.log(target_rk[n])
            # shape: consecutive differences of log r ARE the profile
            shape = ((lg[1:] - lg[:-1]) - (lt[1:] - lt[:-1])) ** 2
            level = (lg.mean() - lt.mean()) ** 2
            loss = loss + W_SHAPE * shape.mean() + W_LEVEL * level
        loss.backward()
        opt.step()
        if step % 10 == 0 or step == STEPS - 1:
            with torch.no_grad():
                xa2 = fwd(z_all)
                ratios = []
                for n in rungs:
                    rk = rk_torch(xa2[fixed_idx[n]], xa2[nmax:], kgrid)
                    lk = torch.log(torch.tensor([float(k) for k in kgrid]))
                    s = torch.gradient(lk, spacing=(torch.log(rk),))[0]
                    ratios.append(float(s[-1] / s[0]))
                tr = (
                    float(np.polyfit(np.log(rungs), ratios, 1)[0])
                    if len(rungs) > 1
                    else float("nan")
                )
            hist.append(
                {
                    "step": step,
                    "loss": float(loss.detach()),
                    "ratios": ratios,
                    "trend": tr,
                }
            )
            print(
                f"  step {step:4d} loss {float(loss.detach()):.6f} "
                f"ratios {[round(r,3) for r in ratios]} trend {tr:+.3f} "
                f"({time.time()-t0:.0f}s)",
                flush=True,
            )

    fitted = {k: v.detach().numpy() for k, v in tp.items()}
    fitted["alpha"] = np.float32(fitted["alpha"])
    save_params(fitted, PARAM_OUT)

    # Independent check through the NUMPY deployment path, not the torch graph.
    zc = hash_noise(np.arange(2048), DIM, SEED)
    agree = float(
        np.abs(forward_np(zc, fitted) - fwd(torch.tensor(zc)).detach().numpy()).max()
    )
    print(f"\nnumpy/torch forward agreement: max abs diff {agree:.2e}", flush=True)

    target_trend = float(
        np.polyfit(np.log(rungs), [tg[str(n)]["ratio"] for n in rungs], 1)[0]
    )
    final = hist[-1]
    print(
        f"target  ratios {[round(tg[str(n)]['ratio'],3) for n in rungs]} "
        f"trend {target_trend:+.3f}",
        flush=True,
    )
    print(
        f"fitted  ratios {[round(r,3) for r in final['ratios']]} "
        f"trend {final['trend']:+.3f}",
        flush=True,
    )
    verdict = (
        "MAP CAN PRODUCE A RISING RAMP"
        if final["trend"] > 0.15
        else "MAP CANNOT — per-row maps of hash noise may be insufficient"
    )
    print(f"VERDICT: {verdict}", flush=True)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": {
                    "dim": DIM,
                    "hidden": HIDDEN,
                    "rungs": rungs,
                    "nq": NQ,
                    "steps": STEPS,
                    "lr": LR,
                    "seed": SEED,
                    "mflops_per_row": flops_per_row(DIM, HIDDEN) / 1e6,
                },
                "target_trend": target_trend,
                "target_ratios": [tg[str(n)]["ratio"] for n in rungs],
                "history": hist,
                "numpy_torch_agreement": agree,
                "verdict": verdict,
            },
            f,
            indent=2,
        )
    print(f"wrote {OUT}", flush=True)
    print("FIT_LEARNED_GEN_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
