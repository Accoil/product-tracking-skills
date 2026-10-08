#!/usr/bin/env python3
"""Check a plugin directory against OpenAI's plugin submission rules.

Limits come from https://developers.openai.com/plugins/deploy/submission-errors
(final directory submission values, which are stricter than upload validation).

Usage: check-openai-package.py <plugin-dir> [repo-root]
Exits non-zero if any check fails. Warnings don't fail the build.
"""
import json
import os
import re
import struct
import sys

root = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else None
errors, warnings = [], []


def fail(msg):
    errors.append(msg)


def limit(label, value, n):
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} is missing or empty")
    elif "\n" in value and n <= 128:
        fail(f"{label} must be one line")
    elif len(value) > n:
        fail(f"{label} is {len(value)} chars (max {n})")


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, None
    fields, key = {}, None
    for line in m.group(1).splitlines():
        top = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if top:
            key = top.group(1)
            fields[key] = top.group(2).strip()
        elif key and line.startswith(" "):
            fields[key] = (fields[key] + " " + line.strip()).strip()
    for k, v in fields.items():
        if v in ("|", ">", "|-", ">-"):
            fields[k] = ""
        fields[k] = re.sub(r"^[|>]-?\s*", "", fields[k]).strip().strip('"')
    return fields, m.group(2)


# --- Manifest ---------------------------------------------------------------
manifest = json.load(open(os.path.join(root, "plugin.json")))
name = manifest.get("name", "")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
    fail(f"plugin name '{name}' must start with a letter/digit, use only [A-Za-z0-9_-], max 64")
if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[\w.]+)?(?:\+[\w.]+)?", manifest.get("version", "")):
    fail("version must be semver")
limit("description", manifest.get("description"), 1024)

openai = manifest.get("extensions", {}).get("com.openai", {})
ui = openai.get("interface", {})
limit("interface.displayName", ui.get("displayName"), 30)
limit("interface.shortDescription", ui.get("shortDescription"), 30)
limit("interface.longDescription", ui.get("longDescription"), 4000)
limit("interface.developerName", ui.get("developerName"), 80)

categories = {"Productivity", "Creativity", "Developer Tools", "Business & Operations",
              "Data & Analytics", "Communication", "Education & Research", "Security",
              "Finance", "Healthcare", "Travel", "Entertainment", "Other"}
if ui.get("category") not in categories:
    fail(f"interface.category '{ui.get('category')}' is not a supported category")

caps = ui.get("capabilities", [])
if len(caps) > 20:
    fail(f"{len(caps)} capabilities (max 20)")
for c in caps:
    limit("capability", c, 120)

prompts = ui.get("defaultPrompt", [])
if len(prompts) > 3:
    fail(f"{len(prompts)} default prompts (max 3)")
if len({p.strip().lower() for p in prompts}) != len(prompts):
    fail("default prompts must be unique")
for p in prompts:
    limit("defaultPrompt", p, 128)
    if "@" in p:
        fail(f"default prompt contains an @mention: {p}")

for key in ("websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"):
    url = ui.get(key)
    if url is not None and not url.startswith("https://"):
        fail(f"interface.{key} must be HTTPS")

for key in ("brandColor", "brandColorDark"):
    if key in ui and not re.fullmatch(r"#[0-9A-Fa-f]{6}", ui[key]):
        fail(f"interface.{key} must be a six-digit hex colour")

for key in ("logo", "composerIcon"):
    path = ui.get(key)
    if not path:
        fail(f"interface.{key} is required")
        continue
    if not path.startswith("./"):
        fail(f"interface.{key} must start with ./")
    full = os.path.join(root, path)
    if not os.path.isfile(full):
        fail(f"interface.{key} file not found: {path}")
        continue
    if os.path.getsize(full) > 5 * 1024 * 1024:
        fail(f"{path} is over 5 MiB")
    size = png_size(full)
    if size is None:
        warnings.append(f"{path} is not a PNG; dimensions not checked")
    else:
        w, h = size
        if w != h or not 48 <= w <= 4096:
            fail(f"{path} is {w}x{h} (must be square, 48-4096 px)")

for key in set(openai) - {"interface", "apps", "hooks", "skills", "mcpServers"}:
    warnings.append(f"extensions.com.openai.{key} is not in OpenAI's documented schema (portal may normalize it)")
if "hooks" in openai or "mcpServers" in openai or "apps" in openai:
    fail("skills-only uploads can't declare hooks, apps or MCP servers")

# --- Skills -----------------------------------------------------------------
skills_dir = os.path.join(root, "skills")
skill_names = set()
for entry in sorted(os.listdir(skills_dir)):
    path = os.path.join(skills_dir, entry)
    if entry.startswith("."):
        fail(f"hidden entry in skills/: {entry}")
        continue
    if os.path.islink(path):
        fail(f"skills/{entry} is a symlink")
        continue
    if not os.path.isdir(path):
        warnings.append(f"skills/{entry} is a file and will be ignored")
        continue
    skill_md = os.path.join(path, "SKILL.md")
    if not os.path.isfile(skill_md):
        fail(f"skills/{entry} has no SKILL.md")
        continue
    fm, body = frontmatter(open(skill_md, encoding="utf-8").read())
    if fm is None:
        fail(f"skills/{entry}/SKILL.md has no front matter")
        continue
    sname = fm.get("name", "")
    if not sname:
        fail(f"skills/{entry}: name is missing")
    if sname in skill_names:
        fail(f"duplicate skill name {sname}")
    skill_names.add(sname)
    if len(f"{name}:{sname}") > 64:
        fail(f"'{name}:{sname}' is {len(name) + 1 + len(sname)} chars (max 64)")
    limit(f"skills/{entry} description", fm.get("description"), 1024)
    if not body.strip():
        fail(f"skills/{entry}/SKILL.md body is empty")

    agent = os.path.join(path, "agents", "openai.yaml")
    if os.path.isfile(agent):
        text = open(agent, encoding="utf-8").read()
        for field in ("display_name", "short_description"):
            if not re.search(rf"^\s+{field}:\s*\S", text, re.M):
                fail(f"skills/{entry}/agents/openai.yaml: interface.{field} is required")
        for product in re.findall(r"^\s+-\s*(\S+)", text.split("products:", 1)[1] if "products:" in text else "", re.M):
            if product.strip("\"'") not in ("CHAT", "CODEX"):
                fail(f"skills/{entry}/agents/openai.yaml: unknown product {product}")

# --- Archive-level ----------------------------------------------------------
files = 0
for dirpath, dirnames, filenames in os.walk(root):
    rel = os.path.relpath(dirpath, root)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    for d in dirnames:
        if os.path.islink(os.path.join(dirpath, d)):
            fail(f"symlink: {os.path.join(rel, d)}")
    for f in filenames:
        files += 1
        full = os.path.join(dirpath, f)
        if os.path.islink(full):
            fail(f"symlink: {os.path.join(rel, f)}")
        if f.startswith(".") or f in ("Thumbs.db",):
            fail(f"junk or hidden file: {os.path.join(rel, f)}")
        if depth + 2 > 20:
            fail(f"path too deep: {os.path.join(rel, f)}")
    for d in dirnames:
        if d.startswith(".") or d == "__MACOSX":
            fail(f"hidden directory: {os.path.join(rel, d)}")
if files > 5000:
    fail(f"{files} files (max 5000)")

# Claude-only content that OpenAI asks you to remove.
for dirpath, _, filenames in os.walk(skills_dir):
    for f in filenames:
        if not f.endswith(".md"):
            continue
        full = os.path.join(dirpath, f)
        for n, line in enumerate(open(full, encoding="utf-8"), 1):
            if re.search(r"\bClaude\b|\bAnthropic\b|AskUserQuestion|TodoWrite|CLAUDE\.md", line):
                warnings.append(f"Claude-specific wording: {os.path.relpath(full, root)}:{n}")

# --- Version consistency with the Claude manifests --------------------------
if repo:
    version = manifest.get("version")
    for rel in (".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"):
        p = os.path.join(repo, rel)
        if os.path.isfile(p):
            found = set(re.findall(r'"version":\s*"([^"]+)"', open(p).read()))
            if found != {version}:
                fail(f"{rel} version {sorted(found)} doesn't match plugin.json {version}")

for w in warnings:
    print(f"warn: {w}")
for e in errors:
    print(f"FAIL: {e}")
print(f"{len(skill_names)} skills, {files} files: "
      + ("all checks passed" if not errors else f"{len(errors)} check(s) failed"))
sys.exit(1 if errors else 0)
