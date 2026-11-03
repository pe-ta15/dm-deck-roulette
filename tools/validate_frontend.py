from pathlib import Path
import re
import sys

import tinycss2

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
errors = []

def fail(message):
    errors.append(message)

styles = re.findall(r"<style\b[^>]*>(.*?)</style\s*>", HTML, re.I | re.S)
scripts = re.findall(r"<script\b[^>]*>(.*?)</script\s*>", HTML, re.I | re.S)
if len(styles) != 1:
    fail(f"Expected one style block, found {len(styles)}")
if len(scripts) != 1:
    fail(f"Expected one application script, found {len(scripts)}")

CSS = styles[0] if len(styles) == 1 else ""
JS = scripts[0] if len(scripts) == 1 else ""

# Parse CSS at every nesting level. A brace count alone cannot detect malformed
# at-rules or declarations, which allowed an incomplete media query to survive.
duplicate_rules = {}

def inspect_rules(rules, context):
    for rule in rules:
        if rule.type == "error":
            fail(f"CSS parse error in {context}: {rule.message}")
            continue
        if rule.type == "at-rule":
            name = rule.lower_at_keyword
            if rule.content is None:
                continue
            if name in {"media", "supports", "layer", "container", "document", "keyframes", "-webkit-keyframes"}:
                nested = tinycss2.parse_rule_list(
                    rule.content, skip_whitespace=True, skip_comments=True
                )
                prelude = tinycss2.serialize(rule.prelude).strip()
                inspect_rules(nested, f"{context} -> @{name} {prelude}")
            else:
                declarations = tinycss2.parse_declaration_list(
                    rule.content, skip_whitespace=True, skip_comments=True
                )
                for item in declarations:
                    if item.type == "error":
                        fail(f"CSS declaration error in {context} -> @{name}: {item.message}")
        elif rule.type == "qualified-rule":
            selector = tinycss2.serialize(rule.prelude).strip()
            declarations = tinycss2.parse_declaration_list(
                rule.content, skip_whitespace=True, skip_comments=True
            )
            normalized = tuple(sorted(
                (item.lower_name, tinycss2.serialize(item.value).strip(), item.important)
                for item in declarations if item.type == "declaration"
            ))
            if normalized:
                duplicate_rules.setdefault((context, selector, normalized), []).append(rule.source_line)
            for item in declarations:
                if item.type == "error":
                    fail(f"CSS declaration error for {selector}: {item.message}")
                elif (
                    "#result" in selector
                    and (":before" in selector or ":after" in selector)
                    and item.type == "declaration"
                    and item.lower_name in {"background", "background-image"}
                    and "radial-gradient(" in tinycss2.serialize(item.value).lower()
                ):
                    fail(f"Radial result halo is not allowed: {selector}")

if CSS:
    rules = tinycss2.parse_stylesheet(CSS, skip_whitespace=True, skip_comments=True)
    inspect_rules(rules, "stylesheet")

# Identical selector/declaration blocks are reported for manual review.
# They are not automatically removed: cascade order and grouped selectors need review.
duplicate_count = 0
for (context, selector, _), occurrences in duplicate_rules.items():
    if len(occurrences) > 1:
        duplicate_count += 1
        line_list = ", ".join(map(str, occurrences))
        print(f"CSS duplicate review: {context}: {selector} at lines {line_list} ({len(occurrences)} copies)")

# Regression guards for the exact handoff effects that previously escaped review.
for forbidden in ("case-burst", "ruptureWave", "resultShockwave", "revealFlash"):
    if forbidden in HTML:
        fail(f"Obsolete transition layer remains: {forbidden}")

if HTML.count('id="deckCase"') != 1:
    fail("Expected exactly one shared deck-case element")

if JS:
    order = [
        "const selectedDeck = await requestDraw()",
        "const presentation = drawPresentation()",
        "applyPresentation(presentation);",
        "await playManaSequence(stopSelectionOrbit)",
        "await playCaseOpeningSequence()",
        "await showKeyCards(deck)",
    ]
    positions = [JS.find(token) for token in order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        fail("Draw request / animation / result handoff order has changed")
    # The presentation lottery must be independent, exhaustive, and use the agreed weights.
    expected_weights = {
        "normal": 7200,
        "premium": 1800,
        "anomaly": 700,
        "special": 250,
        "ultimate": 50,
    }
    for presentation, weight in expected_weights.items():
        pattern = rf'\{{\s*id:\s*"{presentation}"\s*,\s*className:\s*"presentation-[\w-]+"\s*,\s*weight:\s*{weight}\s*\}}'
        if not re.search(pattern, JS):
            fail(f"Missing or incorrect presentation weight: {presentation}={weight}")
    if "PRESENTATION_TOTAL_WEIGHT = 10000" not in JS:
        fail("Presentation weights must use a 10,000-ticket scale")
    presentation_fn = JS[JS.find("function drawPresentation()"):JS.find("function applyPresentation(")]
    if "recentDrawnDeckIds" in presentation_fn:
        fail("Presentation lottery must not depend on recent deck results")
    if "selectionOrbit?.handoff?.()" not in JS:
        fail("Selection orbit must hand off its current position to mana absorption")
    if "stopSelectionOrbit.stop()" not in JS:
        fail("Selection orbit controller must be stopped during final cleanup")

    if JS.count('deckCase.style.opacity = "0"') != 1:
        fail("Case fade-out must have one controlled entry point")
    show_start = JS.find("async function showKeyCards(deck)")
    show_end = JS.find("function loadDecks()", show_start)
    show_body = JS[show_start:show_end] if show_start >= 0 and show_end > show_start else ""
    if 'deckCase.style.opacity = "0"' not in show_body:
        fail("Case fade-out must remain inside showKeyCards")
    if show_body.find('deckCase.style.opacity = "0"') > show_body.find("await sleep(160)") and "await sleep(160)" in show_body:
        fail("Case fade-out must begin before its synchronized wait")

# The case lid must illuminate in lockstep with the body, without its former
# independent pulse or an immediate full-color fill on the inner lid.
if "lidChargeBeat" in CSS:
    fail("Obsolete independent lid charge animation remains")
lid_sync = (
    ".deck-case .case-lid,\n"
    ".deck-case .case-lid-inner,\n"
    ".deck-case .case-lid-front" 
)
if lid_sync not in CSS or "transition:filter 1.2s ease,box-shadow 1.2s ease,border-color 1.2s ease!important;" not in CSS:
    fail("Lid glow must use the synchronized 1.2s case-light transition")
if re.search(r"\.deck-case\.civ-charging \.case-lid-inner\s*\{[^}]*\bbackground\s*:", CSS, re.S):
    fail("Lid inner surface must not switch to full civilization color instantly")

# Duplicate keyframe names can silently replace earlier animation definitions.
keyframes = re.findall(r"@(?:-webkit-)?keyframes\s+([\w-]+)", CSS)
duplicates = sorted({name for name in keyframes if keyframes.count(name) > 1})
if duplicates:
    fail("Duplicate keyframe definitions: " + ", ".join(duplicates))

if errors:
    print("Frontend validation failed:")
    for error in errors:
        print(" - " + error)
    sys.exit(1)

print("Frontend validation passed")
print(f" - CSS parsed successfully ({len(CSS)} characters)")
print(" - No obsolete circular / full-screen transition layers")
print(" - Draw-result handoff order and case fade timing verified")
print(" - Keyframe names are unique")
