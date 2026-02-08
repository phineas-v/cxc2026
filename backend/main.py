from fastapi import FastAPI, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from backboard import BackboardClient # Use the SDK!
from PIL import Image
import io
import asyncio # For startup logic
from elevenlabs.client import ElevenLabs
import os
import base64

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyB0UEAXKvqRdp3wzoFV40cMO6PJP27RAyM"
BACKBOARD_API_KEY = "espr_ZF0hWS5sETRl_kmaNsvywxVJuXKu9IFvtC--W28S2Lk"

# 1. Setup Gemini ("The Eyes")
genai.configure(api_key=GOOGLE_API_KEY)
vision_model = genai.GenerativeModel('gemini-2.5-flash')

# 2. Setup Backboard ("The Brain")
bb_client = BackboardClient(api_key=BACKBOARD_API_KEY)

# 3. Setup ElevenLabs ("The Voice" - optional for future use)
elevenlabs = ElevenLabs(
  api_key=ELEVENLABS_API_KEY,
)

# Global variables to store our AI Agent IDs
assistant_id = None
thread_id = None

app = FastAPI()

# Allow React to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STARTUP EVENT ---
# This runs once when the server starts to set up the Backboard Agent
@app.on_event("startup")
async def startup_event():
    global assistant_id, thread_id
    print("🤖 Initializing AI Agent...")

    # Print out ListModels
    # models = genai.list_models()
    # print(f"Available models: {[model.name for model in models]}") # Debug print

    # Create the Health Expert
    assistant = await bb_client.create_assistant(
        name="Health Analyzer",
        system_prompt="""You are a evaluator for a consumer ingredient-scanning app. Your job is to score how supportive a product’s ingredients are for steadier cognitive performance (focus/attention/mental energy) using ONLY the ingredient list provided (no nutrition facts unless explicitly included). Be conservative, avoid medical claims, and keep decisions explainable and deterministic."""
    )
    assistant_id = assistant.assistant_id
    
    # Create a conversation thread
    thread = await bb_client.create_thread(assistant_id)
    thread_id = thread.thread_id
    print("✅ Agent Ready!")

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...), lens: str = Form(...), user_profile: str = Form(None)):
    # --- STEP 1: READ IMAGE ---
    print("📸 Receiving image...")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # --- STEP 2: GEMINI (EXTRACT TEXT) ---
    print("👀 Gemini is reading the label...")
    ocr_response = vision_model.generate_content([
        "Extract list of ingredients from the text. Output the list only and lower case the ingredients. Make it fast", 
        image
    ])
    extracted_text = ocr_response.text
    print(f"📝 Extracted Text: {extracted_text[:50]}...") # Print first 50 chars

    # --- STEP 3: BACKBOARD (ANALYZE HEALTH) ---
    print("🧠 Backboard is analyzing health...")
    
    # We send the text from Gemini into Backboard according to lens
    if lens == "focus":
        instruction = """
You are “Focus Score” evaluator for a consumer ingredient-scanning app. Your job is to score how supportive a product’s ingredients are for steadier cognitive performance (focus/attention/mental energy) using ONLY the ingredient list provided (no nutrition facts unless explicitly included). Be conservative, avoid medical claims, and keep decisions explainable and deterministic.

GOAL
Given an ingredient list, return:
1) A Focus Score from 0–100 (higher = more supportive of steady focus/mental energy)
2) Values to populate a two-part horizontal bar: Supportive vs Risk (POS vs NEG points)
3) “Top reasons” bullets (✅ positives + ⚠️ concerns) that mention specific ingredients
4) Categorize ALL ingredients into 4 groups:
   - positive_for_lens
   - negative_for_lens
   - mixed_for_lens
   - neutral_for_lens
5) A list of “Lab Labels”: ingredients that the general public may not recognize, with plain-English explanations of what they are and why they’re added (and brief focus relevance)
6) A short list of 4 broad, credible sources consulted (institution/site) and how used
7) Uncertainty notes if ingredients are ambiguous or info is missing

SAFETY + QUALITY RULES (NON-NEGOTIABLE)
- Do NOT claim an ingredient “causes” ADHD/hyperactivity or cures/enhances intelligence.
- You MAY say: “may contribute to energy spikes/crashes,” “often limited by people seeking steadier focus,” “some people are sensitive,” “evidence is mixed,” etc.
- This lens is NOT medical advice; it is an ingredient-based heuristic.
- Never invent ingredients. Only refer to ingredients present.
- Deterministic: same ingredient list → same output.

LENS DEFINITION (FOCUS / STEADY MENTAL ENERGY)
This lens estimates whether the product’s formulation is likely to support steadier attention and mental energy by:
- penalizing ingredient patterns that commonly signal rapid-digesting sweetness, “spike/crash” profiles, and highly engineered sweet taste
- flagging stimulant markers as context-dependent (can increase alertness for many, but may reduce steadiness via jitters/sleep disruption for some)
- rewarding ingredient patterns commonly described as supportive of brain health and steadier energy (e.g., nuts/seeds, whole grains, omega-3 sources) without overclaiming
- recognizing niche-but-legitimate cognitive-support ingredients if present (e.g., creatine), while stating limitations

BROAD SOURCES (LIMIT TO EXACTLY 4)
Use these as broad reference anchors for cautious wording and general nutrition/brain-health context:
1) Harvard Health Publishing (Harvard Medical School) – general health and nutrition guidance
2) Mayo Clinic – general health and nutrition guidance
3) WebMD – general health information (use cautiously; avoid strong claims)
4) Cleveland Clinic – general health and nutrition guidance
IMPORTANT: Do not quote or cite niche blogs. Use these sources to guide conservative, common-sense explanations.

SCORING MODEL (SIMPLE WEIGHTED POINTS)
Start at BASE_SCORE = 50.
Compute POS_POINTS and NEG_POINTS from criteria below (each criterion adds or subtracts points when triggered).
Final score = clamp( BASE_SCORE + POS_POINTS - NEG_POINTS , 0, 100 ).

Bar visualization uses:
- POS_POINTS (supportive)
- NEG_POINTS (risk)
Ratios:
- positive_ratio = POS_POINTS / (POS_POINTS + NEG_POINTS) if total>0 else 0.5
- negative_ratio = NEG_POINTS / (POS_POINTS + NEG_POINTS) if total>0 else 0.5

CRITERIA + WEIGHTS (INGREDIENT-LIST ONLY)
Apply these rules exactly. If a criterion can’t be determined from ingredients_text, treat it as NOT triggered.

A) NEGATIVE (undermines steady focus / increases spike-crash or overstimulation risk)
N1. Sugar is dominant (18)
  Trigger: a sugar term is ingredient #1 or #2
  Sugar terms include: sugar, cane sugar, corn syrup, HFCS, dextrose, glucose, fructose, maltose, invert sugar, honey, agave, molasses, syrup, fruit juice concentrate (when used as sweetener)

N2. Multiple added sugars (12)
  Trigger: 2+ distinct sugar terms anywhere in list

N3. Artificial colors present (10)
  Trigger: Red 40, Yellow 5, Yellow 6, Blue 1, Blue 2, FD&C, “color added”, “artificial color”
  Wording constraint: do NOT claim “causes hyperactivity.” Use: “Some people choose to limit artificial colors; evidence varies.”

N4. Stimulant marker present (8)  [scored as negative for steadiness]
  Trigger: caffeine, guarana, yerba mate, green coffee extract, “energy blend”
  Note: Add caveat that effects vary; scoring reflects steadiness and sleep sensitivity concerns.

N5. Non-nutritive sweeteners present (6)
  Trigger: aspartame, sucralose, acesulfame K, saccharin, neotame, advantame
  stevia/monk fruit: weight 3 (still indicates engineered sweetness)

N6. Highly engineered additive stack (6)
  Trigger: 3+ “engineering markers” appear among flavors/emulsifiers/preservatives/isolate starches
  Examples: “natural flavors”, polysorbate 80, mono- & diglycerides, carrageenan, xanthan gum, sodium benzoate, potassium sorbate, TBHQ, BHT, modified starch, maltodextrin

B) POSITIVE (supports steadier focus / “brain-supportive” cues without overclaiming)
P1. Nuts/seeds present (10)
  Trigger: almonds, walnuts, peanuts, cashews, pistachios, chia, flax, pumpkin seeds, sunflower seeds

P2. Omega-3 source present (10)
  Trigger: fish oil, algae oil, DHA, EPA, flax/chia (ALA sources; optional caveat: conversion varies)

P3. Whole grains / slow-carb cue (6)
  Trigger: oats, whole oats, whole wheat, brown rice, quinoa, barley, bran

P4. Protein-forward cue (6)
  Trigger: eggs, yogurt, milk protein, whey, soy protein, legumes (beans/lentils/chickpeas)
  Note: If “protein isolate” appears, you may still count it as protein-forward but classify as mixed_for_lens.

P5. Creatine present (8)
  Trigger: creatine, creatine monohydrate
  Wording constraint: “Creatine is best known for performance; it has also been studied in cognitive contexts; effects vary.”

P6. No sweeteners (6)
  Trigger: no sugar terms AND no non-nutritive sweeteners

DETERMINISTIC EVALUATION STEPS
1) Normalize ingredient list (lowercase, strip punctuation) and split into items.
2) Detect:
   - sugar_terms_found + positions
   - sweeteners_found
   - colors_found
   - stimulant_terms_found
   - omega3_terms_found
   - nuts_seeds_found
   - whole_grains_found
   - protein_cues_found
   - creatine_found
   - additive_stack_markers_found (flavors/emulsifiers/preservatives/isolate markers)
3) Apply criteria exactly:
   - NEG_POINTS = sum triggered negative criterion weights
   - POS_POINTS = sum triggered positive criterion weights
4) Compute final score: clamp(50 + POS_POINTS - NEG_POINTS, 0, 100)
5) Produce top reasons:
   - Top 3 POS triggers as ✅ bullets (include ingredient names)
   - Top 3 NEG triggers as ⚠️ bullets (include ingredient names + cautious language)
6) Categorize every ingredient into one of:
   - positive_for_lens: nuts/seeds, omega-3 sources, whole grains, protein cues, creatine
   - negative_for_lens: sugar terms, artificial colors, stimulant markers, non-nutritive sweeteners
   - mixed_for_lens: “natural flavors”, “protein isolate”, ambiguous “spices”, certain gums/emulsifiers, caffeine sources (context-dependent), “fruit juice concentrate” (can function as sweetener)
   - neutral_for_lens: salt, water, basic acids (citric acid), basic spices if clearly culinary
7) Identify “Lab Labels” deterministically:
   - Include ingredients likely unfamiliar to the general public, especially:
     a) artificial colors, non-nutritive sweeteners, preservatives, emulsifiers/stabilizers/thickeners, “natural flavors”
     b) refined isolates/reconstituted ingredients (e.g., maltodextrin, modified starch, protein isolate)
     c) chemical-sounding names (common suffix cues: -ate, -ite, -ide, -ose, -ol, -ium, -phosphate, -carbonate, -chloride)
   - Exclude obvious everyday foods: water, salt, sugar, oats, rice, milk, eggs, peanuts, etc. (unless ambiguous)
   - For each lab label, provide:
     - ingredient (exact as listed)
     - plain_english (what it is, in 1 sentence)
     - why_added (its function in foods, in 1 sentence)
     - focus_relevance (1 short sentence using cautious language)
8) Provide sources_consulted with EXACTLY these four sources and how used.

OUTPUT FORMAT (STRICT JSON ONLY)
Return one JSON object (NOTE: JSON portion must use DOUBLE CURLY BRACES):

{{
  "lens": "Focus Score",
  "score": <int 0-100>,
  "bar": {{
    "positive_points": <number>,
    "negative_points": <number>,
    "positive_ratio": <number 0-1>,
    "negative_ratio": <number 0-1>
  }},
  "reasons": {{
    "positives": [ "<✅ ...>", "<✅ ...>", "<✅ ...>" ],
    "concerns": [ "<⚠️ ...>", "<⚠️ ...>", "<⚠️ ...>" ]
  }},
  "criteria_hits": [
    {{ "id": "N1", "name": "Sugar is dominant", "direction": "negative", "points": 18, "evidence": "sugar listed as ingredient #1" }}
  ],
  "ingredients_breakdown": {{
    "positive_for_lens": [ "<ingredient>", ... ],
    "negative_for_lens": [ "<ingredient>", ... ],
    "mixed_for_lens": [ "<ingredient>", ... ],
    "neutral_for_lens": [ "<ingredient>", ... ]
  }},
  "lab_labels": [
    {{
      "ingredient": "<string>",
      "plain_english": "<string>",
      "why_added": "<string>",
      "focus_relevance": "<string>"
    }}
  ],
  "detected_signals": {{
    "first_ingredient": "<string>",
    "ingredient_count": <int>,
    "sugars": {{ "terms": [..], "positions": [..] }},
    "sweeteners": [..],
    "colors": [..],
    "stimulants": [..],
    "omega3_sources": [..],
    "nuts_seeds": [..],
    "whole_grains": [..],
    "protein_cues": [..],
    "creatine": <true/false>,
    "additive_stack_markers": [..]
  }},
  "sources_consulted": [
    {{ "source": "Harvard Health Publishing (Harvard Medical School)", "how_used": "Broad nutrition and brain-health framing; supports conservative language on diet patterns and energy." }},
    {{ "source": "Mayo Clinic", "how_used": "Broad nutrition and wellness framing; used for cautious, consumer-friendly explanations." }},
    {{ "source": "WebMD", "how_used": "General health reference for plain-language descriptions; do not use for strong causal claims." }},
    {{ "source": "Cleveland Clinic", "how_used": "Broad clinical health guidance framing; supports cautious explanations about sugar, stimulants, and diet quality." }}
  ],
  "notes": [ "<uncertainty/caveats>" ]
}}

USER INPUT
ingredients_text: "<string>"

Now evaluate the provided ingredients_text according to this Focus Score lens and return STRICT JSON ONLY (using the DOUBLE CURLY BRACES structure above)."""
    elif lens == "real_food":
        instruction = """
You are “Real Food Score” evaluator for a consumer ingredient-scanning app. Your job is to score how “real-food / minimally processed” a packaged product is using ONLY the ingredient list provided (no nutrition facts unless explicitly included). Be conservative, avoid medical claims, and keep decisions explainable and deterministic.

GOAL
Given an ingredient list, return:
1) A Real Food Score from 0–100 (higher = more minimally processed / closer to whole foods)
2) Values to populate a two-part horizontal bar: Supportive vs Risk (POS vs NEG points)
3) “Top reasons” bullets (✅ positives + ⚠️ concerns) that mention specific ingredients
4) A full ingredient categorization into 4 groups:
   - positive_for_lens (supports “real food / low-processed”)
   - negative_for_lens (signals high processing / ultra-processed formulation)
   - mixed_for_lens (context-dependent or umbrella terms)
   - neutral_for_lens (neither clearly signals processing nor whole-food-ness)
5) A list of “Lab Labels”: ingredients that the general public may not recognize, with plain-English explanations of what they are and why they’re added
6) Credible sources consulted (org + document family) and brief “how used”
7) Uncertainty notes if ingredient list is incomplete/ambiguous

SAFETY + QUALITY RULES (NON-NEGOTIABLE)
- Do NOT claim an ingredient “causes” disease or conditions.
- Additives can be “permitted/regulated” yet still be markers of processing complexity. Frame accordingly.
- Never invent ingredients. Only use what appears in the list.
- If an ingredient is ambiguous (e.g., “spices,” “natural flavors”), treat as a processing signal with uncertainty.
- Deterministic: same ingredient list → same score.

LENS DEFINITION (REAL FOOD / LOW-PROCESSED)
This lens estimates how close the product is to minimally processed whole foods vs “ultra-processed” formulations.
More whole-food ingredients + fewer industrial additives + simpler formulation → higher score.

CREDIBLE FOUNDATIONAL REFERENCES (USE THESE CONCEPTS)
Use these as conceptual anchors; do not over-quote:
- NOVA food processing framework (markers of ultra-processed foods: flavors, colors, emulsifiers, sweeteners, reconstituted ingredients)
- Health Canada – Lists of Permitted Food Additives (regulatory framing; avoid “unsafe” claims)
- FDA – Food additives/GRAS overview (regulatory framing; avoid overstating risk)
- EFSA – Food additives topic pages (regulatory/scientific framing)

SCORING MODEL (WEIGHTED, EXPLAINABLE)
Start BASE_SCORE = 100.
Compute PENALTIES (processing markers) and BONUSES (whole-food/minimal formulation signals).
Final score = clamp( BASE_SCORE - PENALTY_POINTS + BONUS_POINTS , 0, 100 ).

Compute for bar visualization:
- POS_POINTS = BONUS_POINTS
- NEG_POINTS = PENALTY_POINTS

CRITERIA + WEIGHTS
Apply exactly these rules.

A) PENALTIES (processing / ultra-processed markers)
P1. Artificial colors / color additives present (12)
  Trigger: “Red 40”, “Yellow 5”, “Blue 1”, “FD&C”, “color added”, “artificial color”

P2. Non-nutritive sweeteners present (10)
  Trigger: aspartame, sucralose, acesulfame K, saccharin, neotame, advantame
  Note: stevia/monk fruit penalty = 6 (still a processing marker)

P3. Added sugar indicators (up to 18 by prominence)
  Identify sugar terms: sugar, cane sugar, corn syrup, HFCS, dextrose, glucose, fructose, maltose, invert sugar, honey, agave, molasses, syrup, fruit juice concentrate (when used as sweetener)
  - If sugar term is ingredient #1 or #2: 18
  - Else if 2+ distinct sugar terms: 12
  - Else if 1 sugar term later: 6

P4. “Flavors” marker (8)
  Trigger: “natural flavors”, “artificial flavors”, “flavoring”

P5. Emulsifiers / texture agents stack (0–12 by count)
  Examples: polysorbate 80, mono- & diglycerides, lecithin, carrageenan, xanthan gum, guar gum, cellulose gum, DATEM, modified cellulose
  - 1–2: 4
  - 3–4: 8
  - 5+: 12

P6. Preservatives marker (0–10 by count)
  Examples: sodium benzoate, potassium sorbate, calcium propionate, BHA/BHT, TBHQ, sodium nitrite/nitrate
  - 1: 5
  - 2+: 10

P7. Refined isolates / reconstituted ingredients (0–10)
  Examples: maltodextrin, modified starch, protein isolate, isolated fiber, inulin/chicory fiber (context-dependent), “whey protein isolate”
  - 1–2: 5
  - 3+: 10

P8. Ingredient list complexity (0–10)
  - >15 ingredients: 10
  - 10–15: 6
  - <10: 0

P9. First-ingredient quality penalty (0–10)
  - If first ingredient is sugar/syrup OR a refined isolate/starch: 10
  - If first ingredient is refined flour or refined oil: 6
  - If first ingredient is a whole food: 0

B) BONUSES (whole-food / minimal formulation signals)
B1. Whole-food first ingredient (12)
  Trigger: ingredient #1 is a recognizable whole food (oats, milk, peanuts, beans, fruit, etc.)

B2. Short “kitchen-like” list (8)
  Trigger: ingredient_count < 10 AND no colors AND no “flavors” AND emulsifiers <= 2 AND preservatives = 0

B3. Whole-food density (0–10)
  Estimate proportion of ingredients that are recognizable whole foods vs additives/isolate markers:
  - High: +10
  - Medium: +6
  - Low: +0
  Provide short justification.

B4. No sweeteners (6)
  Trigger: no added sugar terms AND no non-nutritive sweeteners

B5. Minimal additive stack (4)
  Trigger: emulsifiers=0 AND preservatives=0 AND no “flavors”

DETERMINISTIC EVALUATION STEPS
1) Normalize ingredient list (lowercase, strip punctuation) and split into items.
2) Detect and list: sugars + positions, sweeteners, colors, flavors, emulsifiers, preservatives, isolates, ingredient_count, first_ingredient.
3) Apply penalties/bonuses exactly.
4) Compute score, POS_POINTS, NEG_POINTS.
5) Select top 3 penalties + top 3 bonuses as reasons (largest points).
6) Categorize every ingredient into 4 groups:
   - positive_for_lens: recognizable whole foods / simple culinary ingredients that support minimal processing
   - negative_for_lens: additives/sweeteners/colors/preservatives/isolate markers
   - mixed_for_lens: umbrella/ambiguous terms (e.g., “spices”, “natural flavors”, “flavoring”, “enriched flour” sometimes) or context-dependent items (e.g., lecithin, inulin)
   - neutral_for_lens: salt, water, basic acids, standard seasonings that don’t strongly signal processing
7) Identify “Lab Labels” deterministically:
   - Include ingredients that are likely unfamiliar to the general public, especially:
     a) preservatives, emulsifiers, stabilizers, thickeners, anti-caking agents, humectants, acidity regulators, firming agents
     b) artificial colors, non-nutritive sweeteners, “natural flavors” / “artificial flavors”
     c) refined isolates/reconstituted ingredients (e.g., maltodextrin, modified starch, protein isolate)
     d) chemical-sounding names (common suffix cues: -ate, -ite, -ide, -ose, -ol, -ium, -phosphate, -carbonate, -chloride)
   - Exclude common kitchen staples unless ambiguous: water, salt, sugar, flour, milk, eggs, butter, olive oil, oats, rice, etc.
   - For each lab label, provide:
     - ingredient (exact as listed)
     - plain_english (what it is, in 1 sentence)
     - why_added (its function in foods, in 1 sentence)
     - common_in (1–3 example product types; e.g., “soft drinks”, “salad dressings”)
8) Provide sources consulted list (org + document family) with “how used”.

OUTPUT FORMAT (STRICT JSON ONLY)
Return one JSON object (NOTE: JSON portion must use DOUBLE CURLY BRACES):

{{
  "lens": "Real Food Score",
  "score": <int 0-100>,
  "bar": {{
    "positive_points": <number>,
    "negative_points": <number>,
    "positive_ratio": <number 0-1>,
    "negative_ratio": <number 0-1>
  }},
  "reasons": {{
    "positives": [ "<✅ ...>", "<✅ ...>", "<✅ ...>" ],
    "concerns": [ "<⚠️ ...>", "<⚠️ ...>", "<⚠️ ...>" ]
  }},
  "criteria_hits": [
    {{ "id": "P3", "name": "Added sugar indicators", "direction": "negative", "points": <number>, "evidence": "<what triggered it>" }}
  ],
  "ingredients_breakdown": {{
    "positive_for_lens": [ "<ingredient>", ... ],
    "negative_for_lens": [ "<ingredient>", ... ],
    "mixed_for_lens": [ "<ingredient>", ... ],
    "neutral_for_lens": [ "<ingredient>", ... ]
  }},
  "lab_labels": [
    {{
      "ingredient": "<string>",
      "plain_english": "<string>",
      "why_added": "<string>",
      "common_in": ["<string>", "<string>"]
    }}
  ],
  "detected_signals": {{
    "first_ingredient": "<string>",
    "ingredient_count": <int>,
    "sugars": {{ "terms": [..], "positions": [..] }},
    "sweeteners": [..],
    "colors": [..],
    "flavors": [..],
    "emulsifiers": [..],
    "preservatives": [..],
    "isolates": [..]
  }},
  "sources_consulted": [
    {{ "source": "NOVA food processing framework", "how_used": "Defines ultra-processed markers (colors, flavors, emulsifiers, sweeteners, reconstituted ingredients)." }},
    {{ "source": "Health Canada – Lists of Permitted Food Additives", "how_used": "Frames additives as regulated/permitted while still being processing markers." }},
    {{ "source": "FDA – Food additives/GRAS overview", "how_used": "Avoids unsafe claims; permitted additives can still indicate processing." }},
    {{ "source": "EFSA – Food additives topic pages", "how_used": "Reference for additive assessment framing; supports cautious language." }}
  ],
  "notes": [ "<uncertainty/caveats>" ]
}}

USER INPUT
ingredients_text: "<string>"

Now evaluate the provided ingredients_text and return STRICT JSON ONLY (using the DOUBLE CURLY BRACES structure above).
"""
    elif lens == "personal":
        instruction = f"""
You are “Personal Fit Score” evaluator for a consumer ingredient-scanning app. Your job is to score how well a packaged product matches a user’s personal profile using ONLY:
- the ingredient list provided (ingredients_text)
- the user profile object provided ({user_profile})
Do NOT use nutrition facts unless explicitly provided. Be conservative, avoid medical claims, and keep decisions explainable and deterministic.

GOAL
Given ingredients_text + user_profile, return:
1) A Personal Fit Score from 0–100 (higher = better fit for THIS user)
2) Values to populate a two-part horizontal bar: Fits You vs Conflicts (POS vs NEG points)
3) “Top reasons” bullets (✅ positives + ⚠️ concerns) that mention specific ingredients and/or profile toggles
4) Categorize ALL ingredients into 4 groups (relative to THIS user):
   - positive_for_lens
   - negative_for_lens
   - mixed_for_lens
   - neutral_for_lens
5) A list of “Lab Labels”: ingredients that the general public may not recognize, with plain-English explanations of what they are and why they’re added (and brief personal relevance)
6) A short list of broad sources consulted (LIMIT TO EXACTLY 4) and how used
7) Uncertainty notes if ingredients are ambiguous or info is missing

SAFETY + QUALITY RULES (NON-NEGOTIABLE)
- Do NOT diagnose conditions or predict disease risk.
- Do NOT say an ingredient “causes” a condition. Use cautious language: “some people prefer to limit…”, “may be relevant for…”, “often avoided by…”, “evidence varies.”
- If a profile toggle is “medical-ish” (e.g., blood sugar aware), treat it as a preference/consideration, not a diagnosis.
- Never invent ingredients. Only refer to ingredients present.
- Deterministic: same ingredients + same user_profile → same output.

PERSONAL LENS DEFINITION (PERSONAL FIT)
This lens scores “fit” based on:
A) HARD RULES (binary compatibility): dietary rules and allergens/intolerances
B) GOAL WEIGHTS (what the user cares about): e.g., focus, weight loss, real-food preference
C) SENSITIVITIES (optional): caffeine sensitive, dye-free preference, avoid artificial sweeteners
The score reflects ingredient-list signals only. If something can’t be assessed from ingredients alone, state that in notes.

USER PROFILE (INPUT SCHEMA)
user_profile is a JSON-like object with these optional fields:

- goal: one of ["real_food", "steady_focus", "weight_loss", "weight_gain", "build_muscle", "general"]
- dietary_rules: array of ["vegan", "halal", "kosher", "vegetarian"]
- avoid_list: array of preferences such as ["avoid_artificial_colors", "avoid_artificial_sweeteners", "avoid_ultra_processed", "caffeine_sensitive"]
- allergens: array of ["peanut", "tree_nut", "dairy", "gluten", "egg", "shellfish", "sesame", "soy"]
- health_considerations: array of ["blood_sugar_aware"]  (optional; treat as preference)
(If fields are missing, assume empty arrays and goal="general".)

BROAD SOURCES (LIMIT TO EXACTLY 4)
Use these as broad reference anchors for cautious wording:
1) Harvard Health Publishing (Harvard Medical School)
2) Mayo Clinic
3) WebMD (use cautiously; avoid strong claims)
4) Cleveland Clinic

SCORING MODEL (DETERMINISTIC, WEIGHTED)
Start BASE_SCORE = 70.

Compute:
- HARD_FAIL_PENALTY (0–70)
- NEG_POINTS (0+)
- POS_POINTS (0+)

Final score = clamp( BASE_SCORE + POS_POINTS - NEG_POINTS - HARD_FAIL_PENALTY , 0, 100 )

Bar visualization uses:
- POS_POINTS as "fits_you_points"
- (NEG_POINTS + HARD_FAIL_PENALTY) as "conflicts_points"
Ratios:
- fits_you_ratio = fits_you_points / (fits_you_points + conflicts_points) if total>0 else 0.5
- conflicts_ratio = conflicts_points / (fits_you_points + conflicts_points) if total>0 else 0.5

HARD RULES (BIGGEST IMPACT)
H1. Allergen present (HARD_FAIL_PENALTY = 70)
- If ANY selected allergen appears in ingredients, apply 70 penalty and add a major warning in reasons.
- Matching logic: exact match OR common derivatives:
  - dairy: milk, whey, casein, lactose, butter, cream
  - gluten: wheat, barley, rye, malt
  - soy: soy, soy lecithin, soybean oil (flag as mixed if highly refined oils; still relevant)
  - egg: egg, albumen
  - sesame: sesame, tahini
  - nuts: peanut, almond, walnut, cashew, etc.
(If unsure, put in mixed_for_lens and note uncertainty.)

H2. Vegan/Vegetarian conflict (HARD_FAIL_PENALTY = 50)
- Vegan conflicts: milk, whey, casein, egg, gelatin, honey (treat honey as conflict for strict vegan)
- Vegetarian conflicts: gelatin (and obvious meats, if present)
(If ambiguous, note uncertainty.)

H3. Halal/Kosher (HARD_FAIL_PENALTY = 40 IF clear conflict, else 0 with note)
- Only penalize when ingredient is clearly non-compliant (e.g., pork-derived gelatin, lard).
- If unclear (generic “gelatin”), do NOT hard-fail; classify as mixed and add a note: “source not specified.”

GOAL WEIGHTS (WHAT TO OPTIMIZE)
Apply goal-based scoring adjustments using ingredient signals:

G1. goal="real_food" (favor simpler / less engineered lists)
- POS:
  - recognizable whole-food-first ingredient +8
  - short list (<10) +6
- NEG:
  - natural flavors / artificial flavors -6
  - 3+ gums/emulsifiers/preservatives -6
  - artificial colors -8
  - non-nutritive sweeteners -6
  - added sugars prominent (ingredient #1/#2) -10

G2. goal="steady_focus" (favor steadier energy cues)
- POS:
  - nuts/seeds +6
  - omega-3 sources (fish/algae oil, DHA/EPA, flax/chia) +6
  - whole grains (oats, whole wheat, brown rice) +4
  - creatine (if present) +4 (keep cautious)
- NEG:
  - sugar dominant (#1/#2) -12
  - multiple sugar terms -8
  - stimulant markers (caffeine/guarana) -6 (steadiness concern)
  - artificial colors -6 (cautious wording)

G3. goal="weight_loss" (ingredient-list-only; do not claim calorie outcomes)
- POS:
  - protein cues (eggs, yogurt, whey, legumes) +4
  - whole grains +3
  - nuts/seeds +2 (satiety cue; cautious)
- NEG:
  - sugar dominant -10
  - multiple sugars -6
  - engineered sweetener stack -4
(If user wants weight loss, strongly suggest nutrition facts would improve accuracy in notes.)

G4. goal="weight_gain"
- POS:
  - nuts/nut butters/oils +4
  - protein cues +4
  - whole grains +3
- NEG:
  - none required; still apply general “overly engineered” negatives lightly (-2 to -4) if goal isn’t “real_food”

G5. goal="build_muscle"
- POS:
  - protein cues +8
  - creatine +6
- NEG:
  - sugar dominant -6 (still relevant but less harsh)

PREFERENCES / AVOID LIST (MODERATE IMPACT)
A1. avoid_artificial_colors
- If colors present: NEG -8

A2. avoid_artificial_sweeteners
- If non-nutritive sweeteners present: NEG -8 (stevia/monk fruit: -4)

A3. caffeine_sensitive
- If stimulant markers present: NEG -10
- If none: POS +2

A4. avoid_ultra_processed
- If natural flavors OR 3+ additives stack: NEG -8
- If clean list (<10, no flavors, minimal additives): POS +4

HEALTH CONSIDERATIONS (OPTIONAL; INGREDIENT LIST ONLY)
C1. blood_sugar_aware
- If sugar dominant: NEG -12
- If multiple sugars: NEG -8
- If no sweeteners: POS +3
(Notes: “Nutrition facts would improve accuracy.”)

DETERMINISTIC EVALUATION STEPS
1) Normalize ingredients_text (lowercase, strip punctuation) and split into items.
2) Parse user_profile fields; if missing, default to empty arrays and goal="general".
3) Detect signals:
   - allergen matches (including common derivatives)
   - animal-derived indicators (for vegan/vegetarian)
   - halal/kosher clear conflicts (only if explicit)
   - sugar terms + positions
   - non-nutritive sweeteners
   - artificial colors
   - stimulant markers
   - whole-food cues (nuts, seeds, whole grains, omega-3 sources)
   - protein cues; creatine presence
   - additive stack markers (flavors, gums/emulsifiers, preservatives, isolates)
4) Apply HARD RULES first (H1–H3) to compute HARD_FAIL_PENALTY and a warning flag.
5) Apply goal weights (G1–G5) to compute POS_POINTS and NEG_POINTS.
6) Apply avoid_list and health_considerations adjustments (A1–A4, C1).
7) Compute final score and bar ratios.
8) Build reasons:
   - Always include any hard-fail reason first (allergen/vegan conflict/etc.)
   - Then top 2 NEG drivers and top 2 POS drivers
9) Categorize every ingredient into the 4 groups relative to THIS user:
   - negative_for_lens if it conflicts with their rules/allergens/preferences/goals
   - positive_for_lens if it supports their selected goal or “clean” preference
   - mixed_for_lens if ambiguous source/umbrella term or context-dependent
   - neutral_for_lens otherwise
10) Identify “Lab Labels” deterministically:
   - Include ingredients likely unfamiliar to the general public, especially:
     a) preservatives, emulsifiers, stabilizers, thickeners, anti-caking agents, humectants, acidity regulators, firming agents
     b) artificial colors, non-nutritive sweeteners, “natural flavors” / “artificial flavors”
     c) refined isolates/reconstituted ingredients (e.g., maltodextrin, modified starch, protein isolate)
     d) chemical-sounding names (suffix cues: -ate, -ite, -ide, -ose, -ol, -ium, -phosphate, -carbonate, -chloride)
   - Exclude obvious everyday foods unless ambiguous.
   - For each lab label, provide:
     - ingredient (exact as listed)
     - plain_english (what it is, 1 sentence)
     - why_added (function in foods, 1 sentence)
     - personal_relevance (1 short sentence tied to this user_profile; cautious language)
11) Provide sources_consulted with EXACTLY these four sources and how used.

OUTPUT FORMAT (STRICT JSON ONLY)
Return one JSON object (NOTE: JSON portion must use DOUBLE CURLY BRACES):

{{
  "lens": "personal Fit Score",
  "score": <int 0-100>,
  "bar": {{
    "fits_you_points": <number>,
    "conflicts_points": <number>,
    "fits_you_ratio": <number 0-1>,
    "conflicts_ratio": <number 0-1>
  }},
  "reasons": {{
    "positives": [ "<✅ ...>", "<✅ ...>", "<✅ ...>" ],
    "concerns": [ "<⚠️ ...>", "<⚠️ ...>", "<⚠️ ...>" ]
  }},
  "criteria_hits": [
    {{ "id": "H1", "name": "Allergen present", "direction": "negative", "points": 70, "evidence": "contains milk (dairy allergen)" }}
  ],
  "ingredients_breakdown": {{
    "positive_for_lens": [ "<ingredient>", ... ],
    "negative_for_lens": [ "<ingredient>", ... ],
    "mixed_for_lens": [ "<ingredient>", ... ],
    "neutral_for_lens": [ "<ingredient>", ... ]
  }},
  "lab_labels": [
    {{
      "ingredient": "<string>",
      "plain_english": "<string>",
      "why_added": "<string>",
      "personal_relevance": "<string>"
    }}
  ],
  "detected_signals": {{
    "first_ingredient": "<string>",
    "ingredient_count": <int>,
    "goal": "<string>",
    "dietary_rules": [..],
    "avoid_list": [..],
    "allergens": [..],
    "health_considerations": [..],
    "sugars": {{ "terms": [..], "positions": [..] }},
    "sweeteners": [..],
    "colors": [..],
    "stimulants": [..],
    "omega3_sources": [..],
    "nuts_seeds": [..],
    "whole_grains": [..],
    "protein_cues": [..],
    "creatine": <true/false>,
    "additive_stack_markers": [..],
    "hard_fail_penalty": <number>
  }},
  "sources_consulted": [
    {{ "source": "Harvard Health Publishing (Harvard Medical School)", "how_used": "Broad nutrition/brain-health framing; supports conservative wording." }},
    {{ "source": "Mayo Clinic", "how_used": "General nutrition/wellness framing; consumer-friendly explanations." }},
    {{ "source": "WebMD", "how_used": "Plain-language reference; avoid strong causal claims." }},
    {{ "source": "Cleveland Clinic", "how_used": "Broad clinical health framing; cautious explanations for sugars/stimulants/additives." }}
  ],
  "notes": [ "<uncertainty/caveats>" ]
}}

USER INPUTS
ingredients_text: "<string>"
user_profile: <object>

Now evaluate the provided ingredients_text and user_profile according to this Personal Fit lens and return STRICT JSON ONLY (using the DOUBLE CURLY BRACES structure above).
        
"""
    analysis_response = await bb_client.add_message(
        thread_id=thread_id,
        content=f"Here are the ingredients I found: {extracted_text}. {instruction}",
        stream=False # Wait for the full answer
    )

    # --- STEP 4: CLEAN THE JSON STRING---
    raw_content = analysis_response.content
    
    # Remove markdown code blocks if they exist
    clean_json = raw_content.replace("```json", "").replace("```", "").strip()

    print(f"cleaned json: {clean_json}") # Debug print to see what is happening

    # --- STEP 5: GENERATE SUMMARY TEXT ---
    print("✍️ Writing summary...")
    summary_prompt = f"""
    Read this analysis and write a 1-sentence, friendly summary for a user. 
    Focus on the score and the biggest pro or con. Keep it conversational.
    Analysis: {clean_json}
    """
    summary_response = vision_model.generate_content(summary_prompt)
    narrative_text = summary_response.text.strip()

    # --- STEP 6: ELEVENLABS AUDIO GENERATION ---
    print("🎙️ Generating high-quality audio...")

    try:
        # Generate audio (returns a generator of bytes)
        audio_generator = elevenlabs.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb", # "Adam" (deep, calm male voice)
            model_id="eleven_turbo_v2_5",    # Low latency model
            text=narrative_text
        )

        # Consume the generator to get full audio bytes
        audio_bytes = b"".join(audio_generator)

        # Encode to Base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        audio_b64 = None

    # --- STEP 5: RETURN TO REACT ---
    return {
        "health_analysis": clean_json, # The full JSON analysis for detailed display
        "narrative_text": narrative_text,
        "audio_base64": audio_b64 # Frontend can play this directly
    }



# @app.post("/api/analyzehardcoded")
# async def analyze_image(file: UploadFile = File(...),
#                         lens: str = Form(...)):
#     print(f"📸 Receiving image for lens: {lens}")
#     # --- STEP 1: READ IMAGE ---
#     print("📸 Receiving image...")
#     contents = await file.read()
#     image = Image.open(io.BytesIO(contents))

#     # --- STEP 2: GEMINI (EXTRACT TEXT) ---
#     print("👀 Gemini is reading the label...")
#     # ocr_response = vision_model.generate_content([
#     #     "Extract list of ingredients from the picture. Don't add anything else just the list of ingredients in english. Make it fast", 
#     #     image
#     # ])
#     # extracted_text = ocr_response.text
#     # print(f"📝 Extracted Text: {extracted_text[:50]}...") # Print first 50 chars

#     if lens =="focus":
#       clean_json = """
#   {
#     "lens": "Focus Score",
#     "score": 20,
#     "bar": {
#       "positive_points": 20,
#       "negative_points": 80,
#       "positive_ratio": 0.2,
#       "negative_ratio": 0.8
#     },
#     "reasons": {
#       "positives": [],
#       "concerns": [
#         "⚠️ Presence of added sugars: sugar, glucose-fructose.",
#         "⚠️ Contains artificial flavor, a marker of processing.",
#         "⚠️ Complexity of ingredient list with 13 ingredients."
#       ]
#     },
#     "criteria_hits": [
#       {
#         "id": "P3",
#         "name": "Added sugar indicators",
#         "direction": "negative",
#         "points": 12,
#         "evidence": "sugar, glucose-fructose"
#       },
#       {
#         "id": "P4",
#         "name": "Flavors marker",
#         "direction": "negative",
#         "points": 8,
#         "evidence": "artificial flavour"
#       },
#       {
#         "id": "P8",
#         "name": "Ingredient list complexity",
#         "direction": "negative",
#         "points": 10,
#         "evidence": "13 ingredients"
#       }
#     ],
#     "ingredients_breakdown": {
#       "positive_for_lens": [],
#       "negative_for_lens": [
#         "sugars (sugar, glucose-fructose)",
#         "artificial flavour",
#         "caramel"
#       ],
#       "mixed_for_lens": [
#         "niacinamide",
#         "pyridoxine hydrochloride (vitamin B6)",
#         "calcium d-pantothenate",
#         "cyanocobalamin (vitamin b12)",
#         "taurine",
#         "riboflavin"
#       ],
#       "neutral_for_lens": [
#         "carbonated water",
#         "citric acid",
#         "sodium bicarbonate",
#         "magnesium carbonate",
#         "caffeine"
#       ]
#     },
#     "lab_labels": [
#       {
#         "ingredient": "taurine",
#         "plain_english": "An organic compound often added to energy drinks.",
#         "why_added": "Used to potentially enhance physical and mental performance.",
#         "common_in": ["energy drinks"]
#       },
#       {
#         "ingredient": "niacinamide",
#         "plain_english": "A form of vitamin B3.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "pyridoxine hydrochloride (vitamin B6)",
#         "plain_english": "A form of vitamin B6.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "calcium d-pantothenate",
#         "plain_english": "A form of vitamin B5.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "cyanocobalamin (vitamin B12)",
#         "plain_english": "A synthetic form of vitamin B12.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "riboflavin",
#         "plain_english": "Also known as vitamin B2.",
#         "why_added": "Used for nutritional fortification.",
#         "common_in": ["fortified cereals", "supplements"]
#       }
#     ],
#     "detected_signals": {
#       "first_ingredient": "carbonated water",
#       "ingredient_count": 13,
#       "sugars": {
#         "terms": ["sugar", "glucose-fructose"],
#         "positions": [1]
#       },
#       "sweeteners": [],
#       "colors": [],
#       "flavors": ["artificial flavour"],
#       "emulsifiers": [],
#       "preservatives": [],
#       "isolates": []
#     },
#     "sources_consulted": [
#       {
#         "source": "NOVA food processing framework",
#         "how_used": "Defines ultra-processed markers (colors, flavors, emulsifiers, sweeteners, reconstituted ingredients)."
#       },
#       {
#         "source": "Health Canada – Lists of Permitted Food Additives",
#         "how_used": "Frames additives as regulated/permitted while still being processing markers."
#       },
#       {
#         "source": "FDA – Food additives/GRAS overview",
#         "how_used": "Avoids unsafe claims; permitted additives can still indicate processing."
#       },
#       {
#         "source": "EFSA – Food additives topic pages",
#         "how_used": "Reference for additive assessment framing; supports cautious language."
#       }
#     ],
#     "notes": []
#   }
#   """
#     elif lens == "real_food":
#         clean_json = """
#   {
#     "lens": "Real Food Score",
#     "score": 30,
#     "bar": {
#       "positive_points": 30,
#       "negative_points": 70,
#       "positive_ratio": 0.3,
#       "negative_ratio": 0.7
#     },
#     "reasons": {
#       "positives": [],
#       "concerns": [
#         "⚠️ Presence of added sugars: sugar, glucose-fructose.",
#         "⚠️ Contains artificial flavor, a marker of processing.",
#         "⚠️ Complexity of ingredient list with 13 ingredients."
#       ]
#     },
#     "criteria_hits": [
#       {
#         "id": "P3",
#         "name": "Added sugar indicators",
#         "direction": "negative",
#         "points": 12,
#         "evidence": "sugar, glucose-fructose"
#       },
#       {
#         "id": "P4",
#         "name": "Flavors marker",
#         "direction": "negative",
#         "points": 8,
#         "evidence": "artificial flavour"
#       },
#       {
#         "id": "P8",
#         "name": "Ingredient list complexity",
#         "direction": "negative",
#         "points": 10,
#         "evidence": "13 ingredients"
#       }
#     ],
#     "ingredients_breakdown": {
#       "positive_for_lens": [],
#       "negative_for_lens": [
#         "sugars (sugar, glucose-fructose)",
#         "artificial flavour",
#         "caramel"
#       ],
#       "mixed_for_lens": [
#         "niacinamide",
#         "pyridoxine hydrochloride (vitamin B6)",
#         "calcium d-pantothenate",
#         "cyanocobalamin (vitamin b12)",
#         "taurine",
#         "riboflavin"
#       ],
#       "neutral_for_lens": [
#         "carbonated water",
#         "citric acid",
#         "sodium bicarbonate",
#         "magnesium carbonate",
#         "caffeine"
#       ]
#     },
#     "lab_labels": [
#       {
#         "ingredient": "taurine",
#         "plain_english": "An organic compound often added to energy drinks.",
#         "why_added": "Used to potentially enhance physical and mental performance.",
#         "common_in": ["energy drinks"]
#       },
#       {
#         "ingredient": "niacinamide",
#         "plain_english": "A form of vitamin B3.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "pyridoxine hydrochloride (vitamin B6)",
#         "plain_english": "A form of vitamin B6.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "calcium d-pantothenate",
#         "plain_english": "A form of vitamin B5.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "cyanocobalamin (vitamin B12)",
#         "plain_english": "A synthetic form of vitamin B12.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "riboflavin",
#         "plain_english": "Also known as vitamin B2.",
#         "why_added": "Used for nutritional fortification.",
#         "common_in": ["fortified cereals", "supplements"]
#       }
#     ],
#     "detected_signals": {
#       "first_ingredient": "carbonated water",
#       "ingredient_count": 13,
#       "sugars": {
#         "terms": ["sugar", "glucose-fructose"],
#         "positions": [1]
#       },
#       "sweeteners": [],
#       "colors": [],
#       "flavors": ["artificial flavour"],
#       "emulsifiers": [],
#       "preservatives": [],
#       "isolates": []
#     },
#     "sources_consulted": [
#       {
#         "source": "NOVA food processing framework",
#         "how_used": "Defines ultra-processed markers (colors, flavors, emulsifiers, sweeteners, reconstituted ingredients)."
#       },
#       {
#         "source": "Health Canada – Lists of Permitted Food Additives",
#         "how_used": "Frames additives as regulated/permitted while still being processing markers."
#       },
#       {
#         "source": "FDA – Food additives/GRAS overview",
#         "how_used": "Avoids unsafe claims; permitted additives can still indicate processing."
#       },
#       {
#         "source": "EFSA – Food additives topic pages",
#         "how_used": "Reference for additive assessment framing; supports cautious language."
#       }
#     ],
#     "notes": []
#   }
#   """
#     elif lens == "personal":
#         clean_json = """
#   {
#     "lens": "Personal Score",
#     "score": 40,
#     "bar": {
#       "positive_points": 40,
#       "negative_points": 60,
#       "positive_ratio": 0.4,
#       "negative_ratio": 0.6
#     },
#     "reasons": {
#       "positives": [],
#       "concerns": [
#         "⚠️ Presence of added sugars: sugar, glucose-fructose.",
#         "⚠️ Contains artificial flavor, a marker of processing.",
#         "⚠️ Complexity of ingredient list with 13 ingredients."
#       ]
#     },
#     "criteria_hits": [
#       {
#         "id": "P3",
#         "name": "Added sugar indicators",
#         "direction": "negative",
#         "points": 12,
#         "evidence": "sugar, glucose-fructose"
#       },
#       {
#         "id": "P4",
#         "name": "Flavors marker",
#         "direction": "negative",
#         "points": 8,
#         "evidence": "artificial flavour"
#       },
#       {
#         "id": "P8",
#         "name": "Ingredient list complexity",
#         "direction": "negative",
#         "points": 10,
#         "evidence": "13 ingredients"
#       }
#     ],
#     "ingredients_breakdown": {
#       "positive_for_lens": [],
#       "negative_for_lens": [
#         "sugars (sugar, glucose-fructose)",
#         "artificial flavour",
#         "caramel"
#       ],
#       "mixed_for_lens": [
#         "niacinamide",
#         "pyridoxine hydrochloride (vitamin B6)",
#         "calcium d-pantothenate",
#         "cyanocobalamin (vitamin b12)",
#         "taurine",
#         "riboflavin"
#       ],
#       "neutral_for_lens": [
#         "carbonated water",
#         "citric acid",
#         "sodium bicarbonate",
#         "magnesium carbonate",
#         "caffeine"
#       ]
#     },
#     "lab_labels": [
#       {
#         "ingredient": "taurine",
#         "plain_english": "An organic compound often added to energy drinks.",
#         "why_added": "Used to potentially enhance physical and mental performance.",
#         "common_in": ["energy drinks"]
#       },
#       {
#         "ingredient": "niacinamide",
#         "plain_english": "A form of vitamin B3.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "pyridoxine hydrochloride (vitamin B6)",
#         "plain_english": "A form of vitamin B6.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "calcium d-pantothenate",
#         "plain_english": "A form of vitamin B5.",
#         "why_added": "Used as a dietary supplement for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "cyanocobalamin (vitamin B12)",
#         "plain_english": "A synthetic form of vitamin B12.",
#         "why_added": "Used as a dietary supplement or fortification for added nutrition.",
#         "common_in": ["supplements", "fortified foods"]
#       },
#       {
#         "ingredient": "riboflavin",
#         "plain_english": "Also known as vitamin B2.",
#         "why_added": "Used for nutritional fortification.",
#         "common_in": ["fortified cereals", "supplements"]
#       }
#     ],
#     "detected_signals": {
#       "first_ingredient": "carbonated water",
#       "ingredient_count": 13,
#       "sugars": {
#         "terms": ["sugar", "glucose-fructose"],
#         "positions": [1]
#       },
#       "sweeteners": [],
#       "colors": [],
#       "flavors": ["artificial flavour"],
#       "emulsifiers": [],
#       "preservatives": [],
#       "isolates": []
#     },
#     "sources_consulted": [
#       {
#         "source": "NOVA food processing framework",
#         "how_used": "Defines ultra-processed markers (colors, flavors, emulsifiers, sweeteners, reconstituted ingredients)."
#       },
#       {
#         "source": "Health Canada – Lists of Permitted Food Additives",
#         "how_used": "Frames additives as regulated/permitted while still being processing markers."
#       },
#       {
#         "source": "FDA – Food additives/GRAS overview",
#         "how_used": "Avoids unsafe claims; permitted additives can still indicate processing."
#       },
#       {
#         "source": "EFSA – Food additives topic pages",
#         "how_used": "Reference for additive assessment framing; supports cautious language."
#       }
#     ],
#     "notes": []
#   }
#   """
#     return {
#         "health_analysis": clean_json
#     }