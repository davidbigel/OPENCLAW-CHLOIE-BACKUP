System Architecture Specification: Multi-Agent Mapping Infrastructure for the Israeli Health-Tech Ecosystem

1. Architectural Overview and System Philosophy

1.1 Mission Statement

The primary objective of this infrastructure is the synthesis of unstructured, high-velocity data from the Israeli Health-Tech ecosystem into a verified, graph-based knowledge repository. This system is engineered to facilitate Swiss engineering planning by identifying high-probability prospects through the mapping of complex connectivity between human capital, technological mechanisms, and international capital flows [Source: Audio, Strategic Directives].

1.2 The "Graph + RAG" Paradigm

The architecture utilizes a hybrid "Graph + Retrieval-Augmented Generation (RAG)" framework. While standard RAG provides concept connectivity via vector search, the Graph Database enables complex relational querying of nodes (people, entities, technologies). This design is explicitly API-first and gateway-independent, ensuring the system remains operational across various front-end interfaces (e.g., WhatsApp, Open WebUI) without being restricted by specific gateway constraints [Source: Audio].

1.3 The "Dictatorship of Data" Doctrine

Operational integrity is maintained through a pedantic commitment to exhaustive documentation. The system enforces a systemic preference for high-granularity/low-density nodes over data omission. Sparse data is prioritized over missing fields; every potential data point must have a corresponding field in the Markdown repository to ensure the structural integrity of the graph ingestion engine [Categorization Blueprint: 4, 13; Global Footprint: 9].


--------------------------------------------------------------------------------


2. Core Taxonomy and Ontological Standards

2.1 Sectoral Backbone

All entities are classified according to the "Four Pillars of Israeli Life Science" [Categorization Blueprint: 2, 3].

Sub-Sector	Scope and Definition	Israeli Ecosystem Context
Digital Health	Software, hardware, and connectivity for health services [11, 13, 15]	Focus on AI and remote monitoring; ~700 companies [1, 11, 15]
Medical Devices	Physical instruments for diagnosis/treatment [2, 13]	Largest sub-sector; includes imaging and surgical tools [1, 8, 9]
Biotechnology	Biological systems for technological applications [2, 4]	Focus on drug discovery, genomics, and microbiome [4, 14, 20]
Pharma & Therapeutics	Chemical/biological drug development [2, 5, 21]	Focus on small molecules and biologics; clinical trials [2, 8, 21]

2.2 Specialised Verticals (Operational Criteria)

Agents must apply vertical tags based on specific operational criteria [Categorization Blueprint: 5, 14, 15, 16, 17]:

* Bio-Convergence: Synergy between engineering (electronics, software) and biology [2, 10, 11].
* Fem-Tech: Solutions tailored specifically for women’s health (fertility, pelvic wellness) [1, 5].
* Dental-Tech: 3D dental printing, AI diagnostics, and guided oral surgery.
* Trauma-Tech: Physical/mental trauma solutions, prioritized post-conflict (PTSD diagnostics, wound management) [16, 17].
* Mental Health: Neurostimulation, AI therapy, and CBT platforms [5, 17, 21].
* Rehabilitation: Functional restoration via robotic exoskeletons or gait analysis [4, 8].
* Decision Support: AI surgical intelligence or drug interaction tools [7, 15].
* Diagnostics: Rapid pathogen detection, imaging AI, or urinalysis [13, 14, 22].
* Digital Therapeutics: Evidence-based software for chronic disease management [14, 23].
* Remote Monitoring: Home-based vitals tracking and wearable sensors [6, 15, 23].
* Clinical Workflow: Hospital administrative optimization (automated reports, EHR interoperability) [7, 15, 24].
* Assistive Devices: Tools for physical/sensory impairments (smart hearing aids) [15].

2.3 Clinical Domain Mapping (Exhaustive Keywords)

The system utilizes a 20-domain ontology with strict keyword matching [Categorization Blueprint: 25-34]:

1. Oncology: Cancer, Neoplasms, Chemotherapy, Immunotherapy, Solid Tumors.
2. Cardiology: Heart, Cardiovascular, Electrophysiology, Heart Failure, EKG.
3. Neurology: Brain, CNS, Alzheimer's, Parkinson's, Epilepsy, Stroke.
4. Orthopaedics: Musculoskeletal, Spine, Joints, Sports Medicine, Bone health.
5. Gastroenterology: Digestive System, Liver, Gut, Microbiome, Colonoscopy.
6. Endocrinology: Diabetes, Metabolism, Thyroid, Hormonal Disorders.
7. Ophthalmology: Vision, Retina, Glaucoma, Cornea, Eye Surgery.
8. Obstetrics & Gyn.: Women's health, Pregnancy, Fertility, Maternal-fetal.
9. Paediatrics: Neonatal, Child Development, Paediatric Specialties.
10. Dermatology: Skin, Wound Management, Melanoma, Psoriasis.
11. Urology: Kidney, Bladder, Prostate, Renal Failure, Urinalysis.
12. Psychiatry: Mental Health, Trauma, PTSD, Addiction, CBT.
13. Pulmonology: Respiratory, Lung, COPD, Sleep-wake disorders.
14. Infectious Diseases: Virology, Bacteriology, Antimicrobial resistance, HIV.
15. Haematology: Blood, Bone Marrow, Coagulation, Leukemia.
16. Immunology: Autoimmune, Allergies, Immune Mechanism.
17. Radiology: Imaging, MRI, CT, Ultrasound, Nuclear Medicine.
18. Surgery: Intraoperative, Laparoscopy, Robotics, Surgical Intelligence.
19. Nephrology: Kidney function, Dialysis, Renal pathology.
20. Geriatrics: Age-related care, Longevity, Alzheimer's care.


--------------------------------------------------------------------------------


3. Agent #1: The Categorization Agent ('The Specialist')

3.1 Ontological Soul

Agent #1 is the ultimate arbiter of "Drawer Placement." It operates under a Closed-World Assumption: if a category is not present in the pre-defined IATI/SNC ontologies, it does not exist. The agent must yield a system error rather than invent new descriptors [Categorization Blueprint: 1, 2, 5].

3.2 Operational Protocol: 'Foot on Neck'

A mandatory five-step verification loop is required for every entity [Categorization Blueprint: 24, 35-37]:

1. Initialize Search: Query company name and regulatory/subsector markers.
2. Fetch Technical Data: Scrape "Products" or "Technology" pages via Browser Tools.
3. Cross-Reference Databases: Verify against Start-Up Nation Finder and IATI project lists [1, 5, 14].
4. Validate Clinical Claims: Search PubMed or ClinicalTrials.gov for therapeutic evidence.
5. Verify Regulatory Class: Identify FDA Class I, II, or III status; this dictates sub-sector hierarchy (e.g., SaMD vs. pure hardware).

3.3 The 'Dominant Value' Rule

For ambiguous technologies, prioritize the Mechanism of Action. If the innovation is software-based (e.g., AI diagnostics via camera), it is Digital Health; if a proprietary physical sensor is the core value, it is a Medical Device [Categorization Blueprint: 6, 13, 22].


--------------------------------------------------------------------------------


4. Agent #5: The Personal Profiling Agent (PPA)

4.1 Career DNA Mapping

The PPA maps high-impact human capital, focusing on the intersection of military excellence, academic research, and clinical leadership [Personal Profiling: 1, 4, 6].

4.2 Multi-Layered Search Protocol

1. Professional Layer: LinkedIn for titles and employment history [2, 37].
2. Academic & Scientific Layer: PubMed/ResearchGate for publication counts and research keywords [26, 39, 40].
3. IP Layer: Patent databases to identify inventor-level technical contributions [3, 17, 44].
4. Clinical Trials Layer: Link MDs/PIs to specific validation efforts via ClinicalTrials.gov [16, 45].

4.3 Archetype Recognition

* The Military-Tech Disruptor (Talpiot Archetype): Engineering/Physics leaders from elite IDF units (8200, Talpiot, IAF) transitioning to deep-tech health ventures [Personal Profiling: 4, 5, 11].
* The Clinical-Entrepreneurial Hybrid (Physician-Founder): Hospital department heads or MDs bridging the gap between clinical operations and commercial innovation [Personal Profiling: 7, 8].
* The Academic-Visionary (Technion-Weizmann Axis): Researchers with deep PhD backgrounds in Bio-convergence or computer science leading translational medicine [Personal Profiling: 23, 28].


--------------------------------------------------------------------------------


5. Agent #8: The Global Footprint Agent

5.1 Identity: Intelligence Officer for Expansion

Operating with Pedantic Scepticism, Agent #8 documents international presence based only on verified physical evidence. It requires a minimum of two independent sources for verification of physical offices or distributor agreements [Global Footprint: 1, 8, 9].

5.2 Geographical Markets Taxonomy [Global Footprint: 5-7, 10-29]

* North America: Primary focus; requires FDA/Health Canada markers [18, 24].
* Western Europe: Focus on CE marking and NHS/Swiss system integration [20, 22, 47].
* Japan: PMDA navigation; strategic partnerships with Sompo or Itochu [12, 25, 26].
* APAC: TGA approvals and regional distribution hubs [23, 24].
* MENA: Post-Abraham Accords Gulf partnerships (Phoenix Capital) [6, 23, 28].
* Other Regions: LATAM (telehealth), China (Ping An), India (hardware), Eastern Europe (trial hubs).

5.3 Presence Type Classification

Presence Type	Operational Definition	Primary Data Indicators
International Pilot	Foreign clinical trials	Mayo Clinic or Charité press releases; IIA grants [9, 30, 31].
Subsidiary / Office	Physical overseas HQ	LinkedIn HQ data; local registries; business addresses [32, 33, 34].
Distributor / Reseller	Contract with local firms	Announcements with Inter Medico or MSE Group [6, 18, 35].
Attaché Outreach	Formal trade delegations	UK-Israel Tech Hub (TeXchange) or Mini-MIXiii missions [16, 20, 21].


--------------------------------------------------------------------------------


6. Agent #10: The Official Corporate Records Agent ('The Registrar')

6.1 The Legal Ground Truth

Acts as the "Legal Archivist," ignoring marketing narratives to find registered legal names and IDs via the Israel Registrar of Companies [Official Records: 1-5].

6.2 Corporate Status Taxonomy

Entities must be classified into one of six mandatory statuses: 1. Active, 2. Closed/Inactive, 3. Acquired, 4. Public (IPO), 5. Stealth Mode, 6. Dissolved/Liquidated [Official Records: 1, 12, 14-24].

6.3 The 'Delaware Flip' Detection & Entity Types

Must identify double-entity structures (Israeli Ltd vs. Delaware C-Corp) for investment mapping [Official Records: 21, 25-28]. Mandatory entity types include:

* Israeli Ltd / ח.פ: Standard private company [2, 8].
* Non-Profit / חל"צ: Registered non-profit or Public Benefit Company [30, 31].
* Partnership: Registered legal partnership [1, 33].


--------------------------------------------------------------------------------


7. Supporting Research Agents: Functional Briefs

* Agent #2: Website Analysis Agent: Decodes UVPs and identifies "Marketing Gaps"—strategic signals where deep R&D exists but a poor digital interface suggests a need for Swiss engineering services [Strategic Directives: Ch 2].
* Agent #3: LinkedIn Employee Search Agent: Tracks "Growth Delta" (rapid headcount increases) and seniority levels (VP R&D, Lead Engineer) [Strategic Directives: Ch 3].
* Agent #4: Investment & Funding Agent: Maps funding "DNA" and IIA grants (Seed to Series D) [Strategic Directives: Ch 4].
* Agent #6: Regulatory & Clinical Agent: Maps FDA 510(k) vs. PMA and EU MDR compliance [Strategic Directives: Ch 6].
* Agent #7: Executive Contact Agent ('The Hunter'): Mandates a Waterfall Enrichment workflow: Lusha (Israeli/EU accuracy) -> Apollo.io (broad reach) -> Hunter.io (verification) [Strategic Directives: Ch 7].
* Agent #9: Commercialisation Stage Agent: Determines lifecycle stage (Concept, Clinical, or Commercial) [Strategic Directives: Ch 9].


--------------------------------------------------------------------------------


8. Operational Framework and Tool Mastery

8.1 Browser-First Methodology

Agents are strictly forbidden from relying on internal LLM training data. Real-time digital reconnaissance via Browser and Web Search tools is a hard constraint [Global Footprint: 32, 33, 40].

8.2 Deployment and Failover Strategy

The system requires a Mac Mini or VPS (Apple Silicon/GPU preferred) running Open WebUI. This infrastructure serves as a local LLM failover strategy, ensuring that small, specialized models can query the graph if external API services (Claude/OpenAI) experience outages [Source: Audio].


--------------------------------------------------------------------------------


9. Data Ingestion & Markdown Template Standards

9.1 The "100 Section" Rule

All agents must adopt the following Universal Template. Fields must never be deleted; unavailable data is marked "N/A" to facilitate gap analysis in the knowledge graph [Official Records: 4, 13; Global Footprint: 9].

# [Entity Name]
## 1. Identity & Legal Records
* Legal Name: [Official Records Agent]
* H.P. Number: [Official Records Agent]
* Delaware Entity: [Official Records Agent]
* Status: [Active/Acquired/etc.]

## 2. Taxonomy & Clinical Domain
* Sub-Sector: [Categorization Agent]
* Specialized Vertical: [Categorization Agent]
* Primary Clinical Domain: [Categorization Agent]
* Clinical Keywords: [Categorization Agent]

## 3. Human Capital Profile
* Founder Archetype: [Military-Tech/Physician/Academic]
* Leadership Career DNA: [PPA Agent]

## 4. International Footprint
* Target Regions: [Global Footprint Agent]
* Presence Type: [Pilot/Subsidiary/Attaché]
* Regulatory Status: [FDA/CE/PMDA]

## 5. Strategic Intelligence
* Marketing Gaps: [Website Analysis Agent]
* Growth Delta: [LinkedIn Agent]
* Funding DNA: [Investment Agent]

## 6. Source Verification & Traceability
* Source 1: [Link]
* Source 2: [Link]
* Confidence Score: [1-10]



