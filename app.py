import streamlit as st
import pandas as pd

st.set_page_config(page_title="Skin Recommendation Engine", layout="centered")

@st.cache_data
def load_products():
    return pd.read_csv('products.csv')

df = load_products()

# Debug line (you can remove later)
st.write(f"**Debug: Loaded {len(df)} products**")

def build_routine(df, skin_type, concerns, is_sensitive, is_pregnant, using_prescription, area):
    # Very relaxed area filter
    if area == "Face":
        filtered = df[~df['name'].str.lower().str.contains('body wash|shower gel', na=False)]  # only exclude strong body washes
    elif area == "Body":
        filtered = df[df['name'].str.lower().str.contains('body', na=False)]
    else:
        filtered = df.copy()  # Both = almost everything

    # Safety only (very minimal)
    filtered = filtered[filtered.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    # Almost no skin type restriction — everyone gets "All" + their type
    filtered = filtered[
        filtered['suitable_skin_types'].str.contains('All', case=False, na=True) |
        filtered['suitable_skin_types'].str.contains(skin_type, case=False, na=True)
    ]

    # If still almost nothing, fall back to ALL safe products
    if len(filtered) < 5:
        filtered = df[df.apply(lambda row: is_safe(row, is_sensitive, is_pregnant, using_prescription), axis=1)]

    st.success("Here's a relaxed & safe routine for you:")

    recommended_products = []

    # 1. Cleanse
    cleansers = filtered[filtered['step'] == '1. Cleanse']
    if not cleansers.empty:
        chosen = cleansers.sample(1).iloc[0]
        st.write(f"**1. Cleanse** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**1. Cleanse** → Any gentle cleanser you like")

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
        st.write("**3. Treat** → Any serum that feels good")

    # 4. Moisturize
    moist = filtered[filtered['step'] == '4. Moisturize']
    if not moist.empty:
        chosen = moist.sample(1).iloc[0]
        st.write(f"**4. Moisturize** → {chosen['product_id']} — {chosen['name']}")
        recommended_products.append(chosen)
    else:
        st.write("**4. Moisturize** → Any moisturizer you enjoy")

    # 5. Protect
    st.write("**5. Protect** → Any SPF 50+ you like in the morning")

    st.info("Start slow • Patch test • Use what feels good on your skin")

    # Products section - always show what we actually recommended
    st.markdown("---")
    st.subheader("🛒 Products Recommended for You")

    seen = set()
    unique_products = []
    for p in recommended_products:
        if p['product_id'] not in seen:
            seen.add(p['product_id'])
            unique_products.append(p)

    if unique_products:
        st.write("Here are the products we picked for your routine:")
        cols = st.columns(min(3, len(unique_products)))
        for idx, p in enumerate(unique_products):
            with cols[idx % 3]:
                st.markdown(f"**{p['product_id']}**")
                st.write(p['name'])
                st.caption(f"{p['primary_target']} • {p['key_actives']}")
    else:
        st.info("No products matched perfectly, but the advice above is still safe to follow!")

    # Next Goals - short teaser
    st.markdown("---")
    st.subheader("🌟 Your Next Skin Goals")
    st.write("• Crystal clear skin")
    st.write("• Natural glow")
    st.write("• Youthful bounce")
    st.success("Come back in a few weeks — we’ll have even better recommendations for you! 🔜")

# UI remains the same
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

    if pregnant or prescription:
        st.warning("Safety first! Consult doctor.")
    elif sensitive and len(concerns) > 2:
        st.warning("Complex concerns — seek professional advice.")
    else:
        build_routine(df, skin_option, concerns, sensitive, pregnant, prescription, area)

# Shopping section (unchanged)
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
