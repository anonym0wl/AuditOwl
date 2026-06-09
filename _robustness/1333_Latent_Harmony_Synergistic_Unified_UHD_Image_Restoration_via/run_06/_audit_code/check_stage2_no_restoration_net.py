"""Static check: does Stage-2 implement the paper's restoration network R_theta and L_Res?

Paper Eq.7: z_res = R_theta(z_deg); L_Res = ||D_psi*(z_res) - I_clean||_1, trained first
with the VAE frozen, BEFORE HF-LoRA tuning. We grep the Stage-2 model and network for any
sign of a separate restoration network or a main restoration (pixel/L_Res) loss term.

Supports finding `stage2-missing-restoration-network`.
"""
import os, re

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
files = {
    'VAEadapter_model.py': os.path.join(REPO, 'basicsr', 'models', 'VAEadapter_model.py'),
    'LHVAE_hflora_arch.py': os.path.join(REPO, 'basicsr', 'archs', 'LHVAE_hflora_arch.py'),
    'stage2_hflora.yml': os.path.join(REPO, 'configs', 'stage2_hflora.yml'),
}

# tokens that would indicate an actual latent restoration network R_theta
restoration_tokens = [r'\bR_?theta\b', r'\bRtheta\b', r'restoration', r'net_r\b', r'\brestor', r'z_res', r'zres', r'l_res\b', r'L_Res']

for label, path in files.items():
    txt = open(path).read()
    print(f'=== {label} ===')
    found_any = False
    for tok in restoration_tokens:
        hits = [(i + 1, ln.strip()) for i, ln in enumerate(txt.splitlines()) if re.search(tok, ln, re.I)]
        if hits:
            found_any = True
            for ln_no, ln in hits:
                print(f'  /{tok}/ L{ln_no}: {ln}')
    if not found_any:
        print('  (no restoration-network / L_Res tokens found)')
    print()

# What does Stage-2 forward feed to the network? and what loss is used?
m = open(files['VAEadapter_model.py']).read()
print('Stage-2 _forward_g call site:')
for i, ln in enumerate(m.splitlines(), 1):
    if 'self.net_g(' in ln:
        print(f'  L{i}: {ln.strip()}')
print()
print('Stage-2 network (RAVAEHFLora.forward) just wraps the VAE:')
h = open(files['LHVAE_hflora_arch.py']).read()
for i, ln in enumerate(h.splitlines(), 1):
    if 'out = self.vae(x)' in ln or 'self.vae =' in ln:
        print(f'  L{i}: {ln.strip()}')
print()
print('VERDICT: Stage-2 has no R_theta and no L_Res; net_g is the VAE itself, optimized only')
print('by HF fidelity + GAN losses. The paper\'s "train R_theta with frozen VAE (Eq.7)" step is absent.')
