// Builds slides/Project2_Scratch_Detection.pptx: the six slides of project B (MixedWM38, scratch detection).
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
  "DBA5106 Project 2, Version 2 (with data). Orange = failing die, light blue = passing die. Source: MixedWM38 (Kaggle, co1d7era/mixedtype-wafer-defect-datasets).");
text(s, "A scratch is a thin line of failing dies from mechanical contact. It has to be found among other defects.", { x: M, y: 1.6, w: 5.9, h: 0.8, fontSize: 16, color: C.text1 });
card(s, M, 2.5, 5.9, 1.1, "Scratch: hold the handler, screen the wafer", "The handler will scratch the next wafers too, and dies beside a scratch can fail later in the field.");
card(s, M, 3.75, 5.9, 1.0, "No scratch: normal review", "The wafer may carry other patterns, but not this one.");
img(s, "s1_wafers.png", "Two wafer maps. Left, a wafer labelled with a scratch alone. Right, a wafer labelled Center, Edge-Loc and Scratch, with a large cluster in the centre and a thin line below it.", 6.9, 1.6, 5.8, 3.04);
card(s, M, 4.95, 3.9, 1.75, "Data", "MixedWM38 (Kaggle usability 7.5): 36,991 wafer maps, each labelled with every pattern it has. 49% have a scratch, a rate the authors balanced.");
card(s, 4.72, 4.95, 3.9, 1.75, "Evaluation loss", "(10 × missed scratch + 1 × false alarm) / wafers. A miss repeats and carries a reliability risk. The 10:1 ratio is our assumption.");
card(s, 8.83, 4.95, 3.9, 1.75, "Cleaning, before any model", "Dropped 1,024 duplicate maps (97.7% scratched). Withheld the die count: no physical link to a scratch, yet it could rule scratches out.");

// 2. Features and models
pres.addSection({ title: "Models and decision" });
s = add("LIGHT", "Models and decision", "models", "Features built for a line, then four models",
  "Solid = log loss, dashed = L2. Intervals resample wafers, 2,000 times. Validation: 7,398 wafers. Training AUC of the blackbox: 0.989.");
card(s, M, 1.6, 6.0, 1.55, "16 features: 9 background, 7 line", "Line features measure thin structures and failing dies that line up in one direction. Alone, they are the seven strongest features (AUC 0.63–0.73). None says where the line is.");
const cell = (t, o = {}) => ({ text: t, options: Object.assign({ fontSize: 14, color: C.text1, valign: "middle" }, o) });
s.addTable([
  [cell("Validation AUC", { bold: true, fill: { color: C.background2 } }), cell("L2 loss", { bold: true, align: "right", fill: { color: C.background2 } }), cell("Log loss", { bold: true, align: "right", fill: { color: C.background2 } })],
  [cell("Glassbox: L1 linear model"), cell("0.885", { align: "right" }), cell("0.909", { align: "right", bold: true })],
  [cell("Blackbox: boosted trees"), cell("0.958", { align: "right" }), cell("0.963", { align: "right", bold: true })],
], { x: M, y: 3.3, w: 6.0, colW: [3.2, 1.4, 1.4], rowH: 0.48, border: { type: "solid", pt: 0.75, color: "E1E0D9" }, objectName: "AUC table" });
card(s, M, 4.95, 6.0, 1.35, "Log loss beats L2 for both", "+0.024 for the glassbox, +0.005 for the blackbox; both intervals exclude zero. L2 scores fall outside 0–1 for 10–24% of wafers.");
img(s, "s2_auc.png", "Validation AUC with 95% intervals: glassbox L2 0.885, glassbox log loss 0.909, blackbox L2 0.958, blackbox log loss 0.963.", 7.0, 1.6, 5.7, 2.85);
text(s, [{ text: "How we kept it fair: ", options: { bold: true, color: C.text1 } }, { text: "60 / 20 / 20 stratified split. Each model tuned separately by cross-validation inside the training split, 32 configurations in total. Validation only compares the four tuned models." }], { x: 7.0, y: 4.7, w: 5.7, h: 1.5 });

// 3. Decision and threshold
s = add("LIGHT", "Models and decision", "decision", "We chose the blackbox, at threshold 0.117",
  "Validation split. Minimising plain misclassification would leave the threshold at 0.48. The model choice holds for every cost ratio from 1 to 20.");
card(s, M, 1.6, 6.0, 1.4, "The blackbox earns its opacity", "AUC is 0.054 higher (95% CI +0.049 to +0.060), and the evaluation loss is 38% lower: 0.250 per wafer against 0.406.");
card(s, M, 3.15, 6.0, 1.25, "Rule set before looking", "An engineer acts on a flag, so a readable model has value. The blackbox had to cut the cost by 10% to be chosen.");
stat(s, M, 4.55, 2.9, 1.7, "−59%", "cost vs a 0.5 threshold (0.613 → 0.250)", { num: C.accent3 });
stat(s, 3.7, 4.55, 2.9, 1.7, "−7.9 pts", "accuracy (89.1% → 81.2%)");
img(s, "s3_threshold.png", "Cost per wafer against the decision threshold for the blackbox. Our evaluation loss is lowest at 0.117. The misclassification rate is lowest near 0.48.", 7.0, 1.6, 5.7, 3.29);
text(s, "At 0.117 we miss 51 scratched wafers instead of 414, for 1,339 false alarms instead of 395.", { x: 7.0, y: 5.1, w: 5.7, h: 0.9 });

// 4. Calibration
pres.addSection({ title: "Calibration and interpretability" });
s = add("LIGHT", "Calibration and interpretability", "calibration", "Calibration: close already, slightly better after",
  "Validation split, equal-count bins. For cost ratios from 1 to 20 the searched threshold stays within 0.03 of the formula.");
img(s, "s4_calibration.png", "Reliability diagram for the blackbox. The log-loss model, raw and after Platt scaling, lies on the diagonal. The L2 version bends away from it.", M, 1.6, 6.6, 4.11);
stat(s, 7.5, 1.6, 5.23, 1.2, "0.011 → 0.009", "calibration error (ECE) of the chosen model; AUC unchanged", { size: 28 });
card(s, 7.5, 2.95, 5.23, 1.25, "How we checked", "Reliability diagram, ECE and Brier score for all four models. The L2 versions are the worst: 0.077 (glassbox) and 0.035 (blackbox).");
card(s, 7.5, 4.3, 5.23, 0.95, "The fix", "Platt scaling, fitted on out-of-fold training scores so the validation split stays clean.");
card(s, 7.5, 5.35, 5.23, 1.3, "Why it matters", "Theory gives the threshold for calibrated probabilities: 1/(1+10) = 0.091. Ours is 0.105, at almost the same cost (0.250 vs 0.260).");

// 5. SHAP
s = add("LIGHT", "Calibration and interpretability", "shap", "Tree SHAP: does the model look at the scratch?",
  "Caution: the top feature is background. Part of that is real context; part may be which patterns come with a Scratch label in this dataset.");
text(s, "Global: about half line, half background", { x: M, y: 1.5, w: 5.3, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
img(s, "s5_shap_global.png", "Mean absolute SHAP value per feature. outer_ring_fail_rate, a background feature, is first at 1.9. Then three line features: thin_fail_rate 1.4, line_score_top20 1.2 and n_line_segments 0.7.", M, 1.95, 5.0, 4.08);
text(s, "Line features carry 49% of the attribution.", { x: M, y: 6.1, w: 5.3, h: 0.5 });
text(s, "Local: two wafers, next to their maps", { x: 6.5, y: 1.5, w: 6.2, h: 0.4, fontSize: 16, bold: true, color: C.text1 });
text(s, [{ text: "Most confident scratch. ", options: { bold: true, color: C.text1 } }, { text: "P = 1.000. A scratch-only wafer with a visible diagonal line. Three of its top four drivers are line features." }], { x: 6.5, y: 1.95, w: 6.2, h: 0.55 });
img(s, "s5_shap_local_correct.png", "Wafer map with a visible diagonal line of failing dies, beside its four largest SHAP values, all pushing towards scratch.", 6.5, 2.55, 5.5, 1.65);
text(s, [{ text: "Costliest mistake. ", options: { bold: true, color: C.text1 } }, { text: "Label: Donut + Edge-Loc + Loc + Scratch, P = 0.003. Large blobs hide the thin line." }], { x: 6.5, y: 4.3, w: 6.2, h: 0.55 });
img(s, "s5_shap_local_mistake.png", "Wafer map mostly covered by a donut and edge defects, beside its SHAP values. A low thin_fail_rate pushes strongly towards no scratch.", 6.5, 4.9, 5.5, 1.65);

// 6. Result
pres.addSection({ title: "Result" });
s = add("DARK", "Result", "result", "Test result, used once, and what to flag",
  "Final model: boosted trees (log loss) + Platt scaling, threshold 0.105. Test split: 7,398 wafers. An earlier version with other features was scored on this split once.");
const dark = { fill: C.accent4, num: C.background1, label: C.accent5 };
stat(s, 0.6, 1.6, 2.9, 1.6, "0.961", "AUC (95% CI 0.957 to 0.964)", dark);
stat(s, 3.68, 1.6, 2.9, 1.6, "0.263", "evaluation loss per wafer (CI 0.242 to 0.286)", dark);
stat(s, 6.76, 1.6, 2.9, 1.6, "98.4%", "of scratched wafers caught; precision 72.3%", dark);
stat(s, 9.84, 1.6, 2.9, 1.6, "−49%", "cost vs flagging every wafer (0.513)", Object.assign({}, dark, { num: C.accent6 }));
const col = (x, head, body) => {
  text(s, head, { x, y: 3.6, w: 3.9, h: 0.45, fontSize: 18, bold: true, color: C.background1 });
  text(s, body, { x, y: 4.15, w: 3.9, h: 2.4, color: C.accent5, paraSpaceAfter: 6 });
};
const bullets = (items) => items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1 } }));
col(0.6, "Audit of our own choice", "On test, the glassbox we didn’t choose scores 0.426 against our 0.263. The difference (+0.162, 95% CI +0.134 to +0.191) confirms the choice. Validation and test agree: 0.250 vs 0.263.");
col(4.72, "Limits", bullets(["The 49% scratch rate is artificial, so the cost is not a fab forecast.", "The 10:1 cost ratio is our assumption.", "Half of the model’s attribution is background.", "No lots in the data, so the split is random."]));
col(8.83, "What we did differently", bullets(["Built line features for the question.", "Left out position and the die count on purpose.", "32 configurations; test used once; an interval on every comparison."]));

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
