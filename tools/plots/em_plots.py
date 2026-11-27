"""Static figures for the electromagnetism extras (deep/em-*.md).

    python tools/plots/em_plots.py          # writes every figure to assets/img/em/*.svg
    python tools/plots/em_plots.py skin     # only the figures whose name contains "skin"

Each figure is one method of EMPlots. To change a figure, change its numbers here and run the script again.
The style (ink colours on transparent background) matches the notebook pages of the site.
The Laplace-solver figures are made by tools/em/laplace.py, not here.
"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "img" / "em"

# Physical constants (SI)
MU0 = 4e-7 * math.pi
EPS0 = 8.8541878128e-12
C0 = 1 / math.sqrt(MU0 * EPS0)


class EMPlots:
    """Holds the shared style and writes one SVG per method."""

    INK, COPPER, BLUE, RED, GREEN, GREY = "#22201b", "#b8622b", "#1d5f86", "#b23a2a", "#2f7d4f", "#8a8577"

    def __init__(self, out=OUT):
        self.out = out
        self.out.mkdir(parents=True, exist_ok=True)
        plt.rcParams.update({
            "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": self.INK, "axes.labelcolor": self.INK,
            "xtick.color": self.INK, "ytick.color": self.INK, "text.color": self.INK, "axes.grid": True,
            "grid.color": "#b9b2a0", "grid.linewidth": 0.5, "grid.alpha": 0.6, "axes.spines.top": False,
            "axes.spines.right": False, "legend.frameon": False, "svg.fonttype": "path",
        })

    def save(self, fig, name):
        fig.savefig(self.out / f"{name}.svg", transparent=True, bbox_inches="tight")
        plt.close(fig)
        print("wrote", (self.out / f"{name}.svg").relative_to(ROOT))

    # ---------------------------------------------------------------- 1. Poynting
    def poynting(self):
        """Power flow in a coaxial cable: |S| between the conductors, and S pointing into a resistive wire."""
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4.2))
        # (a) coax cross-section, V = 28 V, I = 10 A, a = 1 mm, b = 3.5 mm: S = V I / (2 pi r^2 ln(b/a))
        a, b, V, I = 1e-3, 3.5e-3, 28.0, 10.0
        x = np.linspace(-4.5e-3, 4.5e-3, 400)
        X, Y = np.meshgrid(x, x)
        R = np.hypot(X, Y)
        S = np.where((R > a) & (R < b), V * I / (2 * np.pi * R**2 * math.log(b / a)), np.nan)
        im = a1.pcolormesh(X * 1e3, Y * 1e3, S / 1e6, cmap="YlOrBr", shading="auto", rasterized=True)
        for r, lw in ((a, 2), (b, 2)):
            a1.add_patch(plt.Circle((0, 0), r * 1e3, fill=False, color=self.COPPER, lw=lw))
        a1.set_aspect("equal"); a1.grid(False)
        a1.set_title("(α) ομοαξονικό: ροή ισχύος |S|", fontsize=11)
        a1.set_xlabel("x (mm)"); a1.set_ylabel("y (mm)")
        cb = fig.colorbar(im, ax=a1, shrink=0.85); cb.set_label("|S| (MW/m²)")
        # (b) side view of a resistive wire: E along the wire, B around it, S = E x B / mu0 points inwards
        a2.set_xlim(0, 10); a2.set_ylim(-4, 4); a2.grid(False); a2.set_xticks([]); a2.set_yticks([])
        a2.add_patch(plt.Rectangle((0.5, -0.5), 9, 1, color=self.COPPER, alpha=0.35))
        a2.annotate("", xy=(9.3, 0), xytext=(0.7, 0), arrowprops=dict(arrowstyle="->", color=self.BLUE, lw=2))
        a2.text(5, 0.05, "E (κατά μήκος)", ha="center", va="bottom", color=self.BLUE)
        for xi in np.linspace(1.2, 8.8, 7):
            for s in (1, -1):
                a2.annotate("", xy=(xi, s * 0.65), xytext=(xi, s * 3.2), arrowprops=dict(arrowstyle="->", color=self.RED, lw=1.6))
        a2.text(5, 3.5, "S = E × B / μ₀ μπαίνει από έξω", ha="center", color=self.RED)
        a2.text(5, -3.75, "η ισχύς I²R φτάνει στο σύρμα μέσα από το πεδίο", ha="center", color=self.INK, fontsize=10)
        a2.set_title("(β) αντιστατικό σύρμα: πλάγια όψη", fontsize=11)
        for sp in a2.spines.values():
            sp.set_visible(False)
        self.save(fig, "poynting")

    # ---------------------------------------------------------------- 2. Skin effect
    MATERIALS = {  # name: (resistivity in ohm·m, relative permeability)
        "Χαλκός": (1.68e-8, 1), "Αλουμίνιο": (2.65e-8, 1), "Ανοξείδωτος χάλυβας": (7.2e-7, 1), "Μαλακός χάλυβας (μr≈100)": (1.6e-7, 100),
    }

    @staticmethod
    def skin_depth(rho, mur, f):
        return np.sqrt(2 * rho / (2 * np.pi * f * MU0 * mur))

    def skin(self):
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.2))
        f = np.logspace(1, 7, 300)
        cols = [self.COPPER, self.BLUE, self.GREY, self.INK]
        for (name, (rho, mur)), c in zip(self.MATERIALS.items(), cols):
            a1.loglog(f, self.skin_depth(rho, mur, f) * 1e3, color=c, lw=2, label=name)
        for fx, lab in ((50, "50 Hz"), (400, "400 Hz")):
            a1.axvline(fx, color=self.RED, ls="--", lw=1)
            a1.text(fx * 1.1, 20, lab, color=self.RED, rotation=90, va="bottom")
        a1.axvspan(1e3, 1e7, color=self.GREEN, alpha=0.07)
        a1.text(1e5, 40, "περιοχή NDT δινορρευμάτων", color=self.GREEN, ha="center", fontsize=9)
        a1.set_xlabel("συχνότητα f (Hz)"); a1.set_ylabel("βάθος διείσδυσης δ (mm)")
        a1.set_ylim(1e-3, 1e2); a1.legend(fontsize=9, loc="lower left")
        a1.set_title("βάθος διείσδυσης δ = √(2ρ / ωμ)", fontsize=11)
        rho = self.MATERIALS["Αλουμίνιο"][0]
        x = np.linspace(0, 6, 300)
        for fx, c in ((400, self.COPPER), (10e3, self.BLUE), (100e3, self.RED)):
            d = self.skin_depth(rho, 1, fx) * 1e3
            a2.plot(x, np.exp(-x / d), color=c, lw=2, label=f"{fx/1e3:g} kHz (δ = {d:.2f} mm)" if fx >= 1e3 else f"{fx:g} Hz (δ = {d:.2f} mm)")
        a2.set_xlabel("βάθος από την επιφάνεια (mm)"); a2.set_ylabel("|J| / |J επιφάνειας|")
        a2.set_title("αλουμίνιο: πυκνότητα ρεύματος", fontsize=11); a2.legend(fontsize=9)
        self.save(fig, "skin")

    # ---------------------------------------------------------------- 3. Hysteresis
    def hysteresis(self):
        """Simple tanh model of a hysteresis loop: B = Bs tanh((H ± Hc)/H0) + mu0 H."""
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.2))
        for ax, (title, Bs, Hc, H0, Hmax, unit) in zip((a1, a2), (
                ("μαλακό υλικό (πυρήνας μετασχηματιστή)", 1.6, 40, 60, 600, 1),
                ("σκληρό υλικό (μόνιμος μαγνήτης)", 1.2, 9e4, 4e4, 3.5e5, 1e3))):
            H = np.linspace(-Hmax, Hmax, 600)
            up = Bs * np.tanh((H - Hc) / H0) + MU0 * H
            dn = Bs * np.tanh((H + Hc) / H0) + MU0 * H
            ax.plot(H / unit, up, color=self.COPPER, lw=2)
            ax.plot(H / unit, dn, color=self.COPPER, lw=2)
            ax.fill_between(H / unit, up, dn, color=self.COPPER, alpha=0.12)
            Br = Bs * np.tanh(Hc / H0)
            ax.plot([0], [Br], "o", color=self.BLUE); ax.annotate(f"Br ≈ {Br:.2f} T", (0, Br), (Hmax / unit * 0.15, Br * 0.55), color=self.BLUE,
                                                                     arrowprops=dict(arrowstyle="->", color=self.BLUE))
            ax.plot([-Hc / unit], [0], "o", color=self.RED)
            ax.annotate(f"−Hc = −{Hc/unit:g} {'A/m' if unit == 1 else 'kA/m'}", (-Hc / unit, 0), (-Hmax / unit * 0.95, -Bs * 0.55),
                        color=self.RED, arrowprops=dict(arrowstyle="->", color=self.RED))
            ax.axhline(0, color=self.INK, lw=0.8); ax.axvline(0, color=self.INK, lw=0.8)
            ax.set_xlabel("H (A/m)" if unit == 1 else "H (kA/m)"); ax.set_ylabel("B (T)")
            ax.set_title(title, fontsize=11)
        self.save(fig, "hysteresis")

    # ---------------------------------------------------------------- 4. Paschen
    PASCHEN_A, PASCHEN_B, GAMMA = 15.0, 365.0, 0.01   # air: A in 1/(cm·Torr), B in V/(cm·Torr), secondary emission

    @classmethod
    def paschen_v(cls, pd):
        """Breakdown voltage (V) of air for pd in Torr·cm (valid only to the right of the asymptote)."""
        k = math.log(math.log(1 + 1 / cls.GAMMA))
        return cls.PASCHEN_B * pd / (np.log(cls.PASCHEN_A * pd) - k)

    @staticmethod
    def isa_pressure_hpa(h):
        """International Standard Atmosphere pressure at altitude h (m), up to 20 km."""
        return 1013.25 * (1 - 2.25577e-5 * h) ** 5.25588 if h <= 11000 else 226.32 * math.exp(-(h - 11000) / 6341.6)

    def paschen(self):
        fig, ax = plt.subplots(figsize=(8, 4.6))
        k = math.log(math.log(1 + 1 / self.GAMMA))
        pd = np.logspace(math.log10(math.exp(k) / self.PASCHEN_A * 1.05), 3, 600)
        ax.loglog(pd, self.paschen_v(pd), color=self.COPPER, lw=2.2, label="αέρας (νόμος Paschen)")
        pdm = math.e * math.log(1 + 1 / self.GAMMA) / self.PASCHEN_A
        ax.plot([pdm], [self.paschen_v(pdm)], "o", color=self.RED)
        ax.annotate(f"ελάχιστο ≈ {self.paschen_v(pdm):.0f} V", (pdm, self.paschen_v(pdm)), (pdm * 3, 140), color=self.RED,
                    arrowprops=dict(arrowstyle="->", color=self.RED))
        gap_cm = 0.1
        for h, c in ((0, self.INK), (10000, self.BLUE), (20000, self.GREEN)):
            p = self.isa_pressure_hpa(h) * 0.750062 * gap_cm
            ax.plot([p], [self.paschen_v(p)], "s", color=c, ms=7, label=f"διάκενο 1 mm σε {h/1000:g} km: {self.paschen_v(p):.0f} V")
        ax.axhline(540, color=self.GREY, ls="--", lw=1)
        ax.text(1.2, 600, "540 V (±270 V DC)", color=self.GREY, fontsize=9)
        ax.set_xlabel("p · d (Torr · cm)"); ax.set_ylabel("τάση διάσπασης (V)")
        ax.set_ylim(100, 1e5); ax.legend(fontsize=9, loc="upper left")
        self.save(fig, "paschen")

    # ---------------------------------------------------------------- 5. Lightning
    LIGHTNING_A = (218810.0, 11354.0, 647265.0)   # SAE ARP5412 current component A: I0, alpha, beta

    def lightning(self):
        I0, a, b = self.LIGHTNING_A
        t = np.logspace(-8, -3.3, 800)
        i = I0 * (np.exp(-a * t) - np.exp(-b * t))
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4))
        a1.semilogx(t * 1e6, i / 1e3, color=self.COPPER, lw=2.2)
        k = i.argmax()
        a1.plot(t[k] * 1e6, i[k] / 1e3, "o", color=self.RED)
        a1.annotate(f"κορυφή {i[k]/1e3:.0f} kA στα {t[k]*1e6:.1f} μs", (t[k] * 1e6, i[k] / 1e3), (0.02, 120), color=self.RED,
                    arrowprops=dict(arrowstyle="->", color=self.RED))
        a1.set_xlabel("χρόνος (μs)"); a1.set_ylabel("ρεύμα (kA)")
        a1.set_title("τυποποιημένο ρεύμα κεραυνού (component A)", fontsize=11)
        di = np.gradient(i, t)
        a2.semilogx(t * 1e6, di / 1e9, color=self.BLUE, lw=2.2)
        a2.set_xlabel("χρόνος (μs)"); a2.set_ylabel("di/dt (kA/μs)")
        a2.set_title("ρυθμός μεταβολής: η αιτία των επαγόμενων τάσεων", fontsize=11)
        self.save(fig, "lightning")

    # ---------------------------------------------------------------- 6. Antennas
    @staticmethod
    def dipole_pattern(theta, L_over_lambda):
        """Far-field |E| of a centre-fed thin dipole of length L, normalised to 1."""
        kl2 = math.pi * L_over_lambda
        with np.errstate(divide="ignore", invalid="ignore"):
            F = np.abs((np.cos(kl2 * np.cos(theta)) - math.cos(kl2)) / np.sin(theta))
        F = np.nan_to_num(F)
        return F / F.max()

    def antenna(self):
        th = np.linspace(1e-4, 2 * np.pi - 1e-4, 1000)
        fig, axs = plt.subplots(1, 3, figsize=(11, 4), subplot_kw={"projection": "polar"})
        fig.subplots_adjust(wspace=0.45)
        for ax, L, c in zip(axs, (0.1, 0.5, 1.5), (self.GREY, self.COPPER, self.BLUE)):
            ax.plot(th, self.dipole_pattern(th, L) ** 2, color=c, lw=2)
            ax.set_theta_zero_location("N"); ax.set_rticks([0.5, 1]); ax.set_yticklabels([]); ax.set_thetagrids([0, 90, 180, 270], ["0°", "90°", "180°", ""])
            ax.set_title(f"L = {L:g} λ", fontsize=11, pad=12)
            ax.plot([0, 0], [0, 0.25], color=self.INK, lw=3); ax.plot([math.pi, math.pi], [0, 0.25], color=self.INK, lw=3)
        fig.suptitle("διάγραμμα ισχύος διπόλου (η κεραία είναι κατακόρυφη)", fontsize=11)
        self.save(fig, "antenna")

    # ---------------------------------------------------------------- 7. TDR
    def tdr(self):
        """Ideal step TDR on a 50-ohm cable, velocity factor 0.7, source matched (incident level 0.5)."""
        vf, Z0 = 0.7, 50.0
        v = vf * C0
        d = np.linspace(-1, 25, 2000)            # displayed as distance = v t / 2
        fig, ax = plt.subplots(figsize=(8.5, 4.4))
        cases = (("ανοιχτό κύκλωμα (κομμένο) στα 12 m", 12, [(12, 1e12)], self.RED),
                 ("βραχυκύκλωμα στα 18 m", 18, [(18, 0.0)], self.BLUE),
                 ("φθαρμένη μόνωση στα 7 m (40 Ω σε 0,3 m), τέλος σωστά τερματισμένο", 22, [(7, 40.0)], self.COPPER))
        for k, (label, end, faults, c) in enumerate(cases):
            V = np.where(d >= 0, 0.5, 0.0)
            for pos, Zl in faults:
                g = (Zl - Z0) / (Zl + Z0)
                if Zl in (0.0, 1e12):
                    V = V + np.where(d >= pos, 0.5 * g, 0)
                else:                                    # short section: reflection at the start, opposite one at its end
                    V = V + np.where((d >= pos) & (d < pos + 0.3), 0.5 * g, 0)
            ax.plot(d, V + 0.0 * k, color=c, lw=2, label=label)
        ax.set_xlabel("απόσταση στο καλώδιο (m) = v · t / 2, με v = 0,7 c")
        ax.set_ylabel("τάση στην αρχή του καλωδίου (V)")
        ax.set_ylim(-0.1, 1.1); ax.legend(fontsize=9, loc=(0.02, 0.62))
        ax.set_title("TDR: βήμα 1 V σε καλώδιο 50 Ω", fontsize=11)
        ax2 = ax.secondary_xaxis("top", functions=(lambda x: 2 * x / v * 1e9, lambda tn: tn * 1e-9 * v / 2))
        ax2.set_xlabel("χρόνος επιστροφής (ns)")
        self.save(fig, "tdr")

    # ---------------------------------------------------------------- 8. Shielding
    def shielding(self):
        """Plane-wave shielding effectiveness SE = A + R (Schelkunoff, far field, no apertures)."""
        f = np.logspace(3, 10, 400)
        fig, ax = plt.subplots(figsize=(8.5, 4.4))
        sig_cu = 1 / 1.68e-8
        for name, rho, mur, t, c in (("αλουμίνιο 0,1 mm", 2.65e-8, 1, 1e-4, self.BLUE), ("αλουμίνιο 1 mm", 2.65e-8, 1, 1e-3, self.COPPER),
                                     ("χαλκός 0,02 mm (μανδύας καλωδίου)", 1.68e-8, 1, 2e-5, self.RED)):
            delta = self.skin_depth(rho, mur, f)
            A = 8.686 * t / delta
            sr = (1 / rho) / sig_cu
            R = 168 - 10 * np.log10(mur * f / sr)
            ax.semilogx(f, A + R, color=c, lw=2, label=name)
            ax.semilogx(f, A, color=c, lw=1, ls=":")
        ax.set_ylim(0, 400)
        ax.set_xlabel("συχνότητα (Hz)"); ax.set_ylabel("αποτελεσματικότητα θωράκισης (dB)")
        ax.set_title("θωράκιση επίπεδου κύματος: σύνολο (συνεχής), μόνο απορρόφηση (διακεκομμένη)", fontsize=10)
        ax.text(2e3, 20, "σε κοντινό μαγνητικό πεδίο χαμηλής συχνότητας\nη ανάκλαση είναι πολύ μικρότερη", fontsize=9, color=self.GREY)
        ax.legend(fontsize=9, loc="upper left")
        self.save(fig, "shielding")

    # ---------------------------------------------------------------- 9. Relativity (schematic)
    def relativity(self):
        fig, axs = plt.subplots(2, 1, figsize=(8.5, 4.4))
        for ax, title, sp_pos, sp_neg, vp, vn in (
                (axs[0], "σύστημα εργαστηρίου: σύρμα ουδέτερο, φορτίο q κινείται με v", 1.0, 1.0, 0, 1),
                (axs[1], "σύστημα του φορτίου q: τα + κινούνται (συστολή → πυκνότερα), τα − πιο αραιά → καθαρό +", 0.86, 1.16, -1, 0)):
            ax.set_xlim(0, 12); ax.set_ylim(-1.6, 1.6); ax.axis("off"); ax.set_title(title, fontsize=10, loc="left")
            ax.add_patch(plt.Rectangle((0, -0.45), 12, 0.9, color=self.COPPER, alpha=0.18))
            for x in np.arange(0.4, 12, sp_pos):
                ax.text(x, 0.12, "+", color=self.RED, ha="center", va="center", fontsize=13, fontweight="bold")
            for x in np.arange(0.4 + sp_neg / 2, 12, sp_neg):
                ax.text(x, -0.18, "−", color=self.BLUE, ha="center", va="center", fontsize=13, fontweight="bold")
            ax.text(6, 1.15, "● q", color=self.INK, ha="center", fontsize=12)
            if vn:
                ax.annotate("", xy=(4, -0.75), xytext=(2.2, -0.75), arrowprops=dict(arrowstyle="->", color=self.BLUE))
                ax.text(4.2, -0.8, "ηλεκτρόνια, v", color=self.BLUE, va="center", fontsize=9)
                ax.annotate("", xy=(7.8, 1.15), xytext=(6.4, 1.15), arrowprops=dict(arrowstyle="->", color=self.INK))
            if vp:
                ax.annotate("", xy=(2.2, -0.75), xytext=(4, -0.75), arrowprops=dict(arrowstyle="->", color=self.RED))
                ax.text(4.2, -0.8, "ιόντα, −v", color=self.RED, va="center", fontsize=9)
        self.save(fig, "relativity")


if __name__ == "__main__":
    plots = EMPlots()
    names = ["poynting", "skin", "hysteresis", "paschen", "lightning", "antenna", "tdr", "shielding", "relativity"]
    want = sys.argv[1:]
    for n in names:
        if not want or any(w in n for w in want):
            getattr(plots, n)()
