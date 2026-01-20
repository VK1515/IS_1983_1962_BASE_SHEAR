import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="IS 1893:2025 Seismic Force Calculator",
    layout="wide"
)

st.title("IS 1893:2025 – Seismic Force Calculator")
st.caption(
    "Equivalent Static Method | Direction-wise\n"
    "⚠️ For educational use only\n"
    "Created by: Vrushali Kamalakar"
)

# ==================================================
# Z TABLE (IS 1893:2025 – trimmed, stable)
# ==================================================
Z_TABLE = {
    "VI": {75:0.300, 175:0.375, 275:0.450, 475:0.500},
    "V":  {75:0.200, 175:0.250, 275:0.300, 475:0.333},
    "IV": {75:0.140, 175:0.175, 275:0.210, 475:0.233},
    "III":{75:0.0625,175:0.085,275:0.100,475:0.125},
    "II": {75:0.0375,175:0.050,275:0.060,475:0.075}
}

# ==================================================
# SESSION STATE
# ==================================================
if "base_shear" not in st.session_state:
    st.session_state.base_shear = {}
if "storey_df" not in st.session_state:
    st.session_state.storey_df = None

# ==================================================
# IS 1893 FUNCTIONS
# ==================================================
def A_NH(T, site):
    if site == "A/B":
        return 2.5 if T <= 0.4 else 1 / T
    if site == "C":
        return 2.5 if T <= 0.6 else 1.5 / T
    return 2.5 if T <= 0.8 else 2 / T

def delta_v(T, site):
    return 0.67 if T > 0.10 else {"A/B":0.80,"C":0.82,"D":0.85}[site]

def gamma_v(T, site):
    return {"A/B":1/T,"C":1.5/T,"D":2/T}[site]

# ==================================================
# STEP-PLOT ANNOTATION FUNCTION (KEY FIX)
# ==================================================
def annotate_step_plot(ax, x_vals, y_vals, label, color):
    x_max = max(x_vals)
    for x, y in zip(x_vals, y_vals):
        ax.text(
            x + 0.03 * x_max,
            y,
            f"{x:.1f}",
            va="center",
            ha="left",
            fontsize=8,
            color=color
        )

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3 = st.tabs([
    "① Base Shear",
    "② Storey-wise Distribution",
    "③ About"
])

# ==================================================
# TAB 1 – BASE SHEAR
# ==================================================
with tab1:
    st.subheader("Base Shear Calculation")

    zone = st.selectbox("Earthquake Zone", list(Z_TABLE.keys()))
    TR = st.selectbox("Return Period (years)", list(Z_TABLE[zone].keys()))
    Z = Z_TABLE[zone][TR]

    I = st.number_input("Importance Factor (I)", value=1.0)
    R = st.number_input("Response Reduction Factor (R)", value=5.0)
    site = st.selectbox("Site Class", ["A/B","C","D"])
    W = st.number_input("Total Seismic Weight W (kN)", value=10000.0)

    H = st.number_input("Total Height H (m)", value=15.0)
    dx = st.number_input("Plan Dimension X (m)", value=10.0)
    dy = st.number_input("Plan Dimension Y (m)", value=15.0)
    TV = st.number_input("Vertical Period Tv (s)", value=0.4)

    if st.button("Compute Base Shear"):
        Tx = 0.09 * H / math.sqrt(dx)
        Ty = 0.09 * H / math.sqrt(dy)

        Vx = (Z * I * A_NH(Tx, site) / R) * W
        Vy = (Z * I * A_NH(Ty, site) / R) * W
        Vv = Z * I * delta_v(TV, site) * gamma_v(TV, site) * W

        st.session_state.base_shear = {
            "Tx (s)": Tx,
            "Ty (s)": Ty,
            "Vx (kN)": Vx,
            "Vy (kN)": Vy,
            "Vv (kN)": Vv,
            "W (kN)": W
        }

        st.success("Base shear computed and locked.")

        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Tx (s)", f"{Tx:.3f}")
        c2.metric("Ty (s)", f"{Ty:.3f}")
        c3.metric("Vx (kN)", f"{Vx:.1f}")
        c4.metric("Vy (kN)", f"{Vy:.1f}")
        c5.metric("Vv (kN)", f"{Vv:.1f}")

        st.table(
            pd.DataFrame(
                st.session_state.base_shear.items(),
                columns=["Parameter","Value"]
            ).round(3)
        )

# ==================================================
# TAB 2 – STOREY DISTRIBUTION + STEP PLOT
# ==================================================
with tab2:
    if not st.session_state.base_shear:
        st.warning("Compute base shear in Tab ① first.")
    else:
        bs = st.session_state.base_shear

        N = st.number_input("Number of Storeys", min_value=1, value=5)

        rows = []
        for i in range(1, N+1):
            Wi = st.number_input(
                f"W{i} (kN)",
                value=bs["W (kN)"]/N,
                key=f"Wi_{i}"
            )
            Hi = st.number_input(
                f"H{i} (m)",
                value=3.0*i,
                key=f"Hi_{i}"
            )
            rows.append([i, Wi, Hi])

        df = pd.DataFrame(rows, columns=["Storey","Wi","Hi"])
        df["WiHi2"] = df["Wi"] * df["Hi"]**2

        df["VX"] = (df["WiHi2"]/df["WiHi2"].sum()*bs["Vx (kN)"])[::-1].cumsum()[::-1]
        df["VY"] = (df["WiHi2"]/df["WiHi2"].sum()*bs["Vy (kN)"])[::-1].cumsum()[::-1]
        df["VV"] = (df["Wi"]/df["Wi"].sum()*bs["Vv (kN)"])[::-1].cumsum()[::-1]

        st.dataframe(df.round(3), use_container_width=True)

        # -------- STEP PLOT WITH VALUES --------
        fig, ax = plt.subplots(figsize=(6,8))

        ax.step(df["VX"], df["Hi"], where="post", label="X", color="tab:blue")
        ax.step(df["VY"], df["Hi"], where="post", label="Y", color="tab:green")
        ax.step(df["VV"], df["Hi"], where="post", label="Vertical", linestyle="--", color="black")

        annotate_step_plot(ax, df["VX"], df["Hi"], "X", "tab:blue")
        annotate_step_plot(ax, df["VY"], df["Hi"], "Y", "tab:green")
        annotate_step_plot(ax, df["VV"], df["Hi"], "V", "black")

        ax.set_xlabel("Storey Shear (kN)")
        ax.set_ylabel("Height (m)")
        ax.set_title("Storey-wise Shear Distribution (Step Plot)")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

# ==================================================
# TAB 3 – ABOUT
# ==================================================
with tab3:
    st.info(
        "This application demonstrates IS 1893:2025 Equivalent Static Method.\n\n"
        "For educational use only.\n\n"
        "Created by: Vrushali Kamalakar"
    )
