// Builds slides/Project2_Wafer_Defect_Routing.pptx: the same six slides as the published deck.
// Speaker notes are read from slides/deck/slides/*.html, figures from slides/figures/.
// Usage: PPTX_SKILL_DIR=<pptx skill folder> node slides/build_pptx.js
// (needs the pptxgenjs package; the skill folder supplies apply_theme.js, which writes the theme colours into the file)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(path.join(process.env.PPTX_SKILL_DIR, "scripts", "apply_theme.js"));

const HERE = __dirname;
const OUT = path.join(HERE, "Project2_Wafer_Defect_Routing.pptx");
const fig = (name) => path.join(HERE, "figures", name);
const notes = (id) => {
  const html = fs.readFileSync(path.join(HERE, "deck", "slides", id + ".html"), "utf8");
  return html.match(/<aside>([\s\S]*?)<\/aside>/)[1].trim();
};

const THEME = {
  name: "Wafer Defect Routing", headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "14213D", lt1: "FCFCFB", dk2: "4A5568", lt2: "F1F0EC", accent1: "2A78D6", accent2: "EB6834",
            accent3: "B8431A", accent4: "1E2D4F", accent5: "BFC8D8", accent6: "F29A70", hlink: "2A78D6", folHlink: "6250D6" },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "DBA5106 Project 2: Wafer Defect Routing";
const C = pres.SchemeColor;
const M = 0.6, W = 13.333 - 2 * M;

for (const [name, bg, titleColor, footColor] of [["LIGHT", C.background1, C.text1, C.text2], ["DARK", C.text1, C.background1, C.accent5]]) {
  pres.defineSlideMaster({
    title: name, background: { color: bg },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: M, y: 0.45, w: W, h: 0.95, fontSize: 32, bold: true, color: titleColor, align: "left", valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: M, y: 6.8, w: W, h: 0.4, fontSize: 11, color: footColor, align: "left", valign: "middle", margin: 0 }, text: "" } },
    ],
  });
}

function add(master, section, id, title, footer) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addText(footer, { placeholder: "body" });
  s.addNotes(notes(id));
  return s;
}
function card(s, x, y, w, h, head, body, opt = {}) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: opt.fill || C.background2 }, line: { color: opt.fill || C.background2 }, objectName: "Card " + head });
  s.addText([{ text: head, options: { bold: true, fontSize: 16, color: opt.head || C.text1, breakLine: true } },
             { text: body, options: { fontSize: 14, color: opt.body || C.text2 } }],
            { x: x + 0.2, y: y + 0.1, w: w - 0.4, h: h - 0.2, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
}
function stat(s, x, y, w, h, num, label, opt = {}) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: opt.fill || C.background2 }, line: { color: opt.fill || C.background2 }, objectName: "Stat " + num });
  s.addText(num, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: h * 0.5, fontSize: opt.size || 34, bold: true, color: opt.num || C.text1, valign: "middle", margin: 0, isTextBox: true });
  s.addText(label, { x: x + 0.2, y: y + 0.12 + h * 0.5, w: w - 0.4, h: h * 0.5 - 0.2, fontSize: 12, color: opt.label || C.text2, valign: "top", margin: 0, isTextBox: true });
}
const text = (s, t, o) => s.addText(t, Object.assign({ fontSize: 14, color: C.text2, valign: "top", margin: 0, isTextBox: true }, o));
const img = (s, name, alt, x, y, w, h) => s.addImage({ path: fig(name), x, y, w, h, altText: alt });

// 1. The problem
pres.addSection({ title: "Problem and loss" });
let s = add("LIGHT", "Problem and loss", "problem", "Which team gets this wafer?",
  "DBA5106 Project 2, Version 2 (with data). Orange = failing die, light blue = passing die. Source: WM-811K (Kaggle, qingyi/wm811k-wafer-map).");
text(s, "A wafer shows a local cluster of failing dies. The model predicts which of two look-alike patterns it is.", { x: M, y: 1.6, w: 5.9, h: 0.8, fontSize: 16, color: C.text1 });
card(s, M, 2.5, 5.9, 1.05, "Edge-Loc: hold the tool", "A tool’s edge process is drifting. It repeats on every wafer.");
card(s, M, 3.7, 5.9, 1.05, "Loc: normal review", "A one-off particle or local event on that wafer.");
img(s, "s1_wafers.png", "Two wafer maps. Left, Loc: a small cluster of failing dies in the interior. Right, Edge-Loc: failing dies clustered along the top edge.", 6.9, 1.6, 5.8, 3.04);
card(s, M, 4.95, 3.9, 1.7, "Data", "WM-811K, real fab wafer maps. 8,782 labelled wafers, 59% Edge-Loc. We built 10 physical features per map.");
card(s, 4.72, 4.95, 3.9, 1.7, "Evaluation loss", "(5 × missed Edge-Loc + 1 × false alarm) / wafers. A missed tool problem costs 5 unnecessary holds. Our assumption.");
card(s, 8.83, 4.95, 3.9, 1.7, "Why this question", "“Defect or no defect” is almost perfectly predictable here (AUC 0.995). We chose a harder, more useful question.");

// 2. Four models
pres.addSection({ title: "Models and decision" });
s = add("LIGHT", "Models and decision", "models", "Four models, one fair comparison",
  "Solid = log loss, dashed = L2. Intervals resample whole lots, 2,000 times. Validation: 1,756 wafers.");
const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: C.text1, valign: "middle" }, o) });
s.addTable([
  [cell("Validation AUC", { bold: true, fill: { color: C.background2 } }), cell("L2 loss", { bold: true, align: "right", fill: { color: C.background2 } }), cell("Log loss", { bold: true, align: "right", fill: { color: C.background2 } })],
  [cell("Glassbox: L1 linear model"), cell("0.958", { align: "right" }), cell("0.966", { align: "right", bold: true })],
  [cell("Blackbox: boosted trees"), cell("0.966", { align: "right" }), cell("0.972", { align: "right", bold: true })],
], { x: M, y: 1.6, w: 6.0, colW: [3.2, 1.4, 1.4], rowH: 0.48, border: { type: "solid", pt: 0.75, color: "E1E0D9" }, objectName: "AUC table" });
card(s, M, 3.3, 6.0, 1.4, "Log loss beats L2 for both", "+0.008 for the glassbox, +0.007 for the blackbox. Both intervals exclude zero. L2 scores fall outside 0–1 for 20–29% of wafers.");
card(s, M, 4.9, 6.0, 1.15, "Why validation, not training", "The blackbox scores 1.000 on its own training data and 0.972 on validation.");
img(s, "s2_auc.png", "Validation AUC with 95% intervals: glassbox L2 0.958, glassbox log loss 0.966, blackbox L2 0.966, blackbox log loss 0.972. The intervals overlap.", 7.0, 1.6, 5.7, 2.85);
text(s, [{ text: "How we kept it fair: ", options: { bold: true, color: C.text1 } }, { text: "split by lot, 60 / 20 / 20. Each model tuned separately by cross-validation inside the training split. 24 configurations in total." }], { x: 7.0, y: 4.7, w: 5.7, h: 1.3 });

// 3. Decision and threshold
s = add("LIGHT", "Models and decision", "decision", "We chose the glassbox, at threshold 0.28",
  "Validation split. Minimising plain misclassification would move the threshold the other way, to 0.61.");
card(s, M, 1.6, 6.0, 1.5, "Higher AUC, but not lower cost", "The blackbox’s AUC is 0.006 higher (95% CI +0.0001 to +0.012). Its evaluation loss is not lower: 0.149 against the glassbox’s 0.143.");
card(s, M, 3.25, 6.0, 1.1, "Rule set before looking", "A blackbox must cut the cost by 10% to earn its opacity. It didn’t.");
stat(s, M, 4.55, 2.9, 1.7, "−27%", "cost vs a 0.5 threshold (0.196 → 0.143)", { num: C.accent3 });
stat(s, 3.7, 4.55, 2.9, 1.7, "−1.8 pts", "accuracy (91.6% → 89.8%)");
img(s, "s3_threshold.png", "Cost per wafer against the decision threshold. Our evaluation loss is lowest at a threshold of 0.28. The misclassification rate is lowest near 0.61.", 7.0, 1.6, 5.7, 3.29);
text(s, "At 0.28 we miss 18 Edge-Loc wafers instead of 49, for 161 false alarms instead of 99.", { x: 7.0, y: 5.1, w: 5.7, h: 0.9 });

// 4. Calibration
pres.addSection({ title: "Calibration and interpretability" });
s = add("LIGHT", "Calibration and interpretability", "calibration", "Calibration: mildly off, then fixed",
  "Validation split, equal-count bins. The glassbox stays the cheaper model for cost ratios from 3 to 8.");
img(s, "s4_calibration.png", "Reliability diagram. The L2 glassbox is far from the diagonal. The chosen model is close to it, and closer still after isotonic calibration.", M, 1.6, 6.6, 4.11);
stat(s, 7.5, 1.6, 5.23, 1.2, "0.031 → 0.021", "calibration error (ECE) of the chosen model; AUC unchanged", { size: 28 });
card(s, 7.5, 2.95, 5.23, 1.0, "What was wrong", "It under-predicts between 0.2 and 0.5, where our threshold sits.");
card(s, 7.5, 4.1, 5.23, 1.35, "The fix", "Isotonic regression, fitted on out-of-fold training scores so validation stays clean. Platt scaling barely helps a logistic model (0.029).");
card(s, 7.5, 5.6, 5.23, 1.1, "Why it matters", "Theory gives the threshold for calibrated probabilities: 1/(1+5) = 0.167. Ours is 0.22, at almost the same cost.");

// 5. SHAP
s = add("LIGHT", "Calibration and interpretability", "shap", "Tree SHAP on the blackbox: it looks at the edge",
  "Caution: the fail-rate features are correlated, so SHAP credit among them is unstable. Orange pushes towards Edge-Loc, blue towards Loc.");
text(s, "Global: what the model relies on", { x: M, y: 1.5, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
img(s, "s5_shap_global.png", "Mean absolute SHAP value per feature. largest_cluster_radius is far ahead at 4.0, then edge_fail_rate at 1.8 and outer_ring_fail_rate at 0.9.", M, 1.95, 5.3, 3.9);
text(s, "Where the largest cluster sits dominates, then the edge fail rates.", { x: M, y: 5.95, w: 5.3, h: 0.6 });
text(s, "Local: two wafers, next to their maps", { x: 6.5, y: 1.5, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
text(s, [{ text: "Most confident Edge-Loc. ", options: { bold: true, color: C.text1 } }, { text: "P(Edge-Loc) = 1.000. The cluster is at the edge (radius 0.93)." }], { x: 6.5, y: 1.95, w: 6.2, h: 0.5 });
img(s, "s5_shap_local_correct.png", "Wafer map with failing dies along the top edge, beside its SHAP values. largest_cluster_radius = 0.93 pushes strongly towards Edge-Loc.", 6.5, 2.5, 5.6, 1.68);
text(s, [{ text: "Costliest mistake. ", options: { bold: true, color: C.text1 } }, { text: "Labelled Edge-Loc, P = 0.000. Its cluster is near the centre (radius 0.32). Possibly a labelling error." }], { x: 6.5, y: 4.3, w: 6.2, h: 0.6 });
img(s, "s5_shap_local_mistake.png", "Wafer map with a cluster of failing dies near the centre, beside its SHAP values. largest_cluster_radius = 0.32 pushes strongly towards Loc.", 6.5, 4.95, 5.6, 1.68);

// 6. Result
pres.addSection({ title: "Result" });
s = add("DARK", "Result", "result", "Test result, used once, and an honest audit",
  "Final model: L1 logistic regression (log loss) + isotonic calibration, threshold 0.22. Test split: 1,758 wafers.");
const dark = { fill: C.accent4, num: C.background1, label: C.accent5 };
stat(s, 0.6, 1.6, 2.9, 1.6, "0.958", "AUC (95% CI 0.946 to 0.969)", dark);
stat(s, 3.68, 1.6, 2.9, 1.6, "0.181", "evaluation loss per wafer (CI 0.143 to 0.223)", dark);
stat(s, 6.76, 1.6, 2.9, 1.6, "97.3%", "of Edge-Loc wafers caught; accuracy 88.3%", dark);
stat(s, 9.84, 1.6, 2.9, 1.6, "−56%", "cost vs holding the tool for every wafer (0.409)", Object.assign({}, dark, { num: C.accent6 }));
const col = (x, head, body) => {
  text(s, head, { x, y: 3.6, w: 3.9, h: 0.45, fontSize: 18, bold: true, color: C.background1 });
  text(s, body, { x, y: 4.15, w: 3.9, h: 2.4, color: C.accent5, paraSpaceAfter: 6 });
};
col(0.6, "Audit of our own choice", "On test, the blackbox we didn’t choose scores 0.158 against our 0.181. The difference (−0.023, 95% CI −0.051 to +0.007) isn’t distinguishable from zero. We did not switch after seeing test.");
const bullets = (items) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } }));
col(4.72, "Limits", bullets(["The 5:1 cost ratio is our assumption.", "Test is worse than validation (0.181 vs 0.143): the optimiser’s curse.", "Labels are engineers’ judgements; some look wrong."]));
col(8.83, "What we did differently", bullets(["Our own physical features, not a CNN.", "Splits by lot; 24 configurations; test used once.", "An interval on every comparison."]));

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
