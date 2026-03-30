import os, tempfile
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from odf.opendocument import OpenDocumentText
from odf.text import P, H

def generate_report(usage_summary, locations, prediction):
    tmp = tempfile.mkdtemp()
    fig, ax = plt.subplots(figsize=(6, 3))
    labels = ["Daily (MB)", "Weekly (MB)", "Monthly (MB)"]
    values = [usage_summary["daily"], usage_summary["weekly"], usage_summary["monthly"]]
    ax.bar(labels, values, color=["#00d4ff","#00ff88","#ff6b6b"])
    ax.set_title("Network Usage Summary")
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#1a1a2e")
    ax.tick_params(colors="white")
    ax.title.set_color("white")
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_color("white")
    graph_path = os.path.join(tmp, "usage_graph.png")
    plt.tight_layout()
    plt.savefig(graph_path, dpi=100)
    plt.close()

    doc = OpenDocumentText()
    doc.text.addElement(H(outlinelevel=1, text="Smart Network Monitoring Report"))
    doc.text.addElement(P(text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"))
    doc.text.addElement(P(text=""))
    doc.text.addElement(H(outlinelevel=2, text="Usage Summary"))
    doc.text.addElement(P(text=f"Daily: {usage_summary['daily']} MB"))
    doc.text.addElement(P(text=f"Weekly: {usage_summary['weekly']} MB"))
    doc.text.addElement(P(text=f"Monthly: {usage_summary['monthly']} MB"))
    doc.text.addElement(P(text=""))
    doc.text.addElement(H(outlinelevel=2, text="AI Prediction"))
    doc.text.addElement(P(text=prediction))
    doc.text.addElement(P(text=""))
    doc.text.addElement(H(outlinelevel=2, text="Location Analysis"))
    for loc in locations:
        sig = loc.get("signal") or 0
        quality = "Good" if sig > 70 else "Medium" if sig > 40 else "Poor"
        doc.text.addElement(P(text=f"{loc['name']}: {sig}% - {quality}"))

    report_path = os.path.join(tmp, "network_report.odt")
    doc.save(report_path)
    return report_path
