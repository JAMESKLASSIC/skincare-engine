import streamlit as st
import pandas as pd

st.set_page_config(page_title="Skin Recommendation Engine", layout="centered")

# Load products from CSV
@st.cache_data  # This makes it load only once
def load_products():
    return pd.read_csv('products.csv')

df = load_products()

# Skin type explanations
SKIN_TYPE_EXPLANATIONS = {
    "Oily": "Skin that gets shiny quickly, especially on the T-zone, and may be prone to breakouts.",
    "Dry": "Skin that feels tight, flaky, or rough and lacks moisture.",
    "Combination": "Oily in some areas (usually forehead, nose, chin) and dry/normal in others (cheeks).",
    "Normal": "Balanced — not too oily or dry, with few issues."
}

# Concern mapping
CONCERN_MAPPING = {
    "acne": ["acne", "blemish", "pore", "salicylic", "benzoyl", "breakout"],
    "dark spots / uneven tone": ["brightening", "even tone", "fade spots", "whitening", "hyperpigmentation", "dark spots", "melasma", "pigment", "arbutin", "kojic", "niacinamide", "vitamin c", "tranexamic"],
    "dryness": ["dry", "hydration", "hyaluronic", "moisturizing"],
    "texture / rough skin": ["texture", "exfoliation", "smoothing", "glycolic", "lactic", "rough"],
    "aging": ["anti-aging", "retinol", "firming", "wrinkle"],
    "sensitivity": ["sensitive", "soothing", "gentle", "calming", "centella", "ceramide", "barrier"],
    "dehydrated": ["dehydrated", "hydration", "hyaluronic"],
    "dull": ["dull", "glow", "radiance", "vitamin c"],
    "barrier damage": ["barrier", "ceramide", "repair", "restore"]
}

def normalize_skin_type(user_input):
    lower = user_input.lower()
    if any(k in lower for k in ["oily", "shiny", "greasy"]):
        return "Oily"
    if any(k in lower for k in ["dry", "tight", "flaky"]):
        return "Dry"
    if any(k in lower for k in ["combination", "mix", "t-zone"]):
        return "Combination"
    return "Normal"

def extract_concerns(user_input):
    lower = user_input.lower()
    found = set()
    for concern, keywords in CONCERN_MAPPING.items():
        if any(k in lower for k in keywords):
            found.add(concern)
    return list(found) if found else []

def is_safe(row, is_sensitive, is_pregnant, using_prescription):
    if is_pregnant and (row.get('contains_retinol', '') == 'Yes' or row.get('prescripition_only', '') == 'Yes'):
        return False
    if is_sensitive and row.get('safe_for_sensitive', '') != 'Yes':
        return False
    if using_prescription and (row.get('contains_retinol', '') == 'Yes' or row.get('contains_acid', '') == 'Yes'):
        return False
    return True

def build_routine(df, skin_type, concerns, is_sensitive, is_pregnant, using_prescription, area):
    # Area filter
    if area == "face":
        filtered = df[~df['name'].str.lower().str.contains('body')]
    elif area == "body":
        filtered = df[df['name'].str.lower().str.contains('body')]
    else:
        filtered = df.copy()

    # Safety filter
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Skin type filter
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains(skin_type, case=False, na=True) |
        filtered['suitable_skin_types'].str.contains('All', case=False, na=True)
    ]

    # Concerns filter
    if concerns:
        mask = pd.Series([False] * len(filtered))
        for c in concerns:
            keywords = "|".join(CONCERN_MAPPING.get(c, []))
            if keywords:
                mask |= filtered['primary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['secondary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['key_actives'].str.contains(keywords, case=False, na=False)
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("No products match your needs perfectly right now. Your skin profile may need a professional consultation.")
        return False

    st.success("Here's your personalized routine:")

    has_acid = False

    # 1. Cleanse
    cleansers = filtered[filtered['step'] == '1. Cleanse']
    if not cleansers.empty:
        chosen = cleansers.sample(1).iloc[0]
        st.write(f"**1. Cleanse** → {chosen['product_id']} — {chosen['name']}")

    # 2. Tone
    toners = filtered[filtered['step'] == '2. Tone/Exfoliate']
    if not toners.empty:
        gentle = toners[toners['contains_acid'] != 'Yes']
        chosen = (gentle if not gentle.empty else toners).sample(1).iloc[0]
        st.write(f"**2. Tone** → {chosen['product_id']} — {chosen['name']}")

    # 3. Treat
    treats = filtered[filtered['step'] == '3. Treat']
    if not treats.empty:
        nia = treats[treats['key_actives'].str.contains('niacinamide', case=False, na=False)]
        chosen = (nia if not nia.empty else treats).sample(1).iloc[0]
        st.write(f"**3. Treat (Serum)** → {chosen['product_id']} — {chosen['name']}")

    # 4. Moisturize
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        light = moist[moist['product_type'].str.contains('gel|emulsion|light', case=False, na=False)]
        chosen = (light if not light.empty else moist).sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")

    # 5. Protect
    st.write("**5. Protect** → Always use broad-spectrum SPF 50+ in the morning (mineral-based for sensitive skin).")

    st.info("Start slowly with new products. Patch test first. If irritation occurs, stop and consult a professional.")
    return True

# === Streamlit UI ===
st.title("👋 Welcome to Skin Recommendation Engine")
st.write("Hi! I'm here to help with your skin. Let's find the perfect routine for you.")

with st.form("skin_form"):
    st.write("### How would you describe your skin?")
    skin_option = st.selectbox("Choose one:", ["Oily", "Dry", "Combination", "Normal", "Not sure"])

    if skin_option == "Not sure":
        st.info("Here’s a quick guide:")
        for k, v in SKIN_TYPE_EXPLANATIONS.items():
            st.write(f"• **{k}**: {v}")
        skin_option = st.selectbox("Now which sounds most like you?", ["Oily", "Dry", "Combination", "Normal"])

    st.write("### What is the main issue you want to fix right now?")
    concern_main = st.text_input("Tell me freely (e.g., acne and dark spots)")

    st.write("### Any of these apply to you?")
    sensitive = st.checkbox("My skin reacts easily / is sensitive")
    pregnant = st.checkbox("I’m pregnant or breastfeeding")
    prescription = st.checkbox("I’m currently using prescription products")

    area = st.radio("Where are you shopping today?", ("Face", "Body", "Both"))

    submitted = st.form_submit_button("Get My Routine")

if submitted:
    skin_type = normalize_skin_type(skin_option)
    concerns = extract_concerns(concern_main)

    if pregnant or prescription or (sensitive and len(concerns) > 2):
        st.warning("Your situation needs extra care. Please consult a dermatologist or the seller before starting new products.")
    else:
        build_routine(df, skin_type, concerns, sensitive, pregnant, prescription, area.lower())

# Shopping mode
st.markdown("---")
if st.button("Browse Products"):
    query = st.text_input("Search by keyword (e.g., cleanser, niacinamide, vitamin c)")
    if query:
        matches = df[df['name'].str.lower().str.contains(query.lower())]
        if matches.empty:
            st.info("No matches found. Try another keyword.")
        else:
            for _, p in matches.iterrows():
                st.write(f"**{p['product_id']}** — {p['name']}")

st.caption("Thank you for trusting us with your skin 🌿")
