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

def is_safe(row, is_sensitive, is_pregnant, using_prescription):
    if is_pregnant and (row.get('contains_retinol', '') == 'Yes' or row.get('prescripition_only', '') == 'Yes'):
        return False
    if is_sensitive and row.get('safe_for_sensitive', '') != 'Yes':
        return False
    if using_prescription and (row.get('contains_retinol', '') == 'Yes' or row.get('contains_acid', '') == 'Yes'):
        return False
    return True

def build_routine(df, skin_type, concerns, is_sensitive, is_pregnant, using_prescription, area):
    # Area filter - allow more for "Both"
    if area == "Face":
        filtered = df[~df['name'].str.lower().str.contains('body wash|scrub|shower gel', na=False)]
    elif area == "Body":
        filtered = df[df['name'].str.lower().str.contains('body', na=False)]
    else:
        filtered = df.copy()  # Both = all

    # Safety filter
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Skin type filter - include Acne-prone for oily + acne
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains('All', case=False, na=True) |
        filtered['suitable_skin_types'].str.contains(skin_type, case=False, na=True) |
        filtered['suitable_skin_types'].str.contains('Acne-prone', case=False, na=True)
    ]

    if filtered.empty:
        st.warning("No perfect matches found. Please consult a professional for personalized advice.")
        return

    st.success("Here's your safe, personalized routine:")

    recommended_products = []

    # 1. Cleanse
    cleansers = filtered[filtered['step'] == '1. Cleanse']
    if not cleansers.empty:
        chosen = cleansers.sample(1).iloc[0]
        st.write(f"**1. Cleanse** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**1. Cleanse** → Gentle gel cleanser (non-foaming, oil-controlling).")

    # 2. Tone
    toners = filtered[filtered['step'] == '2. Tone/Exfoliate']
    if not toners.empty:
        chosen = toners.sample(1).iloc[0]
        st.write(f"**2. Tone** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**2. Tone** → Mattifying or hydrating toner.")

    # 3. Treat - prioritize acne control
    treats = filtered[filtered['step'] == '3. Treat']
    if not treats.empty:
        acne_priority = treats[treats['key_actives'].str.contains('niacinamide|salicylic', case=False, na=False)]
        chosen = acne_priority.sample(1).iloc[0] if not acne_priority.empty else treats.sample(1).iloc[0]
        st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']} (oil control + acne fighter)")
        recommended_products.append(chosen)
    else:
        st.write("**3. Treat** → Niacinamide serum (mattifies and calms breakouts).")

    # 4. Moisturize - lightweight for oily
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        light = moist[moist['product_type'].str.contains('gel|light|lotion|emulsion', case=False, na=False)]
        chosen = light.sample(1).iloc[0] if not light.empty else moist.sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**4. Moisturize** → Oil-free gel moisturizer.")

    # 5. Protect
    st.write("**5. Protect** → Broad-spectrum SPF 50+ every morning (matte finish for oily skin).")

    st.info("Start slow • Patch test • Consistency is key")

    # Recommended Products Grid
    st.markdown("---")
    st.subheader("🛒 Your Recommended Products")

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
        st.info("General guidance given — specific products coming in your next session!")

    # Next Goals - Teaser style (leaves them thirsty)
    st.markdown("---")
    st.subheader("🌟 Your Next Skin Goals")
    st.write("Once your breakouts calm down...")
    st.write("→ Clearer, smoother texture")
    st.write("→ Reduced oil shine all day")
    st.write("→ Faded acne marks")
    st.write("→ That effortless glow")

    st.success("Come back in 4–6 weeks for your upgraded routine. Your skin's best phase is coming. 🔜")

# === UI (unchanged) ===
st.title("👋 Welcome to Skin Recommendation Engine")
st.write("Hi! I'm here to help you build a safe, effective routine.")

with st.form("skin_form"):
    st.subheader("How would you describe your skin?")
    skin_option = st.selectbox("Select one:", ["Oily", "Dry", "Combination", "Normal", "Not sure"])

    if skin_option == "Not sure":
        st.info("Quick guide:")
        for k, v in SKIN_TYPE_EXPLANATIONS.items():
            st.write(f"• **{k}**: {v}")
        skin_option = st.selectbox("Which sounds most like you?", ["Oily", "Dry", "Combination", "Normal"])

    st.subheader("What are your current skin concerns?")
    st.write("Choose all that apply")
    concern_options = [
        "Acne / breakouts",
        "Dark spots / hyperpigmentation / melasma",
        "Dryness / dehydration",
        "Dull skin",
        "Uneven texture / rough skin",
        "Aging / fine lines",
        "Sensitivity / irritation",
        "Damaged barrier",
        "None — just maintaining"
    ]
    selected_concerns = st.multiselect("Select:", concern_options)

    st.subheader("Any of these apply?")
    sensitive = st.checkbox("My skin reacts easily / is sensitive")
    pregnant = st.checkbox("I’m pregnant or breastfeeding")
    prescription = st.checkbox("I’m currently using prescription skincare")

    area = st.radio("Shopping for:", ("Face", "Body", "Both"))

    submitted = st.form_submit_button("Get My Personalized Routine", type="primary")

if submitted:
    concerns_map = {
        "Acne / breakouts": "acne",
        "Dark spots / hyperpigmentation / melasma": "dark spots / uneven tone",
        "Dryness / dehydration": "dryness",
        "Dull skin": "dull",
        "Uneven texture / rough skin": "texture / rough skin",
        "Aging / fine lines": "aging",
        "Sensitivity / irritation": "sensitivity",
        "Damaged barrier": "barrier damage"
    }
    concerns = [concerns_map.get(c) for c in selected_concerns if concerns_map.get(c)]

    if pregnant or prescription:
        st.warning("Safety first! Consult your doctor before new products.")
    elif sensitive and len(concerns) > 2:
        st.warning("Complex concerns — professional advice recommended.")
    else:
        build_routine(df, skin_option, concerns, sensitive, pregnant, prescription, area)

# Shopping (unchanged)
st.markdown("---")
st.subheader("🛒 Browse Products")
query = st.text_input("Search keyword (cleanser, niacinamide, etc.)")
if query:
    matches = df[df['name'].str.lower().str.contains(query.lower(), na=False)]
    if matches.empty:
        st.info("No matches — try another word!")
    else:
        for _, p in matches.iterrows():
            with st.expander(f"**{p['product_id']} — {p['name']}**"):
                st.write(f"Best for: {p['primary_target']} • {p['secondary_target']}")
                st.write(f"Key actives: {p['key_actives']}")
                st.write(f"Use: {p['recommended_time']} — {p['max_frequency']}")

st.caption("Thank you for trusting us with your skin 🌿")
