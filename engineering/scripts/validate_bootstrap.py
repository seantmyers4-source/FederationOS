#!/usr/bin/env python3
import json, pathlib, re, sys
root=pathlib.Path(__file__).resolve().parents[2]
required=["README.md","CONTRIBUTING.md","SECURITY.md","LICENSE",".gitignore",".github/CODEOWNERS",".github/pull_request_template.md","governance/repository-identity.json","governance/repository-governance.json","governance/authority-ownership-map.json","governance/directory-ownership-map.json","archive/archive-manifest.json"]
dirs=["governance","architecture","registry","engineering","qa","pmo","runtime","references","templates","docs","archive"]
errors=[]
for p in required:
    if not (root/p).is_file(): errors.append(f"missing required file: {p}")
for d in dirs:
    if not (root/d).is_dir(): errors.append(f"missing directory: {d}")
for p in root.rglob("*.json"):
    try: json.loads(p.read_text())
    except Exception as e: errors.append(f"invalid JSON {p.relative_to(root)}: {e}")
for p in root.rglob("*"):
    if p.is_file() and ".git" not in p.parts:
        s=p.read_text(errors="ignore")
        if re.search(r"(?i)(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)",s): errors.append(f"possible secret: {p.relative_to(root)}")
        if re.search(r"(?i)(medical record|social security number|bank account number)",s): errors.append(f"possible prohibited sensitive content: {p.relative_to(root)}")
for p in root.rglob("*.json"):
    s=p.read_text()
    if "cross-os" in p.name and '"canonical_copy":false' not in s.replace(" ",""): errors.append(f"cross-OS manifest must prohibit canonical copy: {p.relative_to(root)}")
if errors:
    print("\n".join(errors)); sys.exit(1)
print("bootstrap validation passed")
