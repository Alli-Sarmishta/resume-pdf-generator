import os
import subprocess
from flask import Flask, request, jsonify

OUTPUT_DIR = "generated_resumes"

def latex_escape(text):
    return str(text).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_")\
        .replace("#", "\\#").replace("{", "\\{").replace("}", "\\}").replace("^", "\\^{}")

def format_links(links):
    return [f"\\href{{https://{latex_escape(link)}}}{{{latex_escape(link)}}}" for link in links]

def format_summary(summary):
    return f"\\section*{{Summary}}\n{latex_escape(summary)}"

def format_skills(skills):
    lines = []
    if "TechnicalSkills" in skills:
        lines.append(f"\\textbf{{Technical Skills:}} {latex_escape(', '.join(skills['TechnicalSkills']))}\\\\")
    if "SoftSkills" in skills:
        lines.append(f"\\textbf{{Soft Skills:}} {latex_escape(', '.join(skills['SoftSkills']))}")
    return "\\section*{Skills}\n" + "\n".join(lines)

def format_education(education):
    blocks = []
    for edu in education:
        line = f"\\textbf{{{latex_escape(edu.get('Degree', ''))}}} \\\\" \
               f"{latex_escape(edu.get('Institution', ''))} ({latex_escape(edu.get('Year', ''))}) \\\\"
        if 'CGPA' in edu:
            line += f"\\textit{{CGPA:}} {latex_escape(edu['CGPA'])} \\\\"
        if 'Percentage' in edu:
            line += f"\\textit{{Percentage:}} {latex_escape(edu['Percentage'])} \\\\"
        if 'Achievements' in edu:
            for ach in edu['Achievements']:
                line += f"\\quad - {latex_escape(ach)} \\\\"
        if 'RelevantCoursework' in edu:
            line += "\\textbf{Relevant Coursework:} " + ", ".join([latex_escape(c) for c in edu['RelevantCoursework']]) + "\\\\"
        blocks.append(line)
    return "\\section*{Education}\n" + "\n\n".join(blocks)

def format_experience(experience):
    if not experience:
        return ""
    blocks = []
    for exp in experience:
        line = f"\\textbf{{{latex_escape(exp.get('job_title', ''))}}} — {latex_escape(exp.get('company', ''))} \\hfill {latex_escape(exp.get('duration', ''))} \\\\" \
               f"{latex_escape(exp.get('description', ''))}"
        blocks.append(line)
    return "\\section*{Experience}\n" + "\n\\vspace{0.1cm}\n".join(blocks)

def format_projects(projects):
    blocks = []
    for proj in projects:
        line = f"\\textbf{{{latex_escape(proj.get('Name', ''))}}} \\hfill {latex_escape(proj.get('Date', ''))} \\\\" \
               f"{latex_escape(proj.get('Description', ''))} \\\\"
        if 'Technologies' in proj:
            line += f"\\textit{{Technologies:}} {latex_escape(proj['Technologies'])} \\\\"
        if 'Award' in proj:
            line += f"\\textit{{Award:}} {latex_escape(proj['Award'])} \\\\"
        blocks.append(line)
    return "\\section*{Projects}\n" + "\n\\vspace{0.1cm}\n".join(blocks)

def format_certifications(certs):
    if not certs:
        return ""
    blocks = []
    for cert in certs:
        line = f"\\textbf{{{latex_escape(cert.get('certification_name', ''))}}} — {latex_escape(cert.get('issuing_organization', ''))} ({latex_escape(cert.get('year', ''))}) \\\\"
        blocks.append(line)
    return "\\section*{Certifications}\n" + "\n".join(blocks)

def generate_resume_pdf(data):
    user_id = data.get("userId", "user")
    job_id = data.get("job", {}).get("id", "job")
    pdf_basename = f"{user_id}_{job_id}"
    pdf_path = os.path.join(OUTPUT_DIR, f"{pdf_basename}.pdf")
    tex_path = os.path.join(OUTPUT_DIR, f"{pdf_basename}.tex")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    contact_lines = [f"{{\\LARGE \\textbf{{{latex_escape(data.get('Name', ''))}}}}}"]
    if data.get("Email"):
        contact_lines.append(latex_escape(data["Email"]))
    if data.get("Phone"):
        contact_lines.append(latex_escape(data["Phone"]))
    if data.get("Links"):
        contact_lines.extend(format_links(data["Links"]))

    latex = f"""
\\documentclass[10pt]{{article}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{parskip}}
\\pagenumbering{{gobble}}

\\begin{{document}}

\\begin{{center}}
""" + " \\\\ \n".join(contact_lines) + "\n\\end{center}\n"

    if data.get("Summary"):
        latex += "\n" + format_summary(data["Summary"])
    if data.get("Skills"):
        latex += "\n" + format_skills(data["Skills"])
    if data.get("Education"):
        latex += "\n" + format_education(data["Education"])
    if data.get("Experience"):
        latex += "\n" + format_experience(data["Experience"])
    if data.get("Projects"):
        latex += "\n" + format_projects(data["Projects"])
    if data.get("Certifications"):
        latex += "\n" + format_certifications(data["Certifications"])

    latex += "\n\\end{document}"

    with open(tex_path, "w") as f:
        f.write(latex)

    try:
        result = subprocess.run([
            "pdflatex",
            "-interaction=nonstopmode",
            f"-jobname={pdf_basename}",
            "-output-directory", OUTPUT_DIR,
            tex_path
        ], check=True, capture_output=True, text=True)

        print("✅ pdflatex stdout:\n", result.stdout)
        print("✅ pdflatex stderr:\n", result.stderr)

        return {
            "user": user_id,
            "job": job_id,
            "message": "Resume generated",
            "pdf": os.path.join(OUTPUT_DIR, f"{pdf_basename}.pdf")
        }

    except subprocess.CalledProcessError as e:
        print("❌ Error generating PDF:", e)
        print("❌ stdout:", e.stdout)
        print("❌ stderr:", e.stderr)
        return None

# --------------------- Flask Setup ---------------------

app = Flask(__name__)

@app.route("/generate_resume", methods=["POST"])
def handle_resume_generation():
    try:
        data = request.json
        result = generate_resume_pdf(data)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"error": "PDF generation failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

