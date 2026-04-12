"""RAG service — manages the medical knowledge vector store."""
from __future__ import annotations

import os
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("service.rag")

# Built-in medical knowledge seeds
MEDICAL_KNOWLEDGE_SEEDS: list[dict[str, Any]] = [
    {
        "content": "Wells Score for DVT: active cancer (+1), paralysis/paresis/cast (+1), bedridden >3 days or major surgery within 12 weeks (+1), localized tenderness (+1), entire leg swelling (+1), calf swelling >3cm compared with asymptomatic leg (+1), pitting edema confined to symptomatic leg (+1), collateral superficial veins (+1), previous DVT (+1), alternative diagnosis at least as likely (-2). Score ≥2: high probability (53%). Score 1: moderate (17%). Score 0: low (5%).",
        "source": "Wells DVT Criteria",
        "category": "clinical_decision_rule",
    },
    {
        "content": "HEART Score for MACE risk in chest pain: History (highly suspicious=2, moderately suspicious=1, slightly suspicious=0), EKG (significant ST depression=2, non-specific repolarization=1, normal=0), Age (≥65=2, 45-64=1, <45=0), Risk factors (≥3 or known atherosclerosis=2, 1-2 risk factors=1, none=0), Troponin (>3x normal=2, 1-3x=1, normal=0). Score ≤3: low risk (0.9-1.7% MACE). Score 4-6: moderate (12-16.6%). Score ≥7: high (50-65%).",
        "source": "HEART Score",
        "category": "clinical_decision_rule",
    },
    {
        "content": "Pneumonia Severity Index (PSI/PORT Score) for community-acquired pneumonia: Age (men: age in years; women: age -10), nursing home resident (+10), neoplastic disease (+30), liver disease (+20), CHF (+10), cerebrovascular disease (+10), renal disease (+10), altered mental status (+20), RR ≥30 (+20), SBP <90 (+20), temp <35 or ≥40 (+15), HR ≥125 (+10), pH <7.35 (+30), BUN ≥30 (+20), sodium <130 (+20), glucose ≥250 (+10), hematocrit <30% (+10), PO2 <60 (+10), pleural effusion (+10). Class I (<50): outpatient. Class II (51-70): outpatient. Class III (71-90): brief inpatient. Class IV (91-130): inpatient. Class V (>130): ICU consideration.",
        "source": "PSI/PORT Score for CAP",
        "category": "clinical_decision_rule",
    },
    {
        "content": "CHA2DS2-VASc Score for AFib stroke risk: Congestive heart failure (+1), Hypertension (+1), Age ≥75 (+2), Diabetes mellitus (+1), Stroke/TIA history (+2), Vascular disease (+1), Age 65-74 (+1), Sex category female (+1). Score 0 (male): anticoagulation not recommended. Score 1 (male) or 1-2 (female): anticoagulation may be considered. Score ≥2 (male) or ≥3 (female): anticoagulation recommended (NOAC preferred over warfarin).",
        "source": "CHA2DS2-VASc Score",
        "category": "clinical_decision_rule",
    },
    {
        "content": "AHA/ACC Hypertension Guidelines (2017): Normal: <120/80 mmHg. Elevated: 120-129/<80. Stage 1 HTN: 130-139/80-89 (lifestyle changes ± medication if 10-year ASCVD ≥10%). Stage 2 HTN: ≥140/90 (lifestyle + medications). Hypertensive crisis: >180/120. First-line medications: thiazide diuretics, calcium channel blockers, ACE inhibitors or ARBs. Beta-blockers for compelling indications (HF, post-MI, angina). Target BP: <130/80 for most patients.",
        "source": "AHA/ACC Hypertension Guidelines 2017",
        "category": "clinical_guideline",
    },
    {
        "content": "ADA Diabetes Standards 2024: Diagnostic criteria: Fasting glucose ≥126 mg/dL, 2-hr glucose ≥200 mg/dL on OGTT, HbA1c ≥6.5%, random glucose ≥200 with symptoms. Prediabetes: fasting 100-125, OGTT 140-199, HbA1c 5.7-6.4%. Treatment targets: HbA1c <7% for most patients (<8% for elderly/comorbid), BP <130/80, LDL <70 mg/dL. First-line: metformin. Add-on: GLP-1 agonists (cardioprotective), SGLT-2 inhibitors (renal/cardiac protection), DPP-4 inhibitors, sulfonylureas.",
        "source": "ADA Standards of Medical Care in Diabetes 2024",
        "category": "clinical_guideline",
    },
    {
        "content": "Warfarin drug interactions (major): NSAIDs — increased bleeding risk; avoid concurrent use or monitor INR closely. Amiodarone — dramatically increases warfarin effect; reduce warfarin dose 30-50% and monitor INR frequently. Fluconazole and azole antifungals — increase warfarin effect significantly. Rifampin — decreases warfarin effect; INR may drop substantially. Vitamin K-containing foods (leafy greens) — decrease warfarin effect. Antibiotics (especially fluoroquinolones, metronidazole) — increase warfarin effect by altering gut flora.",
        "source": "Clinical Pharmacology - Warfarin Interactions",
        "category": "drug_interaction",
    },
    {
        "content": "QT-prolonging medications and Torsades de Pointes risk: High risk: amiodarone, sotalol, dofetilide, haloperidol (IV), methadone, quinidine, procainamide. Moderate risk: azithromycin, fluoroquinolones (especially moxifloxacin), ondansetron, tricyclic antidepressants, antipsychotics (quetiapine, ziprasidone). Risk factors for TdP: female sex, hypokalemia, hypomagnesemia, bradycardia, congenital long QT syndrome, renal/hepatic failure. Monitoring: baseline QTc; if QTc >500ms or increases >60ms, reassess therapy.",
        "source": "CredibleMeds QTDrugs Database",
        "category": "drug_interaction",
    },
    {
        "content": "ACE inhibitor/ARB contraindications and cautions: Contraindicated in pregnancy (teratogenic — causes fetal renal dysgenesis, oligohydramnios). Bilateral renal artery stenosis: can precipitate acute kidney injury — avoid or use with extreme caution. Hyperkalemia risk: use caution with potassium supplements, potassium-sparing diuretics (spironolactone, amiloride), or other RAA inhibitors. ACE inhibitor cough (occurs in ~10-20%): switch to ARB. Angioedema: history of ACE inhibitor-induced angioedema is contraindication; ARBs may also cause angioedema in ~0.1% but generally safe.",
        "source": "Clinical Pharmacology - RAAS Inhibitors",
        "category": "drug_interaction",
    },
    {
        "content": "Acute chest pain differential diagnosis: Cardiac: ACS (STEMI, NSTEMI, unstable angina), pericarditis, myocarditis, aortic dissection, cardiac tamponade. Pulmonary: pulmonary embolism, pneumothorax, plpneumonia, pleuritis. GI: GERD, esophageal spasm, peptic ulcer, Mallory-Weiss tear, esophageal perforation. Musculoskeletal: costochondritis, rib fracture, muscle strain. Other: herpes zoster, anxiety/panic disorder. Life-threatening causes to exclude first: aortic dissection (tearing back pain, BP discrepancy), STEMI (ST elevation, troponin rise), massive PE (hypoxia, right heart strain), tension pneumothorax (absent breath sounds, tracheal deviation).",
        "source": "Emergency Medicine - Chest Pain Evaluation",
        "category": "differential_diagnosis",
    },
    {
        "content": "Acute abdominal pain evaluation framework: RUQ: biliary colic, acute cholecystitis, hepatitis, Fitz-Hugh-Curtis, peptic ulcer. RLQ: appendicitis, Meckel's diverticulum, ovarian pathology, inguinal hernia, psoas abscess. LUQ: splenic pathology, gastric pathology, pancreatitis tail. LLQ: diverticulitis, ovarian pathology, inguinal hernia, colon cancer. Diffuse/central: bowel obstruction, mesenteric ischemia, IBD, peritonitis. Surgical emergency signs: peritoneal signs (rigidity, rebound), absent bowel sounds, signs of hemodynamic instability. Murphy's sign positive: cholecystitis. Rovsing's sign: appendicitis. McBurney's point tenderness: appendicitis.",
        "source": "Surgical Gastroenterology - Abdominal Pain",
        "category": "differential_diagnosis",
    },
    {
        "content": "Sepsis management (Surviving Sepsis Campaign 2021): Definition: life-threatening organ dysfunction caused by dysregulated host response to infection. Septic shock: sepsis + vasopressor requirement + lactate >2 mmol/L. 1-hour bundle: measure lactate (re-measure if >2), obtain blood cultures before antibiotics, administer broad-spectrum antibiotics, give 30mL/kg IV crystalloid for hypotension or lactate ≥4, apply vasopressors if hypotensive during/after fluids to maintain MAP ≥65. Source control within 6-12 hours. Norepinephrine first-line vasopressor. Corticosteroids for refractory septic shock.",
        "source": "Surviving Sepsis Campaign 2021",
        "category": "clinical_guideline",
    },
    {
        "content": "Anemia classification and workup: Microcytic (MCV <80): iron deficiency anemia (low ferritin, low iron, high TIBC), thalassemia (normal/low ferritin, target cells), anemia of chronic disease (normal/high ferritin), sideroblastic anemia. Normocytic (MCV 80-100): acute blood loss, hemolysis (high LDH, indirect bilirubin, low haptoglobin, high reticulocyte count), aplastic anemia, CKD, anemia of chronic disease. Macrocytic (MCV >100): B12 deficiency (low B12, hypersegmented neutrophils), folate deficiency (low folate), hypothyroidism, liver disease, medications (methotrexate, hydroxyurea, AZT), reticulocytosis. Initial workup: CBC with differential, reticulocyte count, peripheral smear, iron studies, B12, folate, TSH.",
        "source": "Hematology - Anemia Classification and Workup",
        "category": "diagnostic_approach",
    },
    {
        "content": "COPD GOLD staging (spirometry-based): GOLD 1 (Mild): FEV1 ≥80% predicted. GOLD 2 (Moderate): 50% ≤ FEV1 <80%. GOLD 3 (Severe): 30% ≤ FEV1 <50%. GOLD 4 (Very Severe): FEV1 <30%. COPD exacerbation management: short-acting bronchodilators (SABA + SAMA), systemic corticosteroids (prednisolone 40mg x5 days), antibiotics if purulent sputum or increase in dyspnea/sputum volume, supplemental O2 (target SpO2 88-92%), NIV for acute hypercapnic failure. Chronic management: LABA+LAMA (first-line for symptomatic patients), add ICS if blood eosinophils ≥300 or frequent exacerbations.",
        "source": "GOLD COPD Guidelines 2023",
        "category": "clinical_guideline",
    },
    {
        "content": "Thyroid function interpretation: TSH low + free T4 high: hyperthyroidism (primary). TSH low + free T4 normal: subclinical hyperthyroidism or early/treated hyperthyroidism. TSH high + free T4 low: hypothyroidism (primary). TSH high + free T4 normal: subclinical hypothyroidism. TSH normal + T4 high: possible T3 toxicosis (check free T3). Causes of hyperthyroidism: Graves disease (TSI positive, diffuse goiter, ophthalmopathy), toxic multinodular goiter, toxic adenoma, subacute thyroiditis (painful), silent/postpartum thyroiditis. Causes of hypothyroidism: Hashimoto's thyroiditis (anti-TPO antibodies), post-ablative, medications (amiodarone, lithium, checkpoint inhibitors).",
        "source": "Endocrinology - Thyroid Function Interpretation",
        "category": "diagnostic_approach",
    },
    {
        "content": "Pulmonary embolism diagnosis: Wells Score for PE: clinical signs of DVT (+3), PE most likely diagnosis (+3), HR >100 (+1.5), immobilization ≥3 days or surgery past 4 weeks (+1.5), previous DVT/PE (+1.5), hemoptysis (+1), malignancy (+1). Score >4: high probability — CT pulmonary angiography. Score ≤4: low probability — D-dimer (if negative, PE excluded; if positive, proceed to CTPA). PERC criteria (rule out if all negative, age <50, HR <100, SpO2 ≥95%, no leg swelling, no hemoptysis, no recent surgery/trauma, no prior DVT/PE, no exogenous estrogen). Treatment: therapeutic anticoagulation (NOAC preferred), systemic thrombolysis for massive PE with hemodynamic compromise.",
        "source": "Pulmonology - Pulmonary Embolism Diagnosis and Management",
        "category": "clinical_guideline",
    },
    {
        "content": "Statin drug interactions: Myopathy/rhabdomyolysis risk — CYP3A4 inhibitors (clarithromycin, azithromycin, ketoconazole, itraconazole, ritonavir, diltiazem, verapamil, amiodarone, cyclosporine) increase simvastatin and lovastatin levels significantly. Avoid simvastatin >20mg with amlodipine/diltiazem. Gemfibrozil + statins: significantly increases myopathy risk; prefer fenofibrate if combination needed. Colchicine + statins: increased myopathy risk. Signs of statin myopathy: myalgias, weakness, elevated CK; rhabdomyolysis: CK >10x ULN, myoglobinuria, risk of AKI. Pravastatin and rosuvastatin have fewer CYP3A4 interactions.",
        "source": "Clinical Pharmacology - Statin Interactions",
        "category": "drug_interaction",
    },
    {
        "content": "Acute kidney injury (AKI) criteria (KDIGO): Stage 1: creatinine ≥0.3 mg/dL increase within 48h, or 1.5-1.9x baseline, or UO <0.5 mL/kg/h for 6-12h. Stage 2: creatinine 2-2.9x baseline, or UO <0.5 mL/kg/h for ≥12h. Stage 3: creatinine ≥3x baseline, or increase ≥4 mg/dL, or initiation of renal replacement therapy, or UO <0.3 mL/kg/h for ≥24h. Causes — prerenal: hypovolemia, decreased cardiac output, hepatorenal. Intrinsic renal: ATN (ischemic, nephrotoxic), GN, interstitial nephritis, vascular. Postrenal: obstruction. Nephrotoxic drugs to monitor: NSAIDs, aminoglycosides, vancomycin, contrast, cisplatin, amphotericin B.",
        "source": "Nephrology - AKI Classification KDIGO 2012",
        "category": "clinical_guideline",
    },
    {
        "content": "Ottawa rules for ankle/foot imaging: Ankle X-ray needed if pain in malleolar zone AND bone tenderness at posterior tip or inferior tip of either malleolus, OR inability to weight bear immediately and in ED. Foot X-ray needed if pain in midfoot zone AND bone tenderness at base of 5th metatarsal or navicular, OR inability to weight bear. Ottawa knee rule: X-ray needed if age ≥55, or tenderness at fibular head, isolated tenderness of patella, inability to flex knee to 90°, inability to weight bear. Sensitivity approaches 100% when applied correctly.",
        "source": "Emergency Medicine - Ottawa Rules",
        "category": "clinical_decision_rule",
    },
    {
        "content": "Antimicrobial stewardship principles: Community-acquired pneumonia (mild): amoxicillin 1g TID or doxycycline 100mg BID (5 days). Moderate CAP: amoxicillin-clavulanate + macrolide, or respiratory fluoroquinolone (levofloxacin 750mg). Severe CAP (ICU): beta-lactam + macrolide OR respiratory fluoroquinolone. UTI (uncomplicated cystitis): nitrofurantoin 100mg BID x5d, trimethoprim-sulfamethoxazole 160/800mg BID x3d (if local resistance <20%), fosfomycin 3g single dose. Avoid fluoroquinolones for uncomplicated UTI. Skin/soft tissue: clindamycin or TMP-SMX for CA-MRSA. Duration matters: shorter courses (5 days for CAP, 3-5 days for UTI) are as effective and reduce resistance.",
        "source": "IDSA Antimicrobial Stewardship Guidelines",
        "category": "clinical_guideline",
    },
]


class RAGService:
    """Manages the medical knowledge vector store and semantic retrieval."""

    def __init__(self) -> None:
        emb_kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            emb_kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.embeddings = OpenAIEmbeddings(**emb_kwargs)
        self.vectorstore: Chroma | None = None
        self._initialized = False

    async def initialize(self, persist_dir: str | None = None) -> None:
        """Load existing vectorstore or create and seed a new one."""
        persist_dir = persist_dir or settings.CHROMA_PERSIST_DIRECTORY
        os.makedirs(persist_dir, exist_ok=True)

        try:
            self.vectorstore = Chroma(
                collection_name="medical_knowledge",
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
            )
            count = self.vectorstore._collection.count()
            logger.info("rag_initialized", document_count=count, persist_dir=persist_dir)

            if count == 0:
                logger.info("rag_seeding", message="Seeding medical knowledge base...")
                await self.seed_medical_knowledge()
        except Exception as exc:
            logger.error("rag_initialization_failed", error=str(exc))
            raise
        self._initialized = True

    async def seed_medical_knowledge(self) -> None:
        """Populate the vector store with built-in medical knowledge."""
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized")

        documents = [
            Document(
                page_content=seed["content"],
                metadata={
                    "source": seed["source"],
                    "category": seed["category"],
                },
            )
            for seed in MEDICAL_KNOWLEDGE_SEEDS
        ]
        self.vectorstore.add_documents(documents)
        logger.info("rag_seeded", document_count=len(documents))

    async def add_documents(self, documents: list[Document]) -> None:
        """Add custom documents to the knowledge base."""
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized")
        self.vectorstore.add_documents(documents)

    async def search(self, query: str, k: int = 5) -> list[Document]:
        """Semantic similarity search over the knowledge base."""
        if not self.vectorstore:
            return []
        return self.vectorstore.similarity_search(query, k=k)

    def get_retriever(self, k: int = 5):
        """Return a LangChain retriever interface."""
        if not self.vectorstore:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")
        return self.vectorstore.as_retriever(search_kwargs={"k": k})

    @property
    def is_initialized(self) -> bool:
        return self._initialized
