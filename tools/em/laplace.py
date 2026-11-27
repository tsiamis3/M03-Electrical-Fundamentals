"""Solve Laplace's equation in 2-D by relaxation, and make the figures of deep/em-laplace.md.

    python tools/em/laplace.py            # runs the three studies, prints the numbers, writes assets/img/em/laplace-*.svg

Physics in one line: in a region without charge the potential obeys ∇²V = 0, and on a square grid
that means every free point equals the average of its four neighbours. Conductors are points whose
potential is fixed. We start from any guess and keep replacing each free point by the average of its
neighbours until nothing changes any more ("relaxation"). Then E = −∇V.

The geometry is 2-D: everything is infinitely long in z (plates are strips, the needle is a thin blade).
Needs numpy and matplotlib.
"""
import math
import pathlib

import numpy as np

EPS0 = 8.8541878128e-12
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "img" / "em"


class LaplaceSolver:
    """A rectangular box of nx × ny grid points with spacing h (metres).

    V      : potential at every grid point (volts)
    fixed  : True where the potential is imposed (conductors and the outer boundary)
    """

    def __init__(self, width, height, h):
        self.h = h
        self.nx, self.ny = int(round(width / h)) + 1, int(round(height / h)) + 1
        self.x = np.arange(self.nx) * h
        self.y = np.arange(self.ny) * h
        self.V = np.zeros((self.ny, self.nx))          # index [row = y, column = x]
        self.fixed = np.zeros_like(self.V, dtype=bool)
        self.fixed[0, :] = self.fixed[-1, :] = self.fixed[:, 0] = self.fixed[:, -1] = True   # outer box: V = 0 unless set
        # red/black colouring of the interior, for Gauss–Seidel and SOR (see relax)
        i, j = np.meshgrid(np.arange(1, self.ny - 1), np.arange(1, self.nx - 1), indexing="ij")
        self.red = (i + j) % 2 == 0

    # ---- building the geometry -------------------------------------------------
    def idx(self, x, y):
        """Grid indices (row, column) nearest to the point (x, y) in metres."""
        return int(round(y / self.h)), int(round(x / self.h))

    def conductor(self, mask, volts):
        """Fix the potential on every grid point where mask is True."""
        self.V[mask] = volts
        self.fixed |= mask

    def rectangle(self, x0, x1, y0, y1, volts):
        X, Y = np.meshgrid(self.x, self.y)
        self.conductor((X >= x0 - 1e-12) & (X <= x1 + 1e-12) & (Y >= y0 - 1e-12) & (Y <= y1 + 1e-12), volts)

    def disk(self, xc, yc, r, volts):
        X, Y = np.meshgrid(self.x, self.y)
        self.conductor((X - xc) ** 2 + (Y - yc) ** 2 <= r ** 2, volts)

    def boundary(self, func):
        """Set the outer boundary to V = func(x, y), e.g. a uniform field far away."""
        X, Y = np.meshgrid(self.x, self.y)
        edge = np.zeros_like(self.fixed); edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
        self.V[edge] = func(X, Y)[edge]

    # ---- the solver ------------------------------------------------------------
    def neighbour_average(self):
        """Average of the four neighbours of every interior point: the discrete form of ∇²V = 0."""
        V = self.V
        return 0.25 * (V[2:, 1:-1] + V[:-2, 1:-1] + V[1:-1, 2:] + V[1:-1, :-2])

    def relax(self, method="sor", tol=1e-6, max_iter=200_000, omega=None):
        """Iterate until the largest change in one sweep is below tol × (largest |V|).

        jacobi : every point takes the average of the OLD neighbours (simple, slow).
        gs     : Gauss–Seidel; points use neighbours already updated in this sweep.
                 Done as two half-sweeps, "red" then "black" points, like a chess board.
        sor    : successive over-relaxation; Gauss–Seidel but overshoot by a factor omega (1 < ω < 2).
                 Best ω for an N×N box is about 2 / (1 + π/N).
        Returns the number of sweeps.
        """
        free = ~self.fixed[1:-1, 1:-1]
        scale = max(np.abs(self.V).max(), 1e-30)
        if method in ("jacobi", "gs"):
            omega = 1.0
        elif omega is None:
            omega = 2 / (1 + math.pi / max(self.nx, self.ny))
        inner = self.V[1:-1, 1:-1]                      # a view: writing to it writes to self.V
        for it in range(1, max_iter + 1):
            if method == "jacobi":
                avg = self.neighbour_average()
                change = np.where(free, avg - inner, 0.0)
                inner += change
                delta = np.abs(change).max()
            else:
                delta = 0.0
                for colour in (self.red, ~self.red):
                    upd = free & colour
                    avg = self.neighbour_average()
                    change = omega * (avg[upd] - inner[upd])
                    inner[upd] += change
                    delta = max(delta, np.abs(change).max() if change.size else 0.0)
            if delta < tol * scale:
                return it
        raise RuntimeError(f"{method}: no convergence in {max_iter} sweeps")

    # ---- results -----------------------------------------------------------------
    def field(self):
        """E = −∇V by central differences (V/m). Returns Ex, Ey, |E|."""
        dVdy, dVdx = np.gradient(self.V, self.h)
        Ex, Ey = -dVdx, -dVdy
        return Ex, Ey, np.hypot(Ex, Ey)

    def charge_inside(self, x0, x1, y0, y1):
        """Charge per unit length (C/m) inside a rectangle, from Gauss's law: Q' = ε0 ∮ E·n dl."""
        Ex, Ey, _ = self.field()
        r0, c0 = self.idx(x0, y0); r1, c1 = self.idx(x1, y1)
        flux = (Ex[r0:r1 + 1, c1].sum() - Ex[r0:r1 + 1, c0].sum() + Ey[r1, c0:c1 + 1].sum() - Ey[r0, c0:c1 + 1].sum()) * self.h
        return EPS0 * flux


# =================================================================== the three studies
def study_capacitor(plot=None):
    """Two plates (strips) 6 cm wide, 2 cm apart, at ±50 V, in a grounded box 30 cm × 20 cm.
    Compare the capacitance per metre with the ideal ε0·w/d (no fringing)."""
    w, d, V0, h = 0.06, 0.02, 50.0, 0.5e-3
    s = LaplaceSolver(0.30, 0.20, h)
    xc, yc = 0.15, 0.10
    s.rectangle(xc - w / 2, xc + w / 2, yc + d / 2, yc + d / 2 + h, +V0)
    s.rectangle(xc - w / 2, xc + w / 2, yc - d / 2 - h, yc - d / 2, -V0)
    n = s.relax("sor", tol=1e-7)
    q = s.charge_inside(xc - w / 2 - 4 * h, xc + w / 2 + 4 * h, yc + d / 2 - 4 * h, yc + d / 2 + 5 * h)
    C = q / (2 * V0)
    C_ideal = EPS0 * w / d
    print(f"capacitor: {n} SOR sweeps; C' = {C*1e12:.1f} pF/m, ideal ε0 w/d = {C_ideal*1e12:.1f} pF/m, ratio {C/C_ideal:.2f}")
    if plot:
        plot.capacitor(s, xc, yc, w, d)
    return C, C_ideal


def study_tip(plot=None):
    """A grounded plane in a uniform field E0 = 100 kV/m (V = E0·y far away).
    On the plane: a half-cylinder boss of radius 5 mm (theory: field ×2 at its top in 2-D),
    and a thin blade 20 mm high, 1 mm thick (like a static wick). Field at the top of each, divided by E0."""
    E0, h = 1e5, 0.25e-3
    results = {}
    for name in ("boss", "blade"):
        s = LaplaceSolver(0.20, 0.12, h)
        s.boundary(lambda X, Y: E0 * Y)
        s.rectangle(0, 0.20, 0, 0, 0.0)                              # the grounded plane (bottom row)
        if name == "boss":
            s.disk(0.10, 0.0, 0.005, 0.0); top_y = 0.005
        else:
            s.rectangle(0.10 - 0.0005, 0.10 + 0.0005, 0, 0.020, 0.0); top_y = 0.020
        n = s.relax("sor", tol=1e-7)
        _, _, E = s.field()
        r, c = s.idx(0.10, top_y)
        k = E[r + 1, c] / E0                                          # first free grid point above the top
        prof = (np.arange(1, 41) * s.h, E[r + 1:r + 41, c] / E0)     # (distance above the top, E/E0)
        results[name] = (k, n, s, prof)
        print(f"{name}: {n} SOR sweeps; field one grid step above the top = {k:.2f} × E0")
    # check against the exact 2-D result for a grounded half-cylinder of radius R on a plane: E = E0 (1 + R²/y²)
    R = 0.005
    dist, num = results["boss"][3]
    theory = 1 + (R / (R + dist)) ** 2
    print("boss profile, distance (mm) / numeric / exact:")
    for dd, nn, tt in list(zip(dist, num, theory))[:12:2]:
        print(f"   {dd*1e3:5.2f}  {nn:.3f}  {tt:.3f}")
    if plot:
        plot.tip(results, E0)
    return {k: v[0] for k, v in results.items()}


def study_convergence(plot=None):
    """Same problem (a 101 × 101 box, one side at 1 V) solved three ways; sweeps to reach 1e-6."""
    out = {}
    for method in ("jacobi", "gs", "sor"):
        s = LaplaceSolver(1.0, 1.0, 0.01)
        s.V[-1, 1:-1] = 1.0                                          # top side at 1 V, others 0
        hist = []
        free = ~s.fixed[1:-1, 1:-1]
        exact_ref = None
        # record the change per sweep to draw the convergence curve
        omega = 2 / (1 + math.pi / 101) if method == "sor" else 1.0
        inner = s.V[1:-1, 1:-1]
        for it in range(1, 30_001):
            old = inner.copy()
            if method == "jacobi":
                avg = s.neighbour_average(); inner[free] = avg[free]
            else:
                for colour in (s.red, ~s.red):
                    upd = free & colour
                    avg = s.neighbour_average(); inner[upd] += omega * (avg[upd] - inner[upd])
            d = np.abs(inner - old).max()
            hist.append(d)
            if d < 1e-6:
                break
        out[method] = hist
        print(f"{method}: {len(hist)} sweeps to 1e-6; V at the centre = {s.V[50, 50]:.4f} V")
    # exact centre value for this square (one side at V0): 0.25 V0 by symmetry (superposition of 4 sides)
    print("exact centre value: 0.2500 V (symmetry: the four sides together give 1 V everywhere)")
    if plot:
        plot.convergence(out)
    return {k: len(v) for k, v in out.items()}


class LaplacePlots:
    """Figures for the page, in the same ink style as tools/plots/em_plots.py."""

    def __init__(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        self.plt = plt
        OUT.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": "#22201b", "text.color": "#22201b",
                             "axes.labelcolor": "#22201b", "xtick.color": "#22201b", "ytick.color": "#22201b", "svg.fonttype": "path"})

    def save(self, fig, name):
        fig.savefig(OUT / f"{name}.svg", transparent=True, bbox_inches="tight", dpi=110)
        self.plt.close(fig)
        print("wrote", (OUT / f"{name}.svg").relative_to(ROOT))

    def capacitor(self, s, xc, yc, w, d):
        plt = self.plt
        fig, ax = plt.subplots(figsize=(8, 5))
        X, Y = np.meshgrid(s.x * 100, s.y * 100)
        im = ax.pcolormesh(X, Y, s.V, cmap="RdBu_r", shading="auto", rasterized=True, vmin=-50, vmax=50)
        ax.contour(X, Y, s.V, levels=np.arange(-45, 50, 5), colors="#22201b", linewidths=0.6)
        Ex, Ey, _ = s.field()
        ax.streamplot(X, Y, Ex, Ey, color="#b8622b", density=1.2, linewidth=0.8, arrowsize=0.8)
        for sign in (1, -1):
            ax.plot([(xc - w / 2) * 100, (xc + w / 2) * 100], [(yc + sign * d / 2) * 100] * 2, color="#22201b", lw=4)
        ax.set_xlim(5, 25); ax.set_ylim(3, 17); ax.set_aspect("equal")
        ax.set_xlabel("x (cm)"); ax.set_ylabel("y (cm)")
        cb = fig.colorbar(im, ax=ax, shrink=0.8); cb.set_label("V (volt)")
        ax.set_title("πυκνωτής με οπλισμούς ±50 V: ισοδυναμικές (μαύρες) και δυναμικές γραμμές (χάλκινες)", fontsize=10)
        self.save(fig, "laplace-capacitor")

    def tip(self, results, E0):
        plt = self.plt
        fig, axs = plt.subplots(1, 2, figsize=(9.5, 4.2))
        for ax, (name, (k, n, s, prof)), title in zip(axs, results.items(), ("ημικύλινδρος r = 5 mm", "λεπίδα 20 mm (σαν static wick)")):
            _, _, E = s.field()
            X, Y = np.meshgrid(s.x * 1000, s.y * 1000)
            Em = np.where(s.fixed, np.nan, E / E0)
            im = ax.pcolormesh(X, Y, Em, cmap="YlOrBr", shading="auto", rasterized=True, vmin=0, vmax=6 if name == "blade" else 2.2)
            ax.contour(X, Y, s.V, levels=np.linspace(500, 11500, 23), colors="#22201b", linewidths=0.5)
            ax.set_xlim(60, 140); ax.set_ylim(0, 50); ax.set_aspect("equal")
            ax.set_title(f"{title}: E ≈ {k:.1f} E₀ πάνω από την κορυφή", fontsize=10)
            ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)")
            cb = fig.colorbar(im, ax=ax, shrink=0.75); cb.set_label("|E| / E₀")
        self.save(fig, "laplace-tip")
        # validation: the half-cylinder profile against the exact solution
        fig, ax = plt.subplots(figsize=(7.5, 3.8))
        dist, num = results["boss"][3]
        R = 0.005
        d = np.linspace(0, dist.max(), 200)
        ax.plot(d * 1e3, 1 + (R / (R + d)) ** 2, color="#22201b", lw=2, label="ακριβής λύση: 1 + R²/(R + s)²")
        ax.plot(dist * 1e3, num, "o", color="#b8622b", ms=4, label="αριθμητική λύση (SOR, h = 0,25 mm)")
        ax.set_xlabel("απόσταση s πάνω από την κορυφή (mm)"); ax.set_ylabel("|E| / E₀")
        ax.set_title("επαλήθευση: ημικύλινδρος σε ομογενές πεδίο", fontsize=11)
        ax.legend(frameon=False); ax.grid(True, alpha=0.4)
        self.save(fig, "laplace-check")

    def convergence(self, out):
        plt = self.plt
        fig, ax = plt.subplots(figsize=(8, 4.2))
        for (m, hist), c, lab in zip(out.items(), ("#8a8577", "#1d5f86", "#b8622b"), ("Jacobi", "Gauss–Seidel", "SOR (ω βέλτιστο)")):
            ax.semilogy(np.arange(1, len(hist) + 1), hist, color=c, lw=2, label=f"{lab}: {len(hist)} επαναλήψεις")
        ax.axhline(1e-6, color="#b23a2a", ls="--", lw=1)
        ax.set_xscale("log"); ax.set_xlabel("επανάληψη (sweep)"); ax.set_ylabel("μέγιστη αλλαγή (V)")
        ax.set_title("σύγκλιση σε πλέγμα 101 × 101", fontsize=11); ax.legend(frameon=False)
        ax.grid(True, alpha=0.4)
        self.save(fig, "laplace-convergence")


if __name__ == "__main__":
    p = LaplacePlots()
    study_capacitor(p)
    study_tip(p)
    study_convergence(p)
