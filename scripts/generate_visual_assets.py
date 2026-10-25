"""Generator for high-resolution, light-theme enterprise graphics and LinkedIn showcase images."""

import os
from PIL import Image, ImageDraw, ImageFont


def get_font(name: str, size: int):
    """Safely load Windows system fonts with fallback to default."""
    try:
        return ImageFont.truetype(name, size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def draw_card(draw, x1, y1, x2, y2, fill, outline="#E2E8F0", radius=16, shadow=True):
    """Draw modern rounded card with subtle drop shadow."""
    if shadow:
        for offset in range(4, 0, -1):
            alpha_color = "#F1F5F9" if offset > 2 else "#E2E8F0"
            draw.rounded_rectangle([x1 + offset, y1 + offset, x2 + offset, y2 + offset], radius=radius, fill=alpha_color)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=2)


def draw_badge(draw, x, y, text, font, fill="#EEF2FF", text_color="#4F46E5", border="#C7D2FE", pad_x=14, pad_y=6):
    """Draw rounded pill badge."""
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x2 = x + w + (pad_x * 2)
    y2 = y + h + (pad_y * 2)
    draw.rounded_rectangle([x, y, x2, y2], radius=h + pad_y, fill=fill, outline=border, width=1)
    draw.text((x + pad_x, y + pad_y - 2), text, font=font, fill=text_color)
    return x2


# ==============================================================================
# 1. HERO BANNER LIGHT (assets/images/eig_hero_light.png)
# ==============================================================================
def generate_hero_banner(output_path="assets/images/eig_hero_light.png"):
    width, height = 1200, 630
    img = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Soft ambient background gradient
    for y in range(height):
        ratio = y / height
        r = int(248 + (255 - 248) * (1 - ratio))
        g = int(250 + (255 - 250) * (1 - ratio))
        b = int(252 + (240 - 252) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    # Decorative background grid dots
    for gx in range(40, width, 40):
        for gy in range(40, height, 40):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill="#E2E8F0")

    # Brand Pill
    f_badge = get_font("segoeuib.ttf", 15)
    f_title = get_font("segoeuib.ttf", 46)
    f_sub = get_font("segoeui.ttf", 20)
    f_card_title = get_font("segoeuib.ttf", 18)
    f_card_desc = get_font("segoeui.ttf", 14)

    draw_badge(draw, 80, 50, "DATHEON AI • ENTERPRISE RISK FRAMEWORK", f_badge, fill="#EFF6FF", text_color="#2563EB", border="#BFDBFE")

    # Main Hero Title
    draw.text((80, 95), "Enterprise Intelligence Gateway", font=f_title, fill="#0F172A")
    draw.text((80, 155), "Production-Grade Secure AI Platform: Ingestion, Multi-Tenant RAG & Autonomous Agent", font=f_sub, fill="#475569")

    # Feature Grid Cards (3 Columns)
    cards = [
        {
            "icon": "ETL",
            "title": "Module 1: Legacy ETL",
            "desc": "PDF, CSV & Markdown ingestion with page/row provenance, SHA-256 deduplication, and ChromaDB vector indexing.",
            "color": "#3B82F6",
            "bg": "#EFF6FF"
        },
        {
            "icon": "RAG",
            "title": "Module 2: Secure RAG",
            "desc": "Fail-closed RBAC with hybrid BM25 + dense search, cross-encoder reranking, and verifiable page citations.",
            "color": "#10B981",
            "bg": "#ECFDF5"
        },
        {
            "icon": "AGENT",
            "title": "Module 3: ERP Agent",
            "desc": "Constrained tool calling with cryptographic HMAC-SHA256 human approval and append-only hash chain audit.",
            "color": "#8B5CF6",
            "bg": "#F5F3FF"
        }
    ]

    card_w = 320
    card_h = 240
    start_x = 80
    card_y = 220

    for idx, card in enumerate(cards):
        cx = start_x + (idx * (card_w + 40))
        draw_card(draw, cx, card_y, cx + card_w, card_y + card_h, fill="#FFFFFF", outline="#E2E8F0", radius=16)

        # Icon pill
        draw.rounded_rectangle([cx + 24, card_y + 24, cx + 90, card_y + 54], radius=8, fill=card["bg"], outline=card["color"])
        draw.text((cx + 34, card_y + 30), card["icon"], font=f_badge, fill=card["color"])

        draw.text((cx + 24, card_y + 75), card["title"], font=f_card_title, fill="#1E293B")

        # Multi-line wrap description
        words = card["desc"].split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 30:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))

        for l_idx, line in enumerate(lines):
            draw.text((cx + 24, card_y + 115 + (l_idx * 22)), line, font=f_card_desc, fill="#64748B")

    # Bottom Stat Badges Bar
    bx = 80
    by = 500
    badges = [
        "169 Docs/Sec Throughput",
        "7.39ms p50 Latency",
        "100% Tenant Isolation",
        "HMAC Approvals",
        "23/23 Automated Tests"
    ]
    for b in badges:
        bx = draw_badge(draw, bx, by, b, f_badge, fill="#F8FAFC", text_color="#334155", border="#CBD5E1") + 16

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"Generated: {output_path}")


# ==============================================================================
# 2. ARCHITECTURE DIAGRAM LIGHT (assets/images/eig_architecture_light.png)
# ==============================================================================
def generate_architecture_diagram(output_path="assets/images/eig_architecture_light.png"):
    width, height = 1200, 675
    img = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(int(248 + 7 * (1 - ratio)), int(250 + 5 * (1 - ratio)), int(252 + 3 * (1 - ratio)), 255))

    f_badge = get_font("segoeuib.ttf", 14)
    f_title = get_font("segoeuib.ttf", 36)
    f_sub = get_font("segoeui.ttf", 18)
    f_box_h = get_font("segoeuib.ttf", 16)
    f_box_b = get_font("segoeui.ttf", 13)

    draw_badge(draw, 60, 40, "SYSTEM ARCHITECTURE & TRUST BOUNDARY", f_badge, fill="#EFF6FF", text_color="#2563EB", border="#BFDBFE")
    draw.text((60, 75), "Modular Monolith Architecture with Fail-Closed RBAC", font=f_title, fill="#0F172A")
    draw.text((60, 125), "Strict isolation between untrusted document ETL, server-verified RAG, and approved tool actions", font=f_sub, fill="#64748B")

    # 4 Main Architectural Blocks
    boxes = [
        {
            "x": 60, "y": 180, "w": 250, "h": 420,
            "title": "MODULE 1: ETL Pipeline",
            "tag": "INGESTION & VECTOR ETL",
            "color": "#3B82F6",
            "items": [
                "• PDF Parser (Page provenance)",
                "• CSV Parser (Row traceability)",
                "• Markdown Parser (Heading trees)",
                "• SHA-256 Content Deduplication",
                "• Semantic & Structure Chunker",
                "• ChromaDB Cosine Store",
                "• Qdrant Client Adapter"
            ]
        },
        {
            "x": 340, "y": 180, "w": 250, "h": 420,
            "title": "MODULE 2: Secure RAG",
            "tag": "MULTI-TENANT RBAC",
            "color": "#10B981",
            "items": [
                "• Server-Verified Identity Context",
                "• Pre-Retrieval RBAC & Clearance",
                "• BM25 Sparse + Dense Vector",
                "• Reciprocal Rank Fusion (RRF)",
                "• Cross-Encoder Reranker",
                "• Context Budget Window Manager",
                "• Grounded Citations & Abstention"
            ]
        },
        {
            "x": 620, "y": 180, "w": 250, "h": 420,
            "title": "MODULE 3: ERP Agent",
            "tag": "CONSTRAINED TOOLS",
            "color": "#8B5CF6",
            "items": [
                "• 7-Phase Execution Lifecycle",
                "• Allowlisted Tool Schemas",
                "• HMAC-SHA256 Approval Engine",
                "• Single-Use Nonce & Expiration",
                "• Mock ERP/CRM REST Services",
                "• State Verification Flow",
                "• Append-Only Hash Chain Audit"
            ]
        },
        {
            "x": 900, "y": 180, "w": 240, "h": 420,
            "title": "MODULE 4: Gateway API",
            "tag": "FASTAPI & OBSERVABILITY",
            "color": "#F59E0B",
            "items": [
                "• JWT Bearer Auth Middleware",
                "• In-Memory Sliding Rate Limiter",
                "• X-Correlation-ID Tracking",
                "• Prometheus /metrics Registry",
                "• /health/live & /health/ready",
                "• Multi-Stage Non-Root Docker",
                "• Safe Redacted Diagnostics"
            ]
        }
    ]

    for b in boxes:
        draw_card(draw, b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"], fill="#FFFFFF", outline="#CBD5E1", radius=14)
        # Top banner in card
        draw.rounded_rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + 46], radius=12, fill=b["color"])
        draw.text((b["x"] + 14, b["y"] + 14), b["tag"], font=get_font("segoeuib.ttf", 11), fill="#FFFFFF")
        draw.text((b["x"] + 14, b["y"] + 60), b["title"], font=f_box_h, fill="#0F172A")

        # Items
        for idx, itm in enumerate(b["items"]):
            draw.text((b["x"] + 14, b["y"] + 105 + (idx * 38)), itm, font=f_box_b, fill="#334155")

    img.save(output_path, "PNG", quality=95)
    print(f"Generated: {output_path}")


# ==============================================================================
# 3. SECURITY & APPROVAL FLOW (assets/images/eig_security_approval_light.png)
# ==============================================================================
def generate_security_diagram(output_path="assets/images/eig_security_approval_light.png"):
    width, height = 1200, 675
    img = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(int(248 + 7 * (1 - ratio)), int(250 + 5 * (1 - ratio)), int(252 + 3 * (1 - ratio)), 255))

    f_badge = get_font("segoeuib.ttf", 14)
    f_title = get_font("segoeuib.ttf", 36)
    f_sub = get_font("segoeui.ttf", 18)
    f_step_num = get_font("segoeuib.ttf", 20)
    f_step_title = get_font("segoeuib.ttf", 15)
    f_step_desc = get_font("segoeui.ttf", 12)

    draw_badge(draw, 60, 40, "SECURITY & COMPLIANCE GUARDRAILS", f_badge, fill="#ECFDF5", text_color="#059669", border="#A7F3D0")
    draw.text((60, 75), "Autonomous Agent 7-Phase Execution Lifecycle", font=f_title, fill="#0F172A")
    draw.text((60, 125), "PLAN -> VALIDATE -> AUTHORIZE -> APPROVE -> EXECUTE -> VERIFY -> AUDIT", font=f_sub, fill="#475569")

    # 7 Phase Workflow Pills horizontally
    phases = [
        {"num": "1", "name": "PLAN", "desc": "Allowlisted tool selection", "color": "#3B82F6"},
        {"num": "2", "name": "VALIDATE", "desc": "Strict Pydantic JSON schema", "color": "#6366F1"},
        {"num": "3", "name": "AUTHORIZE", "desc": "RBAC & Clearance check", "color": "#8B5CF6"},
        {"num": "4", "name": "APPROVE", "desc": "HMAC token & Expiration", "color": "#EC4899"},
        {"num": "5", "name": "EXECUTE", "desc": "Isolated service call", "color": "#F59E0B"},
        {"num": "6", "name": "VERIFY", "desc": "State mutation check", "color": "#10B981"},
        {"num": "7", "name": "AUDIT", "desc": "Append-only hash chain", "color": "#06B6D4"},
    ]

    pw = 142
    ph = 140
    px_start = 60
    py = 180

    for idx, p in enumerate(phases):
        x = px_start + (idx * (pw + 16))
        draw_card(draw, x, py, x + pw, py + ph, fill="#FFFFFF", outline="#CBD5E1", radius=12)

        # Number circle
        draw.ellipse([x + 14, py + 14, x + 44, py + 44], fill=p["color"])
        draw.text((x + 23, py + 18), p["num"], font=f_step_num, fill="#FFFFFF")

        draw.text((x + 14, py + 56), p["name"], font=f_step_title, fill="#0F172A")
        draw.text((x + 14, py + 86), p["desc"], font=f_step_desc, fill="#64748B")

    # Lower Security Invariants Highlights Card
    draw_card(draw, 60, 350, 1140, 610, fill="#F8FAFC", outline="#E2E8F0", radius=16)
    draw.text((90, 375), "Security Invariants & Cryptographic Assurance", font=get_font("segoeuib.ttf", 22), fill="#0F172A")

    invariants = [
        ("Cryptographic HMAC-SHA256 Token", "All sensitive write operations bind tenant_id, user_id, tool_name, argument_hash, and nonce to prevent parameter tampering."),
        ("Strict Replay Attack Defense", "Single-use random nonces ensure approval tokens cannot be re-executed once approved or rejected (HTTP 409 Conflict)."),
        ("Append-Only Hash Chain Ledger", "Audit events are cryptographically linked: current_hash = SHA256(prev_hash + tenant + action + details + timestamp)."),
        ("Fail-Closed Tenant Isolation", "Metadata filtering is hard-pinned at the database boundary, neutralizing prompt injection and filter tampering.")
    ]

    for idx, (inv_title, inv_desc) in enumerate(invariants):
        row_y = 420 + (idx * 44)
        draw.ellipse([90, row_y + 4, 102, row_y + 16], fill="#10B981")
        draw.text((115, row_y), inv_title + " — ", font=get_font("segoeuib.ttf", 15), fill="#1E293B")
        title_bbox = get_font("segoeuib.ttf", 15).getbbox(inv_title + " — ")
        offset_x = 115 + (title_bbox[2] - title_bbox[0])
        draw.text((offset_x, row_y + 1), inv_desc, font=get_font("segoeui.ttf", 13), fill="#475569")

    img.save(output_path, "PNG", quality=95)
    print(f"Generated: {output_path}")


# ==============================================================================
# 4. LINKEDIN SHOWCASE BANNER (image.png in project root)
# ==============================================================================
def generate_linkedin_banner(output_path="image.png"):
    width, height = 1200, 630
    img = Image.new("RGBA", (width, height), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Clean high-end SaaS background
    for y in range(height):
        ratio = y / height
        draw.line([(0, y), (width, y)], fill=(int(248 + 7 * (1 - ratio)), int(250 + 5 * (1 - ratio)), int(252 + 3 * (1 - ratio)), 255))

    # Grid accents
    for gx in range(50, width, 50):
        for gy in range(50, height, 50):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill="#E2E8F0")

    f_badge = get_font("segoeuib.ttf", 14)
    f_title = get_font("segoeuib.ttf", 44)
    f_sub = get_font("segoeui.ttf", 20)
    f_stat_num = get_font("segoeuib.ttf", 36)
    f_stat_lbl = get_font("segoeuib.ttf", 15)
    f_stat_sub = get_font("segoeui.ttf", 13)

    # Top Brand Pill
    draw_badge(draw, 70, 45, "DATHEON FORWARD DEPLOYED ENGINEERING • ENTERPRISE AI", f_badge, fill="#EFF6FF", text_color="#1D4ED8", border="#93C5FD")

    # Main Title
    draw.text((70, 90), "Enterprise Intelligence Gateway (EIG)", font=f_title, fill="#0F172A")
    draw.text((70, 150), "Production-Ready Platform: Legacy Ingestion • Multi-Tenant RAG • Autonomous Agent", font=f_sub, fill="#475569")

    # 4 High-Impact KPI Highlight Cards
    kpis = [
        {
            "stat": "169.5",
            "unit": "Docs/Sec",
            "label": "Ingestion Throughput",
            "desc": "PDF, CSV & Markdown ETL with 0.0% failure rate",
            "color": "#2563EB",
            "bg": "#EFF6FF"
        },
        {
            "stat": "7.39",
            "unit": "ms p50",
            "label": "Hybrid RAG Latency",
            "desc": "Sub-10ms search with BM25 + dense vector RRF",
            "color": "#059669",
            "bg": "#ECFDF5"
        },
        {
            "stat": "100%",
            "unit": "Denial",
            "label": "Cross-Tenant Isolation",
            "desc": "Zero data leakage across department/clearance tiers",
            "color": "#7C3AED",
            "bg": "#F5F3FF"
        },
        {
            "stat": "23/23",
            "unit": "PASS",
            "label": "Automated Test Suite",
            "desc": "100% pass across all 14 mandatory risk categories",
            "color": "#D97706",
            "bg": "#FFFBEB"
        }
    ]

    card_w = 245
    card_h = 220
    start_x = 70
    card_y = 210

    for idx, kpi in enumerate(kpis):
        cx = start_x + (idx * (card_w + 25))
        draw_card(draw, cx, card_y, cx + card_w, card_y + card_h, fill="#FFFFFF", outline="#E2E8F0", radius=16)

        # Stat Header
        draw.text((cx + 20, card_y + 24), kpi["stat"], font=f_stat_num, fill=kpi["color"])
        bbox = f_stat_num.getbbox(kpi["stat"])
        num_w = bbox[2] - bbox[0]
        draw.text((cx + 24 + num_w, card_y + 38), kpi["unit"], font=get_font("segoeuib.ttf", 16), fill="#64748B")

        # Label
        draw.text((cx + 20, card_y + 80), kpi["label"], font=f_stat_lbl, fill="#0F172A")

        # Description
        words = kpi["desc"].split()
        lines = []
        cur = []
        for w in words:
            cur.append(w)
            if len(" ".join(cur)) > 24:
                lines.append(" ".join(cur))
                cur = []
        if cur:
            lines.append(" ".join(cur))

        for l_idx, line in enumerate(lines):
            draw.text((cx + 20, card_y + 115 + (l_idx * 20)), line, font=f_stat_sub, fill="#64748B")

    # Bottom Tech Stack Bar
    draw_card(draw, 70, 470, 1130, 560, fill="#F8FAFC", outline="#E2E8F0", radius=14, shadow=False)
    draw.text((95, 502), "TECHNOLOGY STACK:", font=get_font("segoeuib.ttf", 13), fill="#475569")

    tech_pills = ["Python 3.12+", "FastAPI", "ChromaDB", "Qdrant", "SQLAlchemy 2.0", "HMAC-SHA256", "Prometheus", "Docker"]
    tx = 245
    for t in tech_pills:
        tx = draw_badge(draw, tx, 492, t, f_badge, fill="#FFFFFF", text_color="#1E293B", border="#CBD5E1") + 12

    img.save(output_path, "PNG", quality=95)
    print(f"Generated: {output_path}")


if __name__ == "__main__":
    generate_hero_banner()
    generate_architecture_diagram()
    generate_security_diagram()
    generate_linkedin_banner()
