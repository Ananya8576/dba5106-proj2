// Builds slides/Project2_Scratch_Detection.pptx: the six slides of the second run (MixedWM38, Scratch vs not).
// Speaker notes are read from slides/deck_scratch/slides/*.html, figures from slides/figures_scratch/.
// Usage: PPTX_SKILL_DIR=<pptx skill folder> node slides/build_pptx_scratch.js
// (needs the pptxgenjs package; the skill folder supplies apply_theme.js, which writes the theme colours into the file)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(path.join(process.env.PPTX_SKILL_DIR, "scripts", "apply_theme.js"));

const HERE = __dirname;
const OUT = path.join(HERE, "Project2_Scratch_Detection.pptx");
const fig = (name) => path.join(HERE, "figures_scratch", name);
const notes = (id) => {
  const html = fs.readFileSync(path.join(HERE, "deck_scratch", "slides", id + ".html"), "utf8");
  return html.match(/<aside>([\s\S]*?)<\/aside>/)[1].trim();
};

const THEME = {
  name: "Scratch Detection", headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "14213D", lt1: "FCFCFB", dk2: "4A5568", lt2: "F1F0EC", accent1: "2A78D6", accent2: "EB6834",
            accent3: "B8431A", accent4: "1E2D4F", accent5: "BFC8D8", accent6: "F29A70", hlink: "2A78D6", folHlink: "6250D6" },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";                       // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "DBA5106 Project 2: Scratch Detection";
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
pres.addSection({ title: "Problem and data" });
let s = add("LIGHT", "Problem and data", "problem", "Is there a scratch on this wafer?",
  "DBA5106 Project 2, second run, same pipeline. Orange = failing die, light blue = passing die. Source: MixedWM38 (Kaggle, co1d7era/mixedtype-wafer-defect-datasets).");
text(s, "A scratch is a thin line of failing dies from mechanical contact. Here it must be found among other defects.", { x: M, y: 1.6, w: 5.9, h: 0.8, fontSize: 16, color: C.text1 });
card(s, M, 2.5, 5.9, 1.05, "Scratch: hold the handling path", "A robot, carrier or polishing step is damaging wafers. It repeats until fixed.");
card(s, M, 3.7, 5.9, 1.05, "No scratch: normal review", "The wafer may carry other patterns, but not this one.");
img(s, "s1_wafers.png", "Two wafer maps. Left, a wafer labelled with a scratch alone. Right, a wafer labelled Center, Edge-Loc and Scratch. In neither is the scratch easy to see by eye.", 6.9, 1.6, 5.8, 3.04);
card(s, M, 4.95, 3.9, 1.7, "Data", "MixedWM38: 36,991 wafer maps, each labelled with every pattern it has. 49% have a scratch (balanced by the authors, partly with generated maps).");
card(s, 4.72, 4.95, 3.9, 1.7, "Cleaning we had to do", "Dropped 1,024 duplicate maps (97.7% scratch). Deleted the die-count feature: it gave the label away.");
card(s, 8.83, 4.95, 3.9, 1.7, "Everything else is the same", "Same features, models, search grids and split sizes. Same loss: (5 × missed + 1 × false alarm) / wafers.");

// 2. Four models
pres.addSection({ title: "Models and decision" });
s = add("LIGHT", "Models and decision", "models", "The same four models, a very different picture",
  "Solid = log loss, dashed = L2. Intervals resample wafers, 2,000 times. Validation: 7,398 wafers. Training AUC of the blackbox: 0.930.");
const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: C.text1, valign: "middle" }, o) });
s.addTable([
  [cell("Validation AUC", { bold: true, fill: { color: C.background2 } }), cell("L2 loss", { bold: true, align: "right", fill: { color: C.background2 } }), cell("Log loss", { bold: true, align: "right", fill: { color: C.background2 } })],
  [cell("Glassbox: L1 linear model"), cell("0.597", { align: "right" }), cell("0.654", { align: "right", bold: true })],
  [cell("Blackbox: boosted trees"), cell("0.879", { align: "right" }), cell("0.881", { align: "right", bold: true })],
], { x: M, y: 1.6, w: 6.0, colW: [3.2, 1.4, 1.4], rowH: 0.48, border: { type: "solid", pt: 0.75, color: "E1E0D9" }, objectName: "AUC table" });
card(s, M, 3.3, 6.0, 1.4, "The glassbox can’t see a thin line", "Zone fail rates don’t describe a scratch, and a linear model can’t combine them. The trees can: +0.227 AUC (95% CI +0.215 to +0.241).");
card(s, M, 4.9, 6.0, 1.4, "Log loss beats L2, or ties", "+0.057 for the glassbox. For the blackbox +0.002, with an interval that includes zero: a tie, so we keep log loss for its probabilities.");
img(s, "s2_auc.png", "Validation AUC with 95% intervals: glassbox L2 0.597, glassbox log loss 0.654, blackbox L2 0.879, blackbox log loss 0.881.", 7.0, 1.6, 5.7, 2.85);
text(s, [{ text: "Same setup as the first run: ", options: { bold: true, color: C.text1 } }, { text: "60 / 20 / 20 split, each model tuned separately by cross-validation inside the training split, 24 configurations. The split is random here, because this dataset has no lot information." }], { x: 7.0, y: 4.7, w: 5.7, h: 1.5 });

// 3. Decision and threshold
s = add("LIGHT", "Models and decision", "decision", "This time the blackbox wins, at threshold 0.175",
  "Validation split. Minimising plain misclassification would leave the threshold at 0.49. The choice holds for every cost ratio from 1 to 10.");
card(s, M, 1.6, 6.0, 1.5, "Same rule, opposite answer", "The blackbox must cut the cost by 10% to earn its opacity. Here it cuts it by 36%: 0.328 per wafer against 0.512.");
card(s, M, 3.25, 6.0, 1.1, "The glassbox adds nothing", "Its best cost, 0.512, is the cost of holding the tool for every wafer (0.513).");
stat(s, M, 4.55, 2.9, 1.7, "−45%", "cost vs a 0.5 threshold (0.595 → 0.328)", { num: C.accent3 });
stat(s, 3.7, 4.55, 2.9, 1.7, "−8.2 pts", "accuracy (79.1% → 70.9%)");
img(s, "s3_threshold.png", "Cost per wafer against the decision threshold for the blackbox. Our evaluation loss is lowest at 0.175. The misclassification rate is lowest near 0.49.", 7.0, 1.6, 5.7, 3.29);
text(s, "At 0.175 we miss 68 scratched wafers instead of 714, for 2,088 false alarms instead of 835.", { x: 7.0, y: 5.1, w: 5.7, h: 0.9 });

// 4. Calibration
pres.addSection({ title: "Calibration and interpretability" });
s = add("LIGHT", "Calibration and interpretability", "calibration", "Calibration: already good, and the threshold shows it",
  "Validation split, equal-count bins. For cost ratios 1 to 4 the searched threshold is within 0.02 of the formula.");
img(s, "s4_calibration.png", "Reliability diagram for the blackbox. All three curves, L2 loss, log loss raw and log loss after Platt scaling, lie close to the diagonal.", M, 1.6, 6.6, 4.11);
stat(s, 7.5, 1.6, 5.23, 1.2, "0.013 → 0.009", "calibration error (ECE) of the chosen model; AUC unchanged", { size: 28 });
card(s, 7.5, 2.95, 5.23, 0.95, "What we found", "Boosted trees trained with log loss on 22,195 wafers were close to calibrated from the start.");
card(s, 7.5, 4.02, 5.23, 1.2, "The fix", "Platt scaling, fitted on out-of-fold training scores. A small gain. In the first run isotonic regression was the better fix.");
card(s, 7.5, 5.34, 5.23, 1.3, "Why it matters", "Theory gives the threshold: 1/(1+5) = 0.167. Ours is 0.155. In the first run, with worse calibration, it was 0.22.");

// 5. SHAP
s = add("LIGHT", "Calibration and interpretability", "shap", "Tree SHAP: the model does not look at the scratch",
  "Likely cause: the model has learned which mixes of patterns come with the Scratch label in this dataset. Orange pushes towards scratch, blue away.");
text(s, "Global: what the model relies on", { x: M, y: 1.5, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
img(s, "s5_shap_global.png", "Mean absolute SHAP value per feature. edge_fail_rate is first at 1.2, then outer_ring_fail_rate at 1.0, n_fail_clusters at 0.7 and largest_cluster_radius at 0.7.", M, 1.95, 5.3, 3.9);
text(s, "Edge fail rates lead. No feature describes a line.", { x: M, y: 5.95, w: 5.3, h: 0.6 });
text(s, "Local: two wafers, next to their maps", { x: 6.5, y: 1.5, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
text(s, [{ text: "Most confident scratch. ", options: { bold: true, color: C.text1 } }, { text: "P = 1.000. Label: Donut + Edge-Ring + Loc + Scratch. No line is visible; the edge fail rates decide." }], { x: 6.5, y: 1.95, w: 6.2, h: 0.55 });
img(s, "s5_shap_local_correct.png", "Wafer map with a donut and an edge ring and no visible line, beside its SHAP values. outer_ring_fail_rate and edge_fail_rate push towards scratch.", 6.5, 2.55, 5.5, 1.65);
text(s, [{ text: "Costliest mistake. ", options: { bold: true, color: C.text1 } }, { text: "Label: Edge-Loc + Scratch, P = 0.013. A cluster at the very edge pushes it to “no scratch”." }], { x: 6.5, y: 4.3, w: 6.2, h: 0.55 });
img(s, "s5_shap_local_mistake.png", "Wafer map with scattered failures, beside its SHAP values. largest_cluster_radius = 0.94 pushes strongly towards no scratch.", 6.5, 4.9, 5.5, 1.65);

// 6. Result and comparison
pres.addSection({ title: "Result and comparison" });
s = add("DARK", "Result and comparison", "result", "Two runs, one pipeline, opposite decisions",
  "AUC and loss rows are validation, log-loss models, at each model’s best threshold. Test splits used once. Loss levels are not comparable across runs.");
const dc = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: C.background1, valign: "middle", fill: { color: C.accent4 } }, o) });
const hd = (t) => dc(t, { bold: true, fill: { color: "2A3B63" } });
s.addTable([
  [hd(""), hd("Run 1: Edge-Loc"), hd("Run 2: Scratch")],
  [dc("Data"), dc("Real fab maps, 8,782"), dc("Real + GAN maps, 36,991")],
  [dc("AUC, glassbox / blackbox"), dc("0.966 / 0.972"), dc("0.654 / 0.881")],
  [dc("Loss, glassbox / blackbox"), dc("0.143 / 0.149"), dc("0.512 / 0.328")],
  [dc("Model chosen", { bold: true }), dc("Glassbox", { bold: true }), dc("Blackbox", { bold: true })],
  [dc("Threshold; saving vs 0.5"), dc("0.28; −27%"), dc("0.175; −45%")],
  [dc("Calibration error"), dc("0.031 → 0.021"), dc("0.013 → 0.009")],
  [dc("Test AUC"), dc("0.958"), dc("0.882")],
  [dc("Test loss (hold every wafer)"), dc("0.181 (0.409)"), dc("0.330 (0.513)")],
  [dc("SHAP matches the physics?"), dc("Yes"), dc("No")],
], { x: M, y: 1.6, w: 7.5, colW: [2.9, 2.2, 2.4], rowH: 0.44, border: { type: "solid", pt: 0.75, color: "14213D" }, objectName: "Comparison table" });
const dark = { fill: C.accent4, num: C.background1, label: C.accent5, size: 28 };
stat(s, 8.35, 1.6, 2.1, 1.5, "0.882", "run 2 test AUC (CI 0.874 to 0.889)", dark);
stat(s, 10.63, 1.6, 2.1, 1.5, "−36%", "run 2 test cost vs holding every wafer", Object.assign({}, dark, { num: C.accent6 }));
card(s, 8.35, 3.3, 4.38, 1.55, "What the comparison shows", "The same rule picks the glassbox when a linear model captures the signal, and the blackbox when it can’t. Log loss never loses to L2.", { fill: C.accent4, head: C.background1, body: C.accent5 });
card(s, 8.35, 5.0, 4.38, 1.55, "Which to trust", "Run 1. Run 2 has the bigger gap, but its model reads how the dataset was built, and its 49% scratch rate is artificial.", { fill: C.accent4, head: C.background1, body: C.accent5 });

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
