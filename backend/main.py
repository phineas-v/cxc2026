from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from backboard import BackboardClient # Use the SDK!
from PIL import Image
import io
import asyncio # For startup logic

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyB0UEAXKvqRdp3wzoFV40cMO6PJP27RAyM"
BACKBOARD_API_KEY = "espr_ZF0hWS5sETRl_kmaNsvywxVJuXKu9IFvtC--W28S2Lk"

# 1. Setup Gemini ("The Eyes")
genai.configure(api_key=GOOGLE_API_KEY)
vision_model = genai.GenerativeModel('gemini-flash-latest')

# 2. Setup Backboard ("The Brain")
bb_client = BackboardClient(api_key=BACKBOARD_API_KEY)

# Global variables to store our AI Agent IDs
assistant_id = None
thread_id = None

app = FastAPI()
#a comment for testing

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
    
    # Create the Health Expert
    assistant = await bb_client.create_assistant(
        name="Health Analyzer",
        system_prompt="""
        You are a strict nutritionist. Analyze the ingredients provided.
        Return a JSON Object with a key 'ingredients' containing a list.
        
        Each item in the list must have:
        - "name": String (Name of ingredient)
        - "score": Integer (0-100, where 100 is healthiest)
        - "status": String (One of: "SAFE", "CAUTION", "DANGER")
        - "explanation": String (Short reason why)

        Example format:
        {{
          "ingredients": [
            {{
              "name": "Apples", 
              "score": 100, 
              "status": "SAFE", 
              "explanation": "Rich in fiber."
            }},
            {{
              "name": "Red Dye 40", 
              "score": 10, 
              "status": "DANGER", 
              "explanation": "Potential carcinogen."
            }}
          ]
        }}
        
        DO NOT return Markdown. Return ONLY raw JSON.
        """
    )
    assistant_id = assistant.assistant_id
    
    # Create a conversation thread
    thread = await bb_client.create_thread(assistant_id)
    thread_id = thread.thread_id
    print("✅ Agent Ready!")

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # --- STEP 1: READ IMAGE ---
    print("📸 Receiving image...")
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # --- STEP 2: GEMINI (EXTRACT TEXT) ---
    print("👀 Gemini is reading the label...")
    ocr_response = vision_model.generate_content([
        "Extract ONLY the list of ingredients and nutrition facts. Do not add conversational text.", 
        image
    ])
    extracted_text = ocr_response.text
    print(f"📝 Extracted Text: {extracted_text[:50]}...") # Print first 50 chars

    # --- STEP 3: BACKBOARD (ANALYZE HEALTH) ---
    print("ZO🧠 Backboard is analyzing health...")
    
    # We send the text from Gemini into Backboard
    analysis_response = await bb_client.add_message(
        thread_id=thread_id,
        content=f"Here are the ingredients I found: {extracted_text}. Return ONLY valid JSON.",
        stream=False # Wait for the full answer
    )

    # --- STEP 4: CLEAN THE JSON STRING---
    raw_content = analysis_response.content
    
    # Remove markdown code blocks if they exist
    clean_json = raw_content.replace("```json", "").replace("```", "").strip()

    print(f"cleaned json: {clean_json}") # Debug print to see what is happening

    # --- STEP 5: RETURN TO REACT ---
    return {
        "health_analysis": clean_json
    }



