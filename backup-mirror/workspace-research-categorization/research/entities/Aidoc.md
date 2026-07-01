# Aidoc

Research date: 2026-05-25.

Method note: the local seed file was treated only as a hypothesis. The categorization below relies on current public sources listed in the source register. Every factual field carries a source key; fields marked N/A were not verified in the consulted sources.

## 1. Classification Verdict

| Field | Value | Citation |
|---|---|---|
| Entity name | Aidoc | Aidoc official website and FDA submissions use Aidoc / Aidoc Medical, Ltd. [S1][S5][S7] |
| Legal / submitter name observed | Aidoc Medical, Ltd. | FDA 510(k) letters identify the submitter as Aidoc Medical, Ltd. [S5][S6][S7] |
| System sub-sector | Digital Health | Aidoc's core product is AI software for radiology triage, notification, scan analysis, workflow prioritization, and platform integration; FDA classifies the cleared products as software devices, not physical imaging hardware. [S2][S3][S4][S5][S6][S7] |
| FDA device classification | Class II radiological computer aided triage and notification software | FDA K190896, K222277, and K252970 list Regulation Number 21 CFR 892.2080, Regulation Name radiological computer aided triage and notification software, and Regulatory Class Class II. [S5][S6][S7] |
| Dominant value rule result | Software-led clinical AI; not a proprietary imaging-hardware company | Aidoc states that its radiology platform uses AI triage algorithms, aiOS orchestration, PACS/EHR integration, and AI-powered insights; FDA indications describe artificial-intelligence software that analyzes CT/X-ray images and flags suspected findings. [S2][S3][S4][S5][S6][S7] |
| Primary specialized vertical | Diagnostics | Aidoc's official solution list covers image-based radiology findings including intracranial hemorrhage, pulmonary embolism, pneumothorax, fractures, aortic findings, and abdominal CT findings. [S2][S3][S7] |
| Secondary specialized vertical | Decision Support | FDA indications state that BriefCase/BriefCase-Triage assists workflow triage/prioritization by flagging and communicating suspected positive findings for trained clinicians. [S5][S6][S7] |
| Secondary platform-level vertical | Clinical Workflow | Aidoc states that its platform integrates with EHR, PACS, scheduling, reporting, mobile, and care tools, and supports workflow triage, care coordination, and patient management. [S2][S3][S4] |
| Primary clinical domain | Radiology | Aidoc's official radiology page describes AI medical imaging for radiologists, FDA clearances concern radiological software, and clinical validation studies evaluate CT/radiology workflows. [S2][S5][S6][S7][S10][S11] |
| Secondary clinical domains observed | Neurology; Pulmonology; Cardiology; Orthopedics; Gastroenterology; Urology; Nephrology; Surgery | Neurology-related indications include intracranial hemorrhage and vessel occlusion; pulmonary indications include pulmonary embolism and pneumothorax; cardiology/aortic indications include coronary artery calcification and aortic measurement/dissection; fracture indications include C-spine, rib, vertebral compression, extremity, and pelvic fracture; abdomen indications include diverticulitis, appendicitis, bowel obstruction, abscess, liver/kidney/spleen injury, obstructive renal stone, and free gas. [S2][S3][S5][S6][S7][S8][S9] |
| Core mechanism of action | AI analysis of medical images to flag suspected findings and prioritize/notify clinicians | FDA indications state that BriefCase uses an artificial intelligence algorithm to analyze images, highlight detected findings, present notifications, and assist triage/prioritization; Aidoc's radiology page says AI triage algorithms alert on suspected acute findings. [S2][S5][S6][S7] |
| Diagnostic-use boundary | Not intended to be used as a standalone diagnostic device | FDA indications state that notifications are informational and not intended for diagnostic use beyond notification, and that the device is not intended to be used as a diagnostic device. [S5][S6][S7] |
| Operating status | Operating evidence observed; legal active status not independently verified from Israeli Registrar in this pass | Aidoc's official website is live with 2026 copyright content; FDA issued K252970 on 2026-01-07 to Aidoc Medical, Ltd. [S1][S7] |
| Confidence score | 9/10 for taxonomy placement; lower confidence for legal registry fields | Taxonomy is supported by official company pages, FDA letters, and peer-reviewed clinical literature; Israeli company registration number and formal legal status were not verified in this pass. [S1][S2][S5][S6][S7][S10][S11][S12][S13][S14] |

## 2. Seed Data Check

| Seed claim | Current result | Citation |
|---|---|---|
| Aidoc is Digital Health: Diagnostics, Decision Support | Verified with refinement: Digital Health is correct; Diagnostics and Decision Support are correct; Clinical Workflow is also supported at platform level. | [S2][S3][S4][S5][S6][S7] |
| Established in 2016 | Verified from Aidoc official about page. | [S1] |
| CEO Elad Walach | Partially verified from Aidoc official page evidence: Aidoc's comprehensive abdomen CT page attributes a quote to Elad Walach, CEO and Co-founder, Aidoc; full leadership extraction was limited by the page content fetched. | [S15] |
| Multiple FDA 510(k) clearances | Verified. FDA examples include K190896, K222277, K243548, K242203, K253265, and K252970. | [S5][S6][S7][S8][S9][S16] |
| CE marked | Company-claimed but not independently verified in this pass. Aidoc official radiology page says its algorithms include FDA-cleared and CE/UKCA-marked algorithms; no notified-body certificate was retrieved. | [S2] |
| International HQ New York | Not verified in this pass. | N/A |
| Israeli private Ltd / R&D HQ Tel Aviv | Aidoc Medical, Ltd. and Tel Aviv address are verified from FDA submissions; Israeli private company status and R&D HQ were not verified from the Israeli Registrar in this pass. | [S5][S7] |

## 3. Evidence Matrix

| Evidence item | Extracted fact | Categorization implication | Citation |
|---|---|---|---|
| Aidoc official about page | Aidoc says it was established in 2016 and first focused on helping radiologists reduce turnaround time and increase quality/efficiency by flagging acute anomalies in real time. | Supports Digital Health, Radiology, Diagnostics, and Decision Support. | [S1] |
| Aidoc official radiology page | Aidoc says AI triage algorithms alert on suspected acute findings, quantification algorithms automate repetitive tasks, and the platform integrates with EHR, PACS, scheduling, and reporting systems. | Supports software-led Digital Health, Diagnostics, Decision Support, and Clinical Workflow. | [S2] |
| Aidoc official solutions page | Aidoc lists radiology use cases including intracranial hemorrhage, pulmonary embolism, pneumothorax, fractures, aortic findings, and other imaging findings; it also states radiology solutions include 17 organic FDA-cleared algorithms and eight FDA-cleared partner algorithms. | Supports primary Radiology domain and multi-domain secondary mapping. | [S3] |
| Aidoc aiOS page | Aidoc says aiOS runs, orchestrates, and governs clinical AI across health systems, using textual data, scan metadata, and pixel analysis, and integrating with PACS, EHR, mobile, and care tools. | Supports platform-level Clinical Workflow but does not override the primary Diagnostics/Decision Support categorization. | [S4] |
| FDA K190896 | FDA lists BriefCase as Class II radiological computer aided triage and notification software for cervical-spine CT fracture triage; indications state the software uses AI to analyze images and assist triage/prioritization. | Establishes SaMD/software device class and supports Digital Health over Medical Devices hardware classification. | [S5] |
| FDA K222277 | FDA lists BriefCase as Class II radiological computer aided triage and notification software for CTPA pulmonary embolism triage; indications state the device uses AI and is not intended as a diagnostic device. | Supports Decision Support, Radiology, Pulmonology relevance, and Cardiology relevance for pulmonary embolism. | [S6] |
| FDA K252970 | FDA lists BriefCase-Triage: CARE Multi-triage CT Body as Class II radiological computer aided triage and notification software for contrast/non-contrast CT of chest, abdomen, and/or pelvis, with eleven listed suspected findings. | Supports broad Diagnostic imaging coverage and software-led classification. | [S7] |
| PubMed PMID 31828361 | A 2020 Neuroradiology study analyzed Aidoc software for acute intracranial hemorrhage detection/worklist prioritization on non-contrast head CT and reported sensitivity 88.7%, specificity 94.2%, NPV 97.7%, and accuracy 93.4%. | Supports clinical validation evidence for Radiology/Neurology use. | [S10] |
| PubMed PMID 37095668 | A 2023 AJR study found AI-driven worklist reprioritization reduced report turnaround time and wait time for PE-positive CTPA examinations. | Supports workflow triage and Decision Support effect in pulmonary embolism imaging. | [S11] |
| PubMed PMID 39601611 | A 2025 Neuroradiology Journal external validation study reported Aidoc model sensitivity 89%, specificity 96%, PPV 82%, NPV 97%, accuracy 94%, and AUC 0.954 for intracranial hemorrhage detection. | Supports continuing clinical validation evidence for ICH detection. | [S12] |
| PubMed PMID 40796469 | A 2025 Academic Radiology study evaluated post-deployment Aidoc ICH performance across 332,809 head CT examinations from 37 U.S. radiology practices. | Supports real-world deployment and monitoring evidence. | [S13] |
| PubMed PMID 40957692 | A 2026 AJNR comparison study identifies Vendor A as Aidoc and reports sensitivity 94.4%, specificity 97.4%, PPV 77.7%, and NPV 99.5% for ICH detection on noncontrast head CT. | Supports independent comparative performance evidence for ICH triage. | [S14] |

## 4. Taxonomy Output

| Template field | Aidoc value | Citation |
|---|---|---|
| Legal Name | Aidoc Medical, Ltd. | [S5][S6][S7] |
| H.P. Number | N/A; not verified from Israeli Registrar in this pass | N/A |
| Delaware Entity | N/A; not verified in this pass | N/A |
| Status | Operating evidence observed; formal legal status N/A | [S1][S7] |
| Sub-Sector | Digital Health | [S2][S3][S4][S5][S6][S7] |
| Specialized Vertical | Diagnostics; Decision Support; Clinical Workflow as secondary platform-level tag | [S2][S3][S4][S5][S6][S7] |
| Primary Clinical Domain | Radiology | [S2][S5][S6][S7][S10][S11] |
| Secondary Clinical Domains | Neurology; Pulmonology; Cardiology; Orthopedics; Gastroenterology; Urology; Nephrology; Surgery | [S2][S3][S5][S6][S7][S8][S9] |
| Clinical Keywords | AI radiology; medical imaging; CT; CTA; CTPA; non-contrast head CT; triage; notification; intracranial hemorrhage; pulmonary embolism; pneumothorax; fracture; aortic measurement/dissection; appendicitis; diverticulitis; bowel obstruction; obstructive renal stone; abdominal-pelvic abscess; organ injury | [S2][S3][S5][S6][S7][S8][S9][S10][S11][S12][S14] |
| ICD-11 Alignment | Not finalized to codes in this pass; condition-level mapping requires a separate ICD lookup. Mission-level chapter anchors likely relevant include nervous system for ICH, respiratory context for pneumothorax/PE presentations, musculoskeletal for fractures, genitourinary for obstructive renal stone/kidney injury, digestive for appendicitis/diverticulitis/bowel obstruction, and external causes/surgical-safety context for trauma/emergency findings. | [S5][S6][S7][S8][S10][S11][S12][S14] |
| Regulatory Status | Multiple FDA 510(k) clearances observed; examples include Class II radiological computer aided triage/notification software and Class II medical image management/processing software. | [S5][S6][S7][S8][S9][S16] |
| Mechanism of Action | AI image-analysis software flags suspected findings from medical imaging and routes/prioritizes notifications for clinician review. | [S2][S5][S6][S7] |
| Notable Limitation | FDA indications repeatedly state the software is not intended to be used as a diagnostic device and should be used with clinician judgment and standard-of-care image review. | [S5][S6][S7] |

## 5. Decision Log

1. I classify Aidoc as Digital Health, not Medical Devices, because the dominant value is software: AI triage/notification, orchestration, and workflow integration. FDA device class does not automatically make the system-taxonomy sub-sector Medical Devices when the product is software-based SaMD. [S2][S4][S5][S6][S7]
2. I assign Diagnostics because the product identifies suspected imaging findings across CT/X-ray/radiology use cases. [S2][S3][S5][S6][S7]
3. I assign Decision Support because FDA indications describe assisting workflow triage/prioritization and notifying trained clinicians of suspected findings, while leaving diagnosis to clinicians and standard-of-care review. [S5][S6][S7]
4. I assign Clinical Workflow only as a secondary platform-level tag because Aidoc's aiOS/care-coordination materials emphasize integration, orchestration, communication, patient management, and system workflows; the core cleared device function remains imaging triage/notification. [S2][S3][S4]
5. I mark legal registry fields as N/A where not independently verified, despite seed-file claims, because the task required no assumptions. [S5][S7]

## 6. Source Register

- [S1] Aidoc, "About" page, fetched 2026-05-25: https://www.aidoc.com/about/
- [S2] Aidoc, "Radiology AI Imaging" page, fetched 2026-05-25: https://www.aidoc.com/solutions/radiology/
- [S3] Aidoc, "AI-Powered Clinical Solutions" page, fetched 2026-05-25: https://www.aidoc.com/solutions/
- [S4] Aidoc, "aiOS" page, fetched 2026-05-25: https://www.aidoc.com/platform/aios/
- [S5] FDA 510(k) K190896, BriefCase, Aidoc Medical, Ltd., 2019-05-31: https://www.accessdata.fda.gov/cdrh_docs/pdf19/K190896.pdf
- [S6] FDA 510(k) K222277, BriefCase, Aidoc Medical, Ltd., 2022-07-29: https://www.accessdata.fda.gov/cdrh_docs/pdf22/K222277.pdf
- [S7] FDA 510(k) K252970, BriefCase-Triage: CARE Multi-triage CT Body, Aidoc Medical, Ltd., 2026-01-07: https://www.accessdata.fda.gov/cdrh_docs/pdf25/K252970.pdf
- [S8] FDA 510(k) K243548, BriefCase-Triage, Aidoc Medical, Ltd., 2024-11-15: https://www.accessdata.fda.gov/cdrh_docs/pdf24/K243548.pdf
- [S9] FDA 510(k) K242203, BriefCase-Quantification, Aidoc Medical, Ltd., 2024-10-22: https://www.accessdata.fda.gov/cdrh_docs/pdf24/K242203.pdf
- [S10] Ginat DT, "Analysis of head CT scans flagged by deep learning software for acute intracranial hemorrhage," PubMed PMID 31828361: https://pubmed.ncbi.nlm.nih.gov/31828361/
- [S11] Batra K et al., "Radiologist Worklist Reprioritization Using Artificial Intelligence: Impact on Report Turnaround Times for CTPA Examinations Positive for Acute Pulmonary Embolism," PubMed PMID 37095668: https://pubmed.ncbi.nlm.nih.gov/37095668/
- [S12] Nada A et al., "External validation and performance analysis of a deep learning-based model for the detection of intracranial hemorrhage," PubMed PMID 39601611: https://pubmed.ncbi.nlm.nih.gov/39601611/
- [S13] Rohren E et al., "Post-deployment Monitoring of AI Performance in Intracranial Hemorrhage Detection by ChatGPT," PubMed PMID 40796469: https://pubmed.ncbi.nlm.nih.gov/40796469/
- [S14] Garcia GM et al., "Head-to-Head Comparison of 2 Artificial Intelligence Computer-Aided Triage Solutions for Detecting Intracranial Hemorrhage on Noncontrast Head CT," PubMed PMID 40957692: https://pubmed.ncbi.nlm.nih.gov/40957692/
- [S15] Aidoc, "Comprehensive Abdomen CT Triage" page, fetched 2026-05-25: https://www.aidoc.com/comprehensive-abdomen-ct-triage/
- [S16] Additional FDA 510(k) examples observed via FDA PDFs: K220709 https://www.accessdata.fda.gov/cdrh_docs/pdf22/K220709.pdf; K230534 https://www.accessdata.fda.gov/cdrh_docs/pdf23/K230534.pdf; K253265 https://www.accessdata.fda.gov/cdrh_docs/pdf25/K253265.pdf; K242203 https://www.accessdata.fda.gov/cdrh_docs/pdf24/K242203.pdf; K243548 https://www.accessdata.fda.gov/cdrh_docs/pdf24/K243548.pdf.

## 7. Open Gaps

| Gap | Why it remains open | Next verification target |
|---|---|---|
| Israeli registration number / H.P. | Not retrieved from the Israel Corporations Authority in this pass. | Israel Registrar of Companies / official extract. |
| Delaware entity | Not verified from Delaware Division of Corporations or corporate filings in this pass. | Delaware entity search or company legal docs. |
| Formal active legal status | Operating evidence is strong, but legal registry status was not checked. | Israel Registrar of Companies. |
| CE / UKCA certificate detail | Aidoc claims CE/UKCA-marked algorithms, but no notified-body certificate was retrieved. | EU/UK certificate, MHRA listing, or notified body evidence. |
| Start-Up Nation Central profile | Search result existed but page fetch returned 403; no SNF data used as evidence. | Browser login/access or exported SNC profile. |
