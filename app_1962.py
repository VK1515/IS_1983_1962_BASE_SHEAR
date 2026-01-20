import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet

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
# FULL Z TABLE – IS 1893:2025
# ==================================================
Z_TABLE = {
    "VI": {75:0.300,175:0.375,275:0.450,475:0.500,975:0.600,1275:0.625,2475:0.750,4975:0.940,9975:1.125},
    "V":  {75:0.200,175:0.250,275:0.300,475:0.333,975:0.400,1275:0.4167,2475:0.500,4975:0.625,9975:0.750},
    "IV": {75:0.140,175:0.175,275:0.210,475:0.233,975:0.280,1275:0.2917,2475:0.350,4975:0.440,9975:0.525},
    "III":{75:0.0625,175:0.085,275:0.100,475:0.125,975:0.167,1275:0.1875,2475:0.250,4975:0.333,9975:0.450},
    "II": {75:0.0375,175:0.050,275:0.060,475:0.075,975:0.100,1275:0.1125,2475:0.150,4975:0.200,9975:0.270}
}

# ==================================================
# SESSION STATE
# ==================================================
if "base_shear" not in st.session_state:
    st.session_state.base_shear = {}

# ==================================================
# FUNCTIONS (IS 1893:2025)
# ==================================================
def A_NH(T, site):
    if site == "A/B":
        return 2.5 if T <= 0.4 else 1/T
    if site == "C":
        return 2.5 if T <= 0.6 else 1.5/T
    return 2.5 if T <= 0.8 else 2/T

def delta_v(T, site):
    return 0.67 if T > 0.10 else {"A/B":0.80,"C":0.82,"D":0.85}[site]

def gamma_v(T, site):
    return {"A/B":1/T,"C":1.5/T,"D":2.0/T}[site]

# ==================================================
# TABS
# ==================================================
tab1, tab2, tab3 = st.tabs([
    "① Base Shear",
    "② Storey-wise Distribution & PDF",
    "③ Multi-Zone Study"
])

# ==================================================
# TAB 1 – BASE SHEAR
# ==================================================
with tab1:
    st.subheader("Base Shear Calculation")

    zone = st.selectbox("Earthquake Zone", list(Z_TABLE.keys()))
    TR = st.selectbox("Return Period (years)", sorted(Z_TABLE[zone].keys()))
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
            "Zone": zone,
            "TR (yr)": TR,
            "Z": Z,
            "I": I,
            "R": R,
            "Tx (s)": Tx,
            "Ty (s)": Ty,
            "Vx (kN)": Vx,
            "Vy (kN)": Vy,
            "Vv (kN)": Vv
        }

        st.success("Base shear computed")

        st.table(
            pd.DataFrame(
                st.session_state.base_shear.items(),
                columns=["Parameter","Value"]
            ).round(3)
        )

# ==================================================
# TAB 2 – STOREY DISTRIBUTION + STEP PLOT + PDF
# ==================================================
with tab2:
    st.subheader("Storey-wise Force Distribution")

    if not st.session_state.base_shear:
        st.warning("Compute base shear in Tab ① first.")
    else:
        bs = st.session_state.base_shear
        N = st.number_input("Number of Storeys", min_value=1, value=5, step=1)

        rows = []
        for i in range(1, N + 1):
            Wi = st.number_input(f"W{i} (kN)", value=bs["Vx (kN)"]/N, key=f"W{i}")
            Hi = st.number_input(f"H{i} (m)", value=3.0*i, key=f"H{i}")
            rows.append([i, Wi, Hi])

        df = pd.DataFrame(rows, columns=["Storey","Wi (kN)","Hi (m)"])
        df["WiHi²"] = df["Wi (kN)"] * df["Hi (m)"]**2

        df["QX"] = df["WiHi²"]/df["WiHi²"].sum() * bs["Vx (kN)"]
        df["QY"] = df["WiHi²"]/df["WiHi²"].sum() * bs["Vy (kN)"]
        df["QV"] = df["Wi (kN)"]/df["Wi (kN)"].sum() * bs["Vv (kN)"]

        df["VX"] = df["QX"][::-1].cumsum()[::-1]
        df["VY"] = df["QY"][::-1].cumsum()[::-1]
        df["VV"] = df["QV"][::-1].cumsum()[::-1]

        st.dataframe(df.round(3), use_container_width=True)

        # ---------- STEP PLOT WITH VALUES ----------
        fig, ax = plt.subplots(figsize=(6,8))
        ax.step(df["VX"], df["Hi (m)"], where="post", label="X-direction")
        ax.step(df["VY"], df["Hi (m)"], where="post", label="Y-direction")
        ax.step(df["VV"], df["Hi (m)"], where="post", linestyle="--", label="Vertical")

        for i in range(len(df)):
            h = df.loc[i, "Hi (m)"]
            ax.text(df.loc[i,"VX"], h, f'{df.loc[i,"VX"]:.1f}', fontsize=8, va="bottom")
            ax.text(df.loc[i,"VY"], h, f'{df.loc[i,"VY"]:.1f}', fontsize=8, va="top")
            ax.text(df.loc[i,"VV"], h, f'{df.loc[i,"VV"]:.1f}', fontsize=8, va="center")

        ax.set_xlabel("Storey Shear (kN)")
        ax.set_ylabel("Height (m)")
        ax.set_title("Storey-wise Shear – Step Plot")
        ax.legend()
        ax.grid(True)

        st.pyplot(fig)
        fig.savefig("storey_shear_step.png", dpi=300, bbox_inches="tight")

        # ---------- PDF EXPORT ----------
        if st.button("Export PDF (Base + Storey Results)"):
            doc = SimpleDocTemplate("IS1893_Storey_Results.pdf")
            styles = getSampleStyleSheet()

            content = [
                Paragraph("IS 1893:2025 – Seismic Analysis Output", styles["Title"]),
                Spacer(1,12),
                Paragraph("Base Shear Results", styles["Heading2"]),
                Table([[k,v] for k,v in bs.items()]),
                Spacer(1,12),
                Paragraph("Storey-wise Force Distribution", styles["Heading2"]),
                Table([df.columns.tolist()] + df.round(3).values.tolist()),
                Spacer(1,12),
                Image("storey_shear_step.png", width=380, height=520)
            ]

            doc.build(content)
            st.success("PDF generated: IS1893_Storey_Results.pdf")

# ==================================================
# TAB 3 – MULTI-ZONE STUDY
# ==================================================
with tab3:
    st.subheader("Multi-Zone Base Shear Comparison")

    zones = st.multiselect("Zones", list(Z_TABLE.keys()), default=["II","III","IV"])
    TR = st.selectbox("Return Period (years)", [75,175,275,475,975,1275,2475,4975,9975])

    if st.button("Compute Multi-Zone"):
        rows = []
        for z in zones:
            Z = Z_TABLE[z][TR]
            Vx = Z * A_NH(0.5,"A/B") * 10000 / 5
            Vy = Z * A_NH(0.7,"A/B") * 10000 / 5
            rows.append([z, Z, Vx, Vy])

        dfz = pd.DataFrame(rows, columns=["Zone","Z","Vx (kN)","Vy (kN)"])
        st.dataframe(dfz.round(3), use_container_width=True)

# ==================================================
# FOOTER
# ==================================================
st.markdown("---")
st.info(
    "📘 For educational use only.\n"
    "Independent verification is mandatory before professional application.\n\n"
    "Created by: Vrushali Kamalakar"
)
