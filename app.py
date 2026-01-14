import streamlit as st
import pandas as pd

st.set_page_config(page_title="Skin Recommendation Engine Vovwero", layout="centered")

@st.cache_data
def load_products():
    return pd.read_csv('products.csv')

df = load_products()

# Debug
st.write(f"**Debug: Loaded {len(df)} products**")

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
    # Super relaxed area filter
    if area == "Face":
        filtered = df[~df['name'].str.lower().str.contains('body wash|shower gel', na=False)]  # only exclude heavy body cleansers
    elif area == "Body":
        filtered = df[df['name'].str.lower().str.contains('body', na=False)]
    else:
        filtered = df.copy()

    # Safety only
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Extremely permissive skin type filter — almost everything
    type_pattern = 'All'  # base is everything
    if skin_type == "Oily":
        type_pattern += '|Oily|Acne-prone'  # add acne-prone for oily
    elif skin_type == "Dry":
        type_pattern += '|Dry'
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains(type_pattern, case=False, na=True)
    ]

    # Default to something useful if no concerns
    if not concerns:
        if skin_type == "Oily":
            concerns = ["acne"]
        elif skin_type == "Dry":
            concerns = ["dryness"]
        else:
            concerns = ["dull"]

    # Concerns filter — loose
    if concerns:
        filtered = filtered.reset_index(drop=True)
        mask = pd.Series([False] * len(filtered))
        for c in concerns:
            if c == "acne":
                keywords = "acne|blemish|pore|salicylic|benzoyl|breakout|niacinamide|oil control"
            elif c == "dark spots / uneven tone":
                keywords = "brightening|even tone|fade spots|whitening|hyperpigmentation|dark spots|melasma|pigment|arbutin|kojic|niacinamide|vitamin c|tranexamic"
            elif c == "dryness":
                keywords = "hydration|hyaluronic|moisturizing|dryness|ceramide"
            else:
                keywords = ""
            if keywords:
                mask |= filtered['primary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['secondary_target'].str.contains(keywords, case=False, na=False)
                mask |= filtered['key_actives'].str.contains(keywords, case=False, na=False)
        filtered = filtered[mask]

    st.success("Here's your routine:")

    recommended_products = []

    # 1. Cleanse
    cleansers = filtered[filtered['step'] == '1. Cleanse']
    if not cleansers.empty:
        chosen = cleansers.sample(1).iloc[0]
        st.write(f"**1. Cleanse** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**1. Cleanse** → Any gentle cleanser")

    # 2. Tone
    toners = filtered[filtered['step'] == '2. Tone/Exfoliate']
    if not toners.empty:
        chosen = toners.sample(1).iloc[0]
        st.write(f"**2. Tone** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**2. Tone** → Any hydrating toner")

    # 3. Treat
    treats = filtered[filtered['step'] == '3. Treat']
    if not treats.empty:
        chosen = treats.sample(1).iloc[0]
        st.write(f"**3. Treat** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**3. Treat** → Any serum")

    # 4. Moisturize
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        chosen = moist.sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**4. Moisturize** → Any moisturizer")

    # 5. Protect
    st.write("**5. Protect** → Any SPF 50+ in the morning")

    st.info("Start slow • Patch test • Use what feels good")

    # Products Grid
    st.markdown("---")
    st.subheader("🛒 Products Recommended for You")

    seen = set()
    unique_products = []
    for p in recommended_products:
        if p['product_id'] not in seen:
            seen.add(p['product_id'])
            unique_products.append(p)

    if unique_products:
        st.write("Here are the products we picked for you:")
        cols = st.columns(min(3, len(unique_products)))
        for idx, p in enumerate(unique_products):
            with cols[idx % 3]:
                st.markdown(f"**{p['product_id']}**")
                st.write(p['name'])
                st.caption(f"{p['primary_target']} • {p['key_actives']}")
    else:
        st.info("No specific matches this time — general advice is safe!")

    # Next Goals - Teaser
    st.markdown("---")
    st.subheader("🌟 Your Next Skin Goals")
    st.write("• Crystal clear skin")
    st.write("• Natural glow")
    st.write("• Youthful bounce")
    st.success("Come back soon for better recommendations. Your glow-up is coming! 🔜")

# UI
st.title("👋 Welcome to Skin Recommendation Engine")
st.write("Hi! Let's build your routine.")

with st.form("skin_form"):
    st.subheader("Your Skin Type")
    skin_option = st.selectbox("Select:", ["Oily", "Dry", "Combination", "Normal", "Not sure"])

    if skin_option == "Not sure":
        st.info("Quick guide:")
        for k, v in SKIN_TYPE_EXPLANATIONS.items():
            st.write(f"• **{k}**: {v}")
        skin_option = st.selectbox("Best match?", ["Oily", "Dry", "Combination", "Normal"])

    st.subheader("Current Concerns")
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
    selected_concerns = st.multiselect("Select all:", concern_options)

    st.subheader("Any apply?")
    sensitive = st.checkbox("Skin reacts easily")
    pregnant = st.checkbox("Pregnant / breastfeeding")
    prescription = st.checkbox("Using prescription skincare")

    area = st.radio("Shopping for:", ("Face", "Body", "Both"))

    submitted = st.form_submit_button("Get Routine", type="primary")

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
    concerns = [concerns_map.get(c) for c in selected_concerns if c != "None"]

    is_sensitive = sensitive
    is_pregnant = pregnant
    using_prescription = prescription

    if is_pregnant or using_prescription:
        st.warning("Safety first! Consult doctor.")
    elif is_sensitive and len(concerns) > 2:
        st.warning("Complex concerns — seek professional advice.")
    else:
        build_routine(df, skin_option, concerns, is_sensitive, is_pregnant, using_prescription, area)

# Shopping
st.markdown("---")
st.subheader("🛒 Browse Products")
query = st.text_input("Search keyword")
if query:
    matches = df[df['name'].str.lower().str.contains(query.lower(), na=False)]
    if matches.empty:
        st.info("No matches — try another word")
    else:
        for _, p in matches.iterrows():
            with st.expander(f"**{p['product_id']} — {p['name']}**"):
                st.write(f"Best for: {p['primary_target']} • {p['secondary_target']}")
                st.write(f"Key actives: {p['key_actives']}")
                st.write(f"Use: {p['recommended_time']} — {p['max_frequency']}")

st.caption("Thank you for trusting us with your skin 🌿")


