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
    "acne": ["acne", "pimple", "breakout", "blemish", "pore"],
    "dark spots / uneven tone": ["dark spot", "hyperpigmentation", "melasma", "uneven tone", "pigment"],
    "dryness": ["dryness", "dehydrated", "tight"],
    "texture / rough skin": ["texture", "rough", "bumpy"],
    "aging": ["aging", "wrinkle", "fine line", "firm"],
    "sensitivity": ["sensitive", "irritated", "react", "sting"],
    "dull": ["dull", "lack glow"],
    "barrier damage": ["barrier", "damaged", "weak"]
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
    # Area filter (less strict for face pigmentation products)
    if area == "Face":
        filtered = df[~df['name'].str.lower().str.contains('body wash|scrub|shower gel|body oil gel', na=False)]
    elif area == "Body":
        filtered = df[df['name'].str.lower().str.contains('body', na=False)]
    else:
        filtered = df.copy()

    # Safety filter
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Skin type filter
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains('All', case=False, na=True) |
        filtered['suitable_skin_types'].str.contains(skin_type, case=False, na=True)
    ]

    # Relax for sensitive
    if filtered.empty and is_sensitive:
        st.info("Being extra gentle with your sensitive skin — showing safe universal options.")
        filtered = df[
            (df['safe_for_sensitive'] == 'Yes') &
            (df['suitable_skin_types'].str.contains('All', case=False, na=True))
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
        st.write("**1. Cleanse** → Gentle cream or gel cleanser (no foaming agents).")

    # 2. Tone
    toners = filtered[filtered['step'] == '2. Tone/Exfoliate']
    if not toners.empty:
        gentle = toners[toners['contains_acid'] != 'Yes']
        chosen = (gentle if not gentle.empty else toners).sample(1).iloc[0]
        st.write(f"**2. Tone** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**2. Tone** → Hydrating, alcohol-free toner (ceramides or centella).")

    # 3. Treat
    treats = filtered[filtered['step'] == '3. Treat']
    if not treats.empty:
        if "dark spots / uneven tone" in concerns:
            bright = treats[treats['key_actives'].str.contains('arbutin|tranexamic|niacinamide|kojic|vitamin c', case=False, na=False)]
            chosen = bright.sample(1).iloc[0] if not bright.empty else treats.sample(1).iloc[0]
            st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']} (targets pigmentation)")
        elif "acne" in concerns:
            acne_treat = treats[treats['key_actives'].str.contains('niacinamide|salicylic', case=False, na=False)]
            chosen = acne_treat.sample(1).iloc[0] if not acne_treat.empty else treats.sample(1).iloc[0]
            st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']} (controls acne)")
        else:
            chosen = treats.sample(1).iloc[0]
            st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        if "dark spots / uneven tone" in concerns:
            st.write("**3. Treat** → Niacinamide or tranexamic acid serum for pigmentation.")
        else:
            st.write("**3. Treat** → Consider a hydrating serum.")

    # 4. Moisturize
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        if skin_type == "Oily":
            light = moist[moist['product_type'].str.contains('gel|emulsion|light', case=False, na=False)]
            chosen = light.sample(1).iloc[0] if not light.empty else moist.sample(1).iloc[0]
        else:
            chosen = moist.sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        if skin_type == "Dry":
            st.write("**4. Moisturize** → Rich cream with ceramides or hyaluronic acid.")
        else:
            st.write("**4. Moisturize** → Lightweight gel or lotion moisturizer.")

    # 5. Protect
    st.write("**5. Protect** → Broad-spectrum SPF 50+ every morning (mineral-based is gentler for sensitive skin).")

    st.info("💡 Start one new product at a time • Patch test • Use sunscreen daily • Be patient — results take 4–12 weeks")

    # === Recommended Products Grid ===
    st.markdown("---")
    st.subheader("🛒 Recommended Products from Your Routine")

    # Remove duplicates
    seen = set()
    unique_products = []
    for p in recommended_products:
        pid = p['product_id']
        if pid not in seen:
            seen.add(pid)
            unique_products.append(p)

    if unique_products:
        st.write("Here are the specific products that match your routine:")
        cols = st.columns(min(3, len(unique_products)))
        for idx, p in enumerate(unique_products):
            with cols[idx % 3]:
                st.markdown(f"**{p['product_id']}**")
                st.write(p['name'])
                st.caption(f"{p['primary_target']} • {p['key_actives']}")
    else:
        st.info("No exact product matches right now, but the advice above will guide you to the right type.")

    # Next Goals
    st.markdown("---")
    st.subheader("🌟 Your Next Goals (Once Current Issues Improve)")
    if "acne" in concerns:
        st.write("• Fade post-acne marks with Vitamin C or tranexamic acid")
    if "dark spots / uneven tone" in concerns:
        st.write("• Boost glow with consistent Vitamin C in the morning")
        st.write("• Try gentle exfoliation (lactic acid) 2x/week")
    if "dryness" in concerns or skin_type == "Dry":
        st.write("• Layer hyaluronic acid serum for deep hydration")
    st.write("• Long-term: Introduce anti-aging (retinol) very slowly at night")
    st.write("• Always: SPF to prevent new pigmentation and aging")
    st.success("Re-run this quiz in 6–8 weeks — we'll upgrade your routine as your skin improves! 🌱")

# === Streamlit UI ===
st.title("👋 Welcome to Skin Recommendation Engine")
st.write("Hi! I'm here to help you build a safe, effective routine.")

with st.form("skin_form"):
    st.subheader("How would you describe your skin?")
    skin_option = st.selectbox(
        "Select one:",
        ["Oily", "Dry", "Combination", "Normal", "Not sure"],
        key="skin_select"
    )

    if skin_option == "Not sure":
        st.info("Quick guide:")
        for k, v in SKIN_TYPE_EXPLANATIONS.items():
            st.write(f"• **{k}**: {v}")
        skin_option = st.selectbox(
            "Which sounds most like you?",
            ["Oily", "Dry", "Combination", "Normal"],
            key="skin_sure"
        )

    st.subheader("What are your current skin concerns?")
    st.write("Choose all that apply (or none if just maintaining)")
    concern_options = [
        "Acne / breakouts",
        "Dark spots / hyperpigmentation / melasma",
        "Dryness / dehydration",
        "Dull skin",
        "Uneven texture / rough skin",
        "Aging / fine lines",
        "Sensitivity / irritation",
        "Damaged barrier",
        "None — just maintaining healthy skin"
    ]
    selected_concerns = st.multiselect("Select your concerns:", concern_options, key="concerns_multi")

    st.subheader("Any of these apply to you?")
    sensitive = st.checkbox("My skin reacts easily / is sensitive")
    pregnant = st.checkbox("I’m pregnant or breastfeeding")
    prescription = st.checkbox("I’m currently using prescription skincare")

    area = st.radio("Shopping for:", ("Face", "Body", "Both"), key="area_radio")

    submitted = st.form_submit_button("Get My Personalized Routine", type="primary")

if submitted:
    # Map multiselect to internal concerns
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
    concerns = [concerns_map.get(c, "") for c in selected_concerns if c in concerns_map]

    if pregnant or prescription:
        st.warning("Safety first! Please consult your doctor or dermatologist before starting new products.")
    elif sensitive and len(concerns) > 2:
        st.warning("Multiple concerns + sensitivity need professional guidance. Please speak to the seller or a dermatologist.")
    else:
        build_routine(df, skin_option, concerns, sensitive, pregnant, prescription, area)

# Shopping
st.markdown("---")
st.subheader("🛒 Browse Products")
query = st.text_input("Search by keyword (e.g., niacinamide, vitamin c, cleanser, retinol)")
if query:
    matches = df[df['name'].str.lower().str.contains(query.lower(), na=False)]
    if matches.empty:
        st.info("No matches. Try 'toner', 'serum', 'moisturizer', etc.")
    else:
        for _, p in matches.iterrows():
            with st.expander(f"**{p['product_id']} — {p['name']}**"):
                st.write(f"**Best for**: {p['primary_target']} • {p['secondary_target']}")
                st.write(f"**Key ingredients**: {p['key_actives']}")
                st.write(f"**Use**: {p['recommended_time']} — {p['max_frequency']}")
                if p['safe_for_sensitive'] == 'Yes':
                    st.write("✅ Safe for sensitive skin")
                if p['contains_retinol'] == 'Yes' or p['contains_acid'] == 'Yes':
                    st.write("⚠️ Strong active — patch test + sunscreen required")

st.caption("Thank you for trusting us with your skin 🌿 • Patch test • Start slow • Be consistent")
