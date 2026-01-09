import streamlit as st
import pandas as pd

st.set_page_config(page_title="Skin Recommendation Engine", layout="centered")

# Load products from CSV
@st.cache_data
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

def is_safe(row, is_sensitive, is_pregnant, using_prescription):
    if is_pregnant and (row.get('contains_retinol', '') == 'Yes' or row.get('prescripition_only', '') == 'Yes'):
        return False
    if is_sensitive and row.get('safe_for_sensitive', '') != 'Yes':
        return False
    if using_prescription and (row.get('contains_retinol', '') == 'Yes' or row.get('contains_acid', '') == 'Yes'):
        return False
    return True

def build_routine(df, skin_type, concerns, is_sensitive, is_pregnant, using_prescription, area):
    # Area filter - less strict for face pigmentation/moisturizers
    if area == "Face":
        filtered = df[~df['name'].str.lower().str.contains('body wash|scrub|shower gel|body oil gel', na=False)]
    elif area == "Body":
        filtered = df[df['name'].str.lower().str.contains('body', na=False)]
    else:
        filtered = df.copy()

    # Safety filter
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Skin type filter - include related (e.g., Dry for dehydrated)
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains('All', case=False, na=True) |
        filtered['suitable_skin_types'].str.contains(skin_type, case=False, na=True) |
        (filtered['suitable_skin_types'].str.contains('Dry', case=False, na=True) if skin_type == "Dry" else False)
    ]

    # If no concerns, default to skin type goal (e.g., hydration for Dry)
    if not concerns:
        if skin_type == "Dry":
            concerns = ["dryness"]
        elif skin_type == "Oily":
            concerns = ["acne"]
        else:
            concerns = ["dull"]

    # Concerns filter
    if concerns:
        filtered = filtered.reset_index(drop=True)
        mask = pd.Series([False] * len(filtered))
        for c in concerns:
            keywords = "|".join(CONCERN_MAPPING.get(c, []))
            if keywords:
                mask |= filtered['primary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['secondary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['key_actives'].str.contains(keywords, case=False, na=False)
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("No perfect matches. Here's general guidance — consult a professional for more.")
        st.write("**1. Cleanse** → Gentle, non-foaming cleanser.")
        st.write("**2. Tone** → Hydrating toner.")
        st.write("**3. Treat** → Targeted serum for your concerns.")
        st.write("**4. Moisturize** → Lightweight or rich cream based on skin type.")
        st.write("**5. Protect** → SPF 50+ daily.")
        return

    st.success("Here's your personalized routine:")

    recommended_products = []

    # 1. Cleanse
    cleansers = filtered[filtered['step'] == '1. Cleanse']
    if not cleansers.empty:
        chosen = cleansers.sample(1).iloc[0]
        st.write(f"**1. Cleanse** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**1. Cleanse** → Gentle cream cleanser.")

    # 2. Tone
    toners = filtered[filtered['step'] == '2. Tone/Exfoliate']
    if not toners.empty:
        gentle = toners[toners['contains_acid'] != 'Yes']
        chosen = (gentle if not gentle.empty else toners).sample(1).iloc[0]
        st.write(f"**2. Tone** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**2. Tone** → Hydrating, alcohol-free toner.")

    # 3. Treat
    treats = filtered[filtered['step'] == '3. Treat']
    if not treats.empty:
        chosen = treats.sample(1).iloc[0]
        st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**3. Treat** → Targeted serum for your concerns.")

    # 4. Moisturize
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        chosen = moist.sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**4. Moisturize** → Rich cream for hydration.")

    # 5. Protect
    st.write("**5. Protect** → Broad-spectrum SPF 50+ every morning.")

    st.info("Start slow • Patch test • Be consistent")

    # Recommended Products Grid
    st.markdown("---")
    st.subheader("🛒 Products from Your Routine")

    seen = set()
    unique_products = []
    for p in recommended_products:
        if p['product_id'] not in seen:
            seen.add(p['product_id'])
            unique_products.append(p)

    if unique_products:
        cols = st.columns(min(3, len(unique_products)))
        for idx, p in enumerate(unique_products):
            with cols[idx % 3]:
                st.markdown(f"**{p['product_id']}**")
                st.write(p['name'])
                st.caption(f"{p['primary_target']} • {p['key_actives']}")
    else:
        st.info("General guidance for now — specific products unlocked in your next session!")

    # Next Goals - Teaser
    st.markdown("---")
    st.subheader("🌟 Next Skin Goals (Unlock in Your Follow-Up Session)")
    st.write("• Smoother texture")
    st.write("• Even glow")
    st.write("• Stronger barrier")
    st.write("• Youthful vibe")
    st.success("Return soon to level up — your best skin awaits! 🔜")

# UI
st.title("👋 Welcome to Skin Recommendation Engine")
st.write("Hi! Let's build your routine.")

with st.form("skin_form"):
    st.subheader("Your Skin Type?")
    skin_option = st.selectbox("Select:", ["Oily", "Dry", "Combination", "Normal", "Not sure"])

    if skin_option == "Not sure":
        st.info("Guide:")
        for k, v in SKIN_TYPE_EXPLANATIONS.items():
            st.write(f"• **{k}**: {v}")
        skin_option = st.selectbox("Best match?", ["Oily", "Dry", "Combination", "Normal"])

    st.subheader("Current Concerns?")
    concern_options = [
        "Acne / breakouts",
        "Dark spots / hyperpigmentation / melasma",
        "Dryness / dehydration",
        "Dull skin",
        "Uneven texture / rough skin",
        "Aging / fine lines",
        "Sensitivity / irritation",
        "Damaged barrier",
        "None"
    ]
    selected_concerns = st.multiselect("Select all that apply:", concern_options)

    st.subheader("Any apply?")
    sensitive = st.checkbox("Skin reacts easily")
    pregnant = st.checkbox("Pregnant / breastfeeding")
    prescription = st.checkbox("Using prescription skincare")

    area = st.radio("Shopping for:", ("Face", "Body", "Both"))

    submitted = st.form_submit_button("Get Routine")

if submitted:
    concerns = [c.lower() for c in selected_concerns if c != "None"]

    if pregnant or prescription:
        st.warning("Safety first! Consult doctor.")
    elif sensitive and len(concerns) > 2:
        st.warning("Complex — seek professional advice.")
    else:
        build_routine(df, skin_option, concerns, sensitive, pregnant, prescription, area)

# Shopping
st.markdown("---")
st.subheader("🛒 Browse")
query = st.text_input("Keyword (e.g., cleanser)")
if query:
    matches = df[df['name'].str.lower().str.contains(query.lower(), na=False)]
    if matches.empty:
        st.info("No matches.")
    else:
        for _, p in matches.iterrows():
            with st.expander(f"**{p['product_id']} — {p['name']}**"):
                st.write(f"Best for: {p['primary_target']} • {p['secondary_target']}")
                st.write(f"Key: {p['key_actives']}")
                st.write(f"Use: {p['recommended_time']} — {p['max_frequency']}")

st.caption("Trust your skin journey 🌿")
