"""Static checks (no torch import): (1) stage2 config references arch type 'RAVAE'
which is not registered (only 'RAVAE_EQ' exists) -> stage2 build crashes;
(2) the Stage-2 forward path (RAVAEHFLora.forward / VAEadapter._forward_g) never
invokes a restoration network R_theta. Supports findings ravae-type-not-registered
and missing-restoration-network-rtheta. Read-only AST/text scan."""
import ast
import os
import re

REPO = os.path.join(os.path.dirname(__file__), '..', 'code', 'lyd-2022__Latent-Harmony')
REPO = os.path.abspath(REPO)
OUT = os.path.join(os.path.dirname(__file__), 'out')
os.makedirs(OUT, exist_ok=True)

lines = []

# (1) Collect every @ARCH_REGISTRY.register() class name across archs/
registered = set()
for root, _, files in os.walk(os.path.join(REPO, 'basicsr', 'archs')):
    for f in files:
        if not f.endswith('.py'):
            continue
        src = open(os.path.join(root, f)).read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    txt = ast.dump(dec)
                    if 'ARCH_REGISTRY' in txt and 'register' in txt:
                        registered.add(node.name)
lines.append(f'registered_arch_classes={sorted(registered)}')

# config references
cfg2 = open(os.path.join(REPO, 'configs', 'stage2_hflora.yml')).read()
refs = re.findall(r'type:\s*([A-Za-z_0-9]+)', cfg2)
lines.append(f'stage2_config_type_refs={refs}')
ravae_referenced = 'RAVAE' in refs
ravae_registered = 'RAVAE' in registered
lines.append(f'RAVAE_referenced_in_stage2={ravae_referenced}; RAVAE_registered={ravae_registered}')
lines.append(f'VERDICT_registry_mismatch={ravae_referenced and not ravae_registered}')

# (2) Search whole repo for any token that would be a separate restoration net
restore_tokens = ['SFHformer', 'NAFNet', 'class Restormer', 'net_restore', 'R_theta',
                  'restore_net', 'self.net_r', 'RestorationNet', 'rtheta']
hits = {}
for root, _, files in os.walk(os.path.join(REPO, 'basicsr')):
    for f in files:
        if not f.endswith('.py'):
            continue
        src = open(os.path.join(root, f)).read()
        for tok in restore_tokens:
            if tok in src:
                hits.setdefault(tok, []).append(os.path.relpath(os.path.join(root, f), REPO))
lines.append(f'restoration_net_token_hits={hits}')
lines.append(f'VERDICT_no_standalone_restoration_net={len(hits)==0}')

# Confirm RAVAEHFLora.forward only calls self.vae(...) (no restoration net)
hflora = open(os.path.join(REPO, 'basicsr', 'archs', 'LHVAE_hflora_arch.py')).read()
fwd_calls_vae_only = ('out = self.vae(x)' in hflora) and ('R' not in re.findall(r'def forward.*?raise RuntimeError', hflora, re.S)[0].replace('RuntimeError','').replace('Rθ','') if re.findall(r'def forward.*?raise RuntimeError', hflora, re.S) else False)
lines.append(f'RAVAEHFLora_forward_calls_vae_only={"out = self.vae(x)" in hflora}')

with open(os.path.join(OUT, 'registry_and_rtheta.txt'), 'w') as fh:
    fh.write('\n'.join(lines) + '\n')
print('\n'.join(lines))
