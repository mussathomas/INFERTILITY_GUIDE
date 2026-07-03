"""Generate sample PDF documents for the infertility knowledge base."""

from pathlib import Path

from fpdf import FPDF

KNOWLEDGE = [
    {
        "filename": "01_understanding_infertility.pdf",
        "title": "Understanding Infertility - Evidence-Based Overview",
        "sections": [
            (
                "Definition and Prevalence",
                "Infertility is defined as the inability to achieve pregnancy after 12 months of regular, "
                "unprotected intercourse (or 6 months if the female partner is over 35). It affects "
                "approximately 1 in 6 couples worldwide. Both male and female factors contribute, and "
                "in many cases multiple factors are present.",
            ),
            (
                "Common Causes - Female",
                "Female factors include ovulatory disorders (e.g., PCOS), tubal blockage, endometriosis, "
                "uterine abnormalities, diminished ovarian reserve, and age-related decline in egg quality. "
                "A thorough evaluation typically includes history, physical exam, ovulation tracking, "
                "hormone testing (AMH, FSH, TSH, prolactin), hysterosalpingography or sonohysterography, "
                "and pelvic ultrasound.",
            ),
            (
                "Common Causes - Male",
                "Male factor infertility accounts for approximately 40-50% of cases, either alone or combined "
                "with female factors. Semen analysis evaluates count, motility, and morphology. Additional "
                "testing may include hormonal panels and genetic screening when indicated.",
            ),
            (
                "When to Seek Help",
                "Couples under 35 should seek evaluation after 12 months of trying; those 35 and older "
                "should seek help after 6 months. Earlier evaluation is recommended for known conditions "
                "such as irregular cycles, prior pelvic surgery, cancer treatment history, or recurrent pregnancy loss.",
            ),
        ],
    },
    {
        "filename": "02_treatment_options.pdf",
        "title": "Fertility Treatment Options",
        "sections": [
            (
                "Lifestyle and Preconception Care",
                "Evidence supports maintaining a healthy BMI, avoiding smoking and excessive alcohol, "
                "managing chronic conditions, taking folic acid, and limiting environmental toxin exposure. "
                "These measures support overall reproductive health but do not replace medical treatment when needed.",
            ),
            (
                "Ovulation Induction and IUI",
                "For ovulatory dysfunction, medications such as letrozole or clomiphene may be used under "
                "medical supervision. Intrauterine insemination (IUI) places prepared sperm directly into "
                "the uterus and may be combined with ovulation induction for unexplained infertility or mild male factor.",
            ),
            (
                "IVF and Assisted Reproductive Technology",
                "In vitro fertilization (IVF) involves ovarian stimulation, egg retrieval, laboratory fertilization, "
                "and embryo transfer. Success rates depend on age, diagnosis, embryo quality, and clinic expertise. "
                "IVF does not guarantee pregnancy; national registries report varying live birth rates by age group.",
            ),
            (
                "Third-Party Reproduction",
                "Donor eggs, donor sperm, gestational carriers, and embryo adoption are options for specific "
                "clinical situations. These pathways involve medical, legal, and psychological counseling.",
            ),
        ],
    },
    {
        "filename": "03_misinformation_and_myths.pdf",
        "title": "Correcting Common Infertility Misinformation",
        "sections": [
            (
                "Myth: Infertility Is Always a Woman's Problem",
                "Fact: Male factor contributes in roughly half of all infertility cases. Comprehensive "
                "evaluation of both partners is the standard of care and avoids delay in diagnosis.",
            ),
            (
                "Myth: Stress Is the Sole Cause",
                "Fact: While chronic stress may affect menstrual regularity and libido, it is rarely the "
                "only cause of infertility. Medical evaluation should not be postponed based on stress alone.",
            ),
            (
                "Myth: IVF Always Works",
                "Fact: IVF success varies significantly. For women under 35, live birth rates per cycle "
                "may be favorable, but rates decline with age. Multiple cycles may be needed.",
            ),
            (
                "Myth: You Can 'Wait Until 40'",
                "Fact: Fertility declines gradually beginning in the late 20s and more steeply after 35. "
                "Egg quantity and quality both decrease with age, affecting natural conception and IVF outcomes.",
            ),
            (
                "Myth: Certain Positions or Timing Guarantees Conception",
                "Fact: While tracking ovulation can optimize timing, no position or post-intercourse routine "
                "has been proven to overcome underlying medical infertility.",
            ),
        ],
    },
    {
        "filename": "04_traditional_and_complementary_medicine.pdf",
        "title": "Traditional and Complementary Medicine - Balanced Guidance",
        "sections": [
            (
                "Acupuncture",
                "Some studies suggest acupuncture may reduce stress and improve well-being during fertility "
                "treatment. Evidence for significantly improved live birth rates is mixed. When used, it "
                "should complement - not replace - conventional medical care and should be provided by "
                "licensed practitioners.",
            ),
            (
                "Traditional Chinese Medicine (TCM) and Herbal Remedies",
                "TCM approaches fertility holistically through herbs, diet, and acupuncture. Quality research "
                "is limited and herb quality varies. Some herbs may interact with fertility medications or "
                "affect hormone levels. Always disclose all supplements and herbs to your fertility specialist.",
            ),
            (
                "Ayurveda",
                "Ayurvedic practices emphasize diet, lifestyle, and herbal preparations. Rigorous clinical "
                "trials in infertility are sparse. Cultural and wellness benefits may exist, but unproven "
                "claims should not delay evidence-based evaluation.",
            ),
            (
                "Nutritional Supplements",
                "Folic acid is recommended when trying to conceive. CoQ10, vitamin D, and omega-3 may support "
                "general health; evidence for direct fertility improvement varies. Avoid megadoses and unverified "
                "'fertility blend' products without medical guidance.",
            ),
            (
                "Safe Integration Principles",
                "Inform your medical team of all complementary practices. Do not stop prescribed medications. "
                "Be skeptical of cures that promise results without clinical evaluation. Seek products with "
                "third-party purity testing when supplements are used.",
            ),
        ],
    },
]


def create_pdf(output_dir: Path, doc: dict) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, doc["title"])
    pdf.ln(5)

    for heading, body in doc["sections"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 8, heading)
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, body)
        pdf.ln(5)

    pdf.output(str(output_dir / doc["filename"]))


def main() -> None:
    output_dir = Path(__file__).resolve().parent.parent / "knowledge_base"
    output_dir.mkdir(parents=True, exist_ok=True)
    for doc in KNOWLEDGE:
        create_pdf(output_dir, doc)
        print(f"Created {doc['filename']}")
    print(f"\nDone. {len(KNOWLEDGE)} PDFs written to {output_dir}")


if __name__ == "__main__":
    main()
