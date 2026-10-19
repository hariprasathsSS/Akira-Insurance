"""Generate synthetic policy PDF documents for Health, Motor, and Home domains.

Per Section 6:
Every PDF contains a conspicuous note:
"SYNTHETIC POC DOCUMENT — NOT A REAL INSURANCE CONTRACT."
"""
from __future__ import annotations

import os

SAMPLE_DOCS = [
    {
        "filename": "health_guard_basic_v1.pdf",
        "title": "Health Guard Basic Policy Document",
        "policy_type": "health",
        "plan_tier": "basic",
        "sections": [
            (
                "Section 1: Scope of Cover",
                "This synthetic health policy provides in-patient hospitalization coverage up to INR 5,00,000 "
                "per policy year. Room rent is covered up to INR 5,000 per day. ICU charges are covered "
                "up to INR 10,000 per day. Pre-hospitalization expenses are covered for 30 days prior to admission. "
                "Post-hospitalization medical expenses are covered for 60 days following discharge.",
            ),
            (
                "Section 2: Deductibles and Co-payments",
                "An annual aggregate deductible of INR 5,000 applies to all claims under this basic plan. "
                "The insured is responsible for the first INR 5,000 of admissible hospital expenses. "
                "No co-payment applies for treatments at network hospitals; a 10% co-payment applies at non-network hospitals.",
            ),
            (
                "Section 3: Exclusions and Waiting Periods",
                "Pre-existing diseases (PED) are subject to a 36-month waiting period from inception. "
                "A initial 30-day waiting period applies for any illness except accidental injuries. "
                "Cosmetic surgery, weight control procedures, and non-prescription vitamins are specifically excluded.",
            ),
            (
                "Section 4: Claim Filing and FNOL",
                "Notice of claim (FNOL) must be submitted within 48 hours of emergency hospitalization or "
                "72 hours prior to planned hospitalization. Required documentation includes original discharge summary, "
                "itemized hospital bills, pharmacy receipts, and diagnostic test reports.",
            ),
        ],
    },
    {
        "filename": "motor_drivecare_gold_v1.pdf",
        "title": "Motor DriveCare Gold Comprehensive Policy",
        "policy_type": "motor",
        "plan_tier": "gold",
        "sections": [
            (
                "Section 1: Own Damage and Third Party Coverage",
                "This comprehensive policy covers loss or damage to the insured vehicle caused by accidental external "
                "means, fire, theft, explosion, lightning, and natural perils. Maximum Insured's Declared Value (IDV) "
                "is INR 8,00,000. Third party property damage liability is covered up to statutory limits.",
            ),
            (
                "Section 2: Deductibles and Zero Depreciation",
                "Standard compulsory deductible is INR 0 for this Gold tier policy. "
                "Includes Zero Depreciation (Bumper to Bumper) endorsement: depreciation is waived on replacement of "
                "plastic, rubber, nylon, glass, and metal parts during authorized collision repair claims.",
            ),
            (
                "Section 3: Exclusions",
                "Damage sustained while driving under the influence of alcohol or drugs is strictly excluded. "
                "Consequential loss, normal wear and tear, mechanical/electrical breakdown, and driving without a valid "
                "license are not covered.",
            ),
            (
                "Section 4: Claims Procedure",
                "Immediate intimation is required upon occurrence of any collision or theft incident. "
                "Police First Information Report (FIR) is mandatory for third party injury, fatal accidents, or total vehicle theft.",
            ),
        ],
    },
    {
        "filename": "home_protect_elite_v1.pdf",
        "title": "Home Protect Elite Comprehensive Policy",
        "policy_type": "home",
        "plan_tier": "elite",
        "sections": [
            (
                "Section 1: Structure and Contents Coverage",
                "Covers physical structure of the residential property up to INR 50,00,000 and household contents "
                "up to INR 15,00,000 against fire, earthquake, lightning, explosion, storm, flood, and water tank rupture. "
                "Includes temporary alternate accommodation allowance up to INR 2,00,000.",
            ),
            (
                "Section 2: Deductible",
                "A compulsory excess/deductible of INR 10,000 applies to each and every property damage claim under this policy.",
            ),
            (
                "Section 3: Exclusions",
                "Loss caused by gradual seepage, defective design, willful destruction, war, or radioactive contamination "
                "is excluded. Valuables exceeding INR 50,000 must be individually scheduled.",
            ),
            (
                "Section 4: Claim Assessment",
                "Insured must preserve damaged items for physical adjuster inspection. Estimates from licensed contractors "
                "must accompany repair claims exceeding INR 25,000.",
            ),
        ],
    },
]


def _build_minimal_pdf_bytes(title: str, sections: list[tuple[str, str]]) -> bytes:
    """Generate a clean, strictly standard-conforming PDF 1.4 file directly."""
    # Build text content
    lines = [
        f"AKIRA INSURANCE — {title.upper()}",
        "===========================================================",
        "SYNTHETIC POC DOCUMENT — NOT A REAL INSURANCE CONTRACT.",
        "For simulation, testing, and AI demonstration purposes only.",
        "===========================================================",
        "",
    ]
    for heading, text in sections:
        lines.append(heading)
        lines.append("-" * len(heading))
        # Word wrap approx 70 chars
        words = text.split()
        cur_line = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 > 70:
                lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
            else:
                cur_line.append(w)
                cur_len += len(w) + 1
        if cur_line:
            lines.append(" ".join(cur_line))
        lines.append("")

    lines.append("SYNTHETIC POC DOCUMENT — NOT A REAL INSURANCE CONTRACT.")

    # Escape parentheses and backslashes for PDF string literal
    def escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    # Build PDF stream
    stream_content = "BT\n/F1 10 Tf\n12 TL\n50 720 Td\n"
    for line in lines:
        stream_content += f"({escape(line)}) '\n"
    stream_content += "ET\n"

    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)

    objects = [
        # Obj 1: Catalog
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        # Obj 2: Pages
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        # Obj 3: Page
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        # Obj 4: Contents
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1")
        + stream_bytes
        + b"\nendstream\nendobj\n",
        # Obj 5: Font
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode("latin-1")

    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
    return pdf


def generate_sample_pdfs(output_dir: str) -> list[str]:
    """Generate sample PDF files in output_dir and return list of file paths."""
    os.makedirs(output_dir, exist_ok=True)
    generated = []

    for item in SAMPLE_DOCS:
        out_path = os.path.join(output_dir, item["filename"])
        pdf_bytes = _build_minimal_pdf_bytes(item["title"], item["sections"])
        with open(out_path, "wb") as fh:
            fh.write(pdf_bytes)
        generated.append(out_path)
        print(f"Generated sample policy PDF: {out_path} ({len(pdf_bytes)} bytes)")

    return generated


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "sample_policies")
    generate_sample_pdfs(target)
