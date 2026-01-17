
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
import tempfile

ah_table = {
    "0":   {"Hard": 0.00, "Average": 0.00, "Soft": 0.00},
    "I":   {"Hard": 0.01, "Average": 0.01, "Soft": 0.02},
    "II":  {"Hard": 0.02, "Average": 0.03, "Soft": 0.04},
    "III": {"Hard": 0.04, "Average": 0.05, "Soft": 0.06},
    "IV":  {"Hard": 0.05, "Average": 0.06, "Soft": 0.08},
    "V":   {"Hard": 0.06, "Average": 0.08, "Soft": 0.10},
    "VI":  {"Hard": 0.08, "Average": 0.10, "Soft": 0.12}
}

st.title("IS 1893 : 1962 Seismic Force Calculator")
st.markdown("**Design Equation:**  \nF = ah × W")

zone = st.selectbox("Select Seismic Zone", ["0", "I", "II", "III", "IV", "V", "VI"])
soil = st.selectbox("Select Soil Type", ["Hard", "Average", "Soft"])
W = st.number_input("Enter Seismic Weight W", min_value=0.0, value=0.0, step=1.0)

ah = ah_table[zone][soil]
st.info(f"Horizontal Seismic Coefficient (ah) = {ah}")

if st.button("Compute Seismic Force"):
    F = ah * W
    st.success(f"Seismic Force, F = ah × W = {round(F, 4)}")

    def generate_pdf():
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=25 * mm,
            leftMargin=25 * mm,
            topMargin=25 * mm,
            bottomMargin=25 * mm
        )

        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("<b>IS 1893 : 1962 Seismic Force Calculation Report</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

        table_data = [
            ["Parameter", "Value"],
            ["Seismic Zone", zone],
            ["Soil Type", soil],
            ["Seismic Weight (W)", str(W)],
            ["Horizontal Seismic Coefficient (ah)", str(ah)]
        ]

        elements.append(Table(table_data, colWidths=[70 * mm, 80 * mm]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("F = ah × W", styles["Normal"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Result: F = {round(F, 4)}", styles["Normal"]))

        doc.build(elements)
        return temp_file.name

    pdf_path = generate_pdf()

    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            "Download PDF Report",
            pdf_file,
            file_name="IS_1893_1962_Seismic_Force_Report.pdf",
            mime="application/pdf"
        )
