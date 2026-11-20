"""DBA5106 Project 2: classification and review policy for flagged steel faults."""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.metrics import brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
SEED = 5106
COST_FN = 5
LABELS = ['Pastry', 'Z_Scratch', 'K_Scatch', 'Stains', 'Dirtiness', 'Bumps', 'Other_Faults']
SCRATCH_LABELS = ['Z_Scratch', 'K_Scatch']
EXCLUDED = [
    'X_Minimum', 'X_Maximum', 'Y_Minimum', 'Y_Maximum', 'Length_of_Conveyer',
    'TypeOfSteel_A400', 'LogOfAreas', 'Log_X_Index', 'Log_Y_Index',
]
CANDIDATE_ORDER = ['Linear / L2', 'Linear / Log loss', 'Boosted trees / L2', 'Boosted trees / Log loss']
DISPLAY = {
    'Pixels_Areas': 'Defect area', 'X_Perimeter': 'X perimeter', 'Y_Perimeter': 'Y perimeter',
    'Minimum_of_Luminosity': 'Minimum brightness', 'Maximum_of_Luminosity': 'Maximum brightness',
    'Mean_Luminosity': 'Mean brightness', 'TypeOfSteel_A300': 'Steel grade A300',
    'Steel_Plate_Thickness': 'Plate thickness', 'Edges_Index': 'Edges index',
    'Empty_Index': 'Empty index', 'Square_Index': 'Square index', 'Outside_X_Index': 'Outside X index',
    'Edges_X_Index': 'Edges X index', 'Edges_Y_Index': 'Edges Y index',
    'Outside_Global_Index': 'Outside global index', 'Orientation_Index': 'Orientation index',
    'Luminosity_Index': 'Luminosity index', 'SigmoidOfAreas': 'Sigmoid of area',
    'Width_px': 'Defect width', 'Height_px': 'Defect height',
}
NAVY, BLUE, TEAL, RED, MUTED, LIGHT = '#16263C', '#2664B0', '#077779', '#BA4F2B', '#53647A', '#DDE6EF'


def load_data(path: Path):
    raw = pd.read_csv(path)
    label_frame = raw[LABELS]
    if not label_frame.isin([0, 1]).all().all() or not label_frame.sum(axis=1).eq(1).all():
        raise ValueError('Expected seven one-hot fault labels, with exactly one active label per row.')
    subtype = label_frame.idxmax(axis=1)
    y = label_frame[SCRATCH_LABELS].sum(axis=1).astype(int).rename('scratch')
    x = raw.drop(columns=LABELS + EXCLUDED + ['Sum_of_Luminosity']).assign(
        Width_px=raw['X_Maximum'] - raw['X_Minimum'],
        Height_px=raw['Y_Maximum'] - raw['Y_Minimum'],
        Mean_Luminosity=raw['Sum_of_Luminosity'] / raw['Pixels_Areas'],
    )
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError('Non-finite feature values require inspection before modeling.')
    duplicates = int(x.duplicated().sum())
    if duplicates:
        raise ValueError('Group duplicate feature vectors before splitting to avoid crossing splits.')
    audit = {
        'rows': len(raw), 'input_features': raw.shape[1] - len(LABELS),
        'features': x.shape[1], 'positive': int(y.sum()), 'negative': int(y.eq(0).sum()),
        'missing_cells': int(raw.isna().sum().sum()), 'duplicate_rows': int(raw.duplicated().sum()),
        'duplicate_feature_rows': duplicates, 'subtypes': subtype.value_counts().to_dict(),
    }
    return x, y, subtype, audit


def make_splits(y):
    development, test = train_test_split(y.index, test_size=0.20, stratify=y, random_state=SEED)
    train, validation = train_test_split(
        development, test_size=0.25, stratify=y.loc[development], random_state=SEED + 1,
    )
    return {'train': train, 'validation': validation, 'test': test}


def candidate_models():
    tree_grid = {'max_depth': [2, 3], 'n_estimators': [80, 160, 240], 'min_samples_leaf': [5, 15]}
    return {
        'Linear / L2': (make_pipeline(StandardScaler(), Lasso(max_iter=30000)),
                        {'lasso__alpha': [0.0003, 0.001, 0.003, 0.01, 0.03, 0.06]}),
        'Linear / Log loss': (make_pipeline(StandardScaler(), LogisticRegression(
            l1_ratio=1, solver='liblinear', max_iter=5000, random_state=SEED)),
            {'logisticregression__C': [0.03, 0.1, 0.3, 1, 3, 10]}),
        'Boosted trees / L2': (GradientBoostingRegressor(
            loss='squared_error', learning_rate=0.05, random_state=SEED), tree_grid),
        'Boosted trees / Log loss': (GradientBoostingClassifier(
            loss='log_loss', learning_rate=0.05, random_state=SEED), tree_grid),
    }


def cv_auc(estimator, x, y):
    return roc_auc_score(y, raw_score(estimator, x))


def raw_score(estimator, x):
    if hasattr(estimator, 'decision_function'):
        return estimator.decision_function(x)
    return estimator.predict(x)


def probability_view(estimator, score):
    if hasattr(estimator, 'decision_function'):
        return expit(score)
    return np.clip(score, 0, 1)


def expected_calibration_error(y, p):
    bins = np.searchsorted(np.linspace(0, 1, 11)[1:-1], p, side='right')
    y = np.asarray(y)
    total_error = 0.0
    for group in np.unique(bins):
        rows = bins == group
        total_error += rows.mean() * abs(y[rows].mean() - p[rows].mean())
    return float(total_error)


def calibration_metrics(y, p):
    return {'brier': float(brier_score_loss(y, p)), 'ece': expected_calibration_error(y, p)}


def fit_candidates(x_train, y_train, x_validation, y_validation):
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    fitted, rows = {}, []
    for name, (estimator, grid) in candidate_models().items():
        search = GridSearchCV(estimator, grid, scoring=cv_auc, cv=cv, error_score='raise', n_jobs=1)
        search.fit(x_train, y_train)
        model = search.best_estimator_
        train_score, validation_score = raw_score(model, x_train), raw_score(model, x_validation)
        method = 'decision_function' if hasattr(model, 'decision_function') else 'predict'
        oof_score = cross_val_predict(model, x_train, y_train, cv=cv, method=method, n_jobs=1)
        platt = LogisticRegression(C=1000, solver='lbfgs').fit(oof_score.reshape(-1, 1), y_train)
        p_raw = probability_view(model, validation_score)
        p_platt = platt.predict_proba(validation_score.reshape(-1, 1))[:, 1]
        raw_metrics = calibration_metrics(y_validation, p_raw)
        platt_metrics = calibration_metrics(y_validation, p_platt)
        row = {
            'model': name, 'parameters': search.best_params_, 'cv_auc': float(search.best_score_),
            'train_auc': float(roc_auc_score(y_train, train_score)),
            'validation_auc': float(roc_auc_score(y_validation, validation_score)),
            'raw_brier': raw_metrics['brier'], 'platt_brier': platt_metrics['brier'],
            'raw_ece': raw_metrics['ece'], 'platt_ece': platt_metrics['ece'],
            'platt_slope': float(platt.coef_[0, 0]), 'platt_intercept': float(platt.intercept_[0]),
            'outside_unit_interval': int(((validation_score < 0) | (validation_score > 1)).sum())
            if method == 'predict' else 0,
        }
        rows.append(row)
        fitted[name] = {'model': model, 'platt': platt, 'raw': p_raw, 'calibrated': p_platt,
                        'scores': validation_score, 'cv_results': pd.DataFrame(search.cv_results_)}
    comparison = pd.DataFrame(rows).sort_values('validation_auc', ascending=False, kind='stable')
    return fitted, comparison


def threshold_curve(y, p, cost_fn=COST_FN):
    # All distinct decisions, including review all and review none.
    order = np.argsort(-p, kind='stable')
    sorted_y, sorted_p = np.asarray(y)[order], p[order]
    ends = np.flatnonzero(np.r_[sorted_p[1:] != sorted_p[:-1], True])
    tp = np.r_[0, np.cumsum(sorted_y)[ends]]
    alert_count = np.r_[0, ends + 1]
    fp, fn = alert_count - tp, sorted_y.sum() - tp
    return pd.DataFrame({
        'threshold': np.r_[np.nextafter(sorted_p[0], np.inf), sorted_p[ends]],
        'reviewed': alert_count, 'weighted_loss': (cost_fn * fn + fp) / len(sorted_y),
    })


def select_threshold(y, p, cost_fn=COST_FN):
    curve = threshold_curve(y, p, cost_fn)
    # Prefer fewer reviews when tied. Represent the chosen validation decision by the
    # midpoint between adjacent score boundaries so a single case does not set the cut.
    best = int(curve['weighted_loss'].idxmin())
    upper = float(curve.loc[best, 'threshold'])
    if best == 0 or best + 1 == len(curve):
        return upper
    lower = float(curve.loc[best + 1, 'threshold'])
    return (lower + upper) / 2


def decision_metrics(y, p, threshold, cost_fn=COST_FN):
    predicted = p >= threshold
    tn, fp, fn, tp = (int(v) for v in confusion_matrix(y, predicted, labels=[0, 1]).ravel())
    return {
        'threshold': float(threshold), 'tn': tn, 'fp': fp, 'fn': fn, 'tp': tp,
        'reviewed': tp + fp, 'weighted_loss': (cost_fn * fn + fp) / len(y),
        'weighted_errors': cost_fn * fn + fp, 'review_rate': (tp + fp) / len(y),
        'recall': tp / (tp + fn) if tp + fn else 0.0,
        'precision': tp / (tp + fp) if tp + fp else 0.0,
        'accuracy': (tp + tn) / len(y),
    }


def policy_rows(y, p, threshold):
    return pd.DataFrame({
        'Review none': decision_metrics(y, p, np.nextafter(1.0, np.inf)),
        'Review all': decision_metrics(y, p, 0.0),
        'Default 0.50': decision_metrics(y, p, 0.5),
        'Tuned rule': decision_metrics(y, p, threshold),
    }).T


def bootstrap_test(y, scores, p, threshold, reps=1200):
    rng = np.random.default_rng(SEED + 2)
    y = np.asarray(y)
    decision = p >= threshold
    default = p >= 0.5
    cost = np.where(y == 1, COST_FN * (~decision), decision.astype(int))
    cost_default = np.where(y == 1, COST_FN * (~default), default.astype(int))
    metrics = []
    for sample in rng.integers(0, len(y), size=(reps, len(y))):
        if np.unique(y[sample]).size == 2:
            metrics.append((roc_auc_score(y[sample], scores[sample]), cost[sample].mean(),
                            (cost_default[sample] - cost[sample]).mean()))
    bounds = np.quantile(metrics, [0.025, 0.975], axis=0).T
    return {key: list(values) for key, values in zip(['auc', 'cost', 'saving_vs_default'], bounds)}


def exact_tree_shap(model, x):
    """Exact tree-path-dependent Shapley values for this shallow sklearn ensemble.

    Exhaustively enumerate coalitions of each tree's split features. Unknown splits
    average child expectations using the fractions of weighted training samples that
    went to each child. Features absent from a tree have zero contribution, so the
    dummy axiom and Shapley linearity let us sum the smaller per-tree games exactly.
    The output is the model's raw margin for log loss and its raw score for L2.
    """
    data = x.to_numpy(dtype=np.float32)
    phi = np.zeros(data.shape, dtype=float)
    if hasattr(model, 'decision_function'):
        prediction = model.decision_function(x)
    else:
        prediction = model.predict(x)
    base = float(prediction[0])
    for fitted_tree in model.estimators_.ravel():
        tree = fitted_tree.tree_
        base -= model.learning_rate * fitted_tree.predict(data[:1])[0]
        split_features = np.unique(tree.feature[tree.feature >= 0])
        k = len(split_features)
        if k > 7:
            raise ValueError('Exhaustive TreeSHAP is configured for depth at most three.')
        bits = {int(feature): 1 << index for index, feature in enumerate(split_features)}
        masks = np.arange(1 << k)
        cover, leaves = tree.weighted_n_node_samples, tree.value[:, 0, 0]

        def expectation(node):
            left, right = tree.children_left[node], tree.children_right[node]
            if left == right:
                return np.full((len(masks), len(data)), leaves[node])
            left_value, right_value = expectation(left), expectation(right)
            fraction = cover[left] / cover[node]
            unknown = fraction * left_value + (1 - fraction) * right_value
            feature = int(tree.feature[node])
            known = np.where(data[:, feature] <= tree.threshold[node], left_value, right_value)
            return np.where((masks & bits[feature])[:, None] != 0, known, unknown)

        values = expectation(0)
        base += model.learning_rate * values[0, 0]
        for feature, bit in bits.items():
            without = masks[masks & bit == 0]
            weights = np.array([1 / (k * comb(k - 1, int(mask).bit_count())) for mask in without])
            phi[:, feature] += model.learning_rate * (weights @ (values[without | bit] - values[without]))
    if not np.allclose(base + phi.sum(axis=1), prediction, rtol=1e-7, atol=1e-7):
        raise AssertionError('The TreeSHAP contributions do not reconstruct the raw model outputs.')
    return pd.DataFrame(phi, index=x.index, columns=x.columns), base


def feature_screen(x_train, y_train):
    auc = x_train.apply(lambda values: roc_auc_score(y_train, values))
    oriented_auc = auc.where(auc >= 0.5, 1 - auc)
    return oriented_auc.rename('one_feature_auc').sort_values(ascending=False)


def style_charts():
    font_names = {font.name for font in font_manager.fontManager.ttflist}
    plt.rcParams.update({
        'font.family': 'Inter' if 'Inter' in font_names else 'DejaVu Sans', 'font.size': 12,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': LIGHT,
        'axes.labelcolor': NAVY, 'xtick.color': MUTED, 'ytick.color': NAVY,
        'text.color': NAVY, 'axes.titlecolor': NAVY, 'figure.facecolor': 'white',
        'axes.facecolor': 'white', 'savefig.facecolor': 'white',
    })


def save_chart(fig, folder, name):
    fig.savefig(folder / name, dpi=180, bbox_inches='tight', pad_inches=0.09)
    plt.close(fig)


def decision_chart(y, p, threshold, policy_name, folder):
    thresholds = np.linspace(0, 1, 501)
    losses = np.array([decision_metrics(y, p, t)['weighted_loss'] for t in thresholds])
    exact = threshold_curve(y, p)
    exact.to_csv(folder.parent / 'validation_threshold_curve.csv', index=False)
    default = decision_metrics(y, p, 0.5)['weighted_loss']
    tuned = decision_metrics(y, p, threshold)['weighted_loss']
    fig, ax = plt.subplots(figsize=(7.3, 3.5), layout='constrained')
    ax.plot(thresholds, losses, lw=2.4, color=BLUE)
    ax.scatter([threshold, 0.5], [tuned, default], s=65, color=[TEAL, RED], zorder=3)
    ax.axvline(threshold, lw=1.1, color=TEAL, ls=':')
    ax.axvline(0.5, lw=1.1, color=RED, ls=':')
    ax.set(xlim=(0, 1), ylim=(0, None), xlabel=f'{policy_name} probability threshold',
           ylabel='Weighted loss per record')
    ax.grid(axis='y', alpha=0.55, color=LIGHT)
    save_chart(fig, folder, 'threshold.png')


def reliability_chart(y, p_raw, p_platt, folder):
    fig, ax = plt.subplots(figsize=(6.2, 4.5), layout='constrained')
    ax.plot([0, 1], [0, 1], ls='--', color=MUTED, lw=1.25, label='Perfect calibration')
    for data, color, label, marker in [(p_raw, BLUE, 'Raw', 'o'), (p_platt, TEAL, 'Platt', 's')]:
        observed, predicted = calibration_curve(y, data, n_bins=8, strategy='quantile')
        ax.plot(predicted, observed, color=color, label=label, marker=marker, lw=2, ms=5)
    ax.set(xlim=(-0.02, 1.02), ylim=(-0.02, 1.02), xlabel='Mean predicted scratch probability',
           ylabel='Observed scratch fraction', aspect='equal')
    ax.legend(loc='upper left', frameon=False, fontsize=10)
    ax.grid(alpha=0.35, color=LIGHT)
    save_chart(fig, folder, 'calibration.png')


def shap_charts(phi, local_values, folder):
    top = phi.abs().mean().nlargest(6).sort_values()
    fig, ax = plt.subplots(figsize=(6.0, 3.35), layout='constrained')
    ax.barh([DISPLAY[name] for name in top.index], top, color=BLUE, height=0.62)
    ax.set_xlabel('Mean absolute TreeSHAP value')
    ax.grid(axis='x', zorder=0, alpha=0.45, color=LIGHT)
    ax.set_axisbelow(True)
    save_chart(fig, folder, 'shap_global.png')

    magnitudes = local_values.abs().nlargest(5)
    top_local = local_values.loc[magnitudes.index]
    other = local_values.drop(top_local.index).sum()
    top_local = pd.concat([top_local, pd.Series({'All other features': other})]).iloc[::-1]
    fig, ax = plt.subplots(figsize=(6.0, 3.35), layout='constrained')
    ax.barh([DISPLAY.get(name, name) for name in top_local.index], top_local,
            color=[TEAL if value > 0 else RED for value in top_local], height=0.62)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel('Signed contribution to raw model score')
    ax.grid(axis='x', zorder=0, alpha=0.45, color=LIGHT)
    ax.set_axisbelow(True)
    save_chart(fig, folder, 'shap_local.png')


def analyze(data_path=ROOT / 'data' / 'faults.csv', output=ROOT / 'results', verbose=True):
    output = Path(output)
    charts = output / 'figures'
    charts.mkdir(parents=True, exist_ok=True)
    style_charts()
    x, y, subtype, audit = load_data(Path(data_path))
    splits = make_splits(y)
    train, validation, test = (splits[key] for key in ('train', 'validation', 'test'))
    split_counts = {key: {'rows': len(indices), 'positive': int(y.loc[indices].sum())}
                    for key, indices in splits.items()}
    if verbose:
        print(f'Loaded {len(x)} records and {x.shape[1]} features. Tuning the four models…', flush=True)
    screen = feature_screen(x.loc[train], y.loc[train])
    screen.to_csv(output / 'training_single_feature_auc.csv', header=True)
    fitted, comparison = fit_candidates(x.loc[train], y.loc[train], x.loc[validation], y.loc[validation])
    comparison.to_csv(output / 'validation_models.csv', index=False)
    for i, name in enumerate(CANDIDATE_ORDER, start=1):
        grid = fitted[name]['cv_results']
        grid[['params', 'mean_test_score', 'std_test_score', 'rank_test_score']].to_csv(
            output / f'cv_model_{i}.csv', index=False,
        )
    selected = comparison.iloc[0].to_dict()
    name = selected['model']
    entry = fitted[name]
    calibrated = selected['platt_brier'] < selected['raw_brier'] and selected['platt_slope'] > 0
    p_validation = entry['calibrated' if calibrated else 'raw']
    threshold = select_threshold(y.loc[validation], p_validation)
    validation_policies = policy_rows(y.loc[validation], p_validation, threshold)
    sensitivity = pd.DataFrame([
        dict(cost_fn=weight, **decision_metrics(y.loc[validation], p_validation,
             select_threshold(y.loc[validation], p_validation, weight), weight)) for weight in (2, 5, 10)
    ])
    sensitivity.to_csv(output / 'validation_cost_sensitivity.csv', index=False)
    validation_policies.to_csv(output / 'validation_decisions.csv')
    if verbose:
        print(comparison[['model', 'cv_auc', 'validation_auc', 'raw_brier', 'platt_brier']].to_string(index=False), flush=True)
        print(f'Selected {name}. Locked {"Platt" if calibrated else "raw"} policy at {threshold:.6f}.', flush=True)

    # Explain the highest-validation-AUC black box on validation. Prefer the costliest
    # error type and pick the highest score among those to illustrate a borderline miss.
    shap_name = next(model_name for model_name in comparison['model'] if model_name.startswith('Boosted'))
    shap_entry = fitted[shap_name]
    # Check whether plate thickness and grade materially affect discrimination.
    # Keep the chosen tree configuration and use only training and validation.
    shape_only = x.drop(columns=['Steel_Plate_Thickness', 'TypeOfSteel_A300'])
    ablated = clone(shap_entry['model']).fit(shape_only.loc[train], y.loc[train])
    no_plate_auc = cv_auc(ablated, shape_only.loc[validation], y.loc[validation])
    phi, base = exact_tree_shap(shap_entry['model'], x.loc[validation])
    phi.to_csv(output / 'validation_tree_shap.csv', index_label='row_id')
    shap_p = p_validation if name == shap_name else shap_entry['raw']
    shap_threshold = threshold if name == shap_name else select_threshold(y.loc[validation], shap_p)
    y_val = y.loc[validation].to_numpy()
    misses = np.flatnonzero((y_val == 1) & (shap_p < shap_threshold))
    mistakes = np.flatnonzero((y_val == 0) & (shap_p >= shap_threshold))
    if len(misses):
        local_index = misses[np.argmax(shap_p[misses])]
    elif len(mistakes):
        local_index = mistakes[np.argmin(shap_p[mistakes])]
    else:
        local_index = int(np.argmin(np.abs(shap_p - shap_threshold)))
    row_id = int(validation[local_index])
    local_phi = phi.loc[row_id]
    local_details = pd.DataFrame({'value': x.loc[row_id], 'shap': local_phi})
    local_details.to_csv(output / 'local_tree_shap.csv', index_label='feature')
    shap_result = {
        'model': shap_name, 'base': base, 'global': phi.abs().mean().sort_values(ascending=False).to_dict(),
        'case_row_id': row_id, 'case_subtype': subtype.loc[row_id], 'case_true_scratch': int(y.loc[row_id]),
        'case_score': float(shap_entry['scores'][local_index]), 'case_probability': float(shap_p[local_index]),
        'case_threshold': shap_threshold, 'case_reviewed': bool(shap_p[local_index] >= shap_threshold),
        'case_shap': local_phi.to_dict(), 'case_features': x.loc[row_id].to_dict(),
        'max_additivity_error': float(np.abs(phi.sum(axis=1).to_numpy() + base - shap_entry['scores']).max()),
    }
    decision_chart(y.loc[validation], p_validation, threshold, 'Platt-scaled' if calibrated else 'Raw', charts)
    reliability_chart(y.loc[validation], entry['raw'], entry['calibrated'], charts)
    shap_charts(phi, local_phi, charts)

    # The test labels are used here only, after locking the model, calibration and cutoff.
    test_scores = raw_score(entry['model'], x.loc[test])
    raw_test = probability_view(entry['model'], test_scores)
    platt_test = entry['platt'].predict_proba(test_scores.reshape(-1, 1))[:, 1]
    p_test = platt_test if calibrated else raw_test
    test_policies = policy_rows(y.loc[test], p_test, threshold)
    test_policies.to_csv(output / 'test_decisions.csv')
    pd.DataFrame({'row_id': test, 'actual_scratch': y.loc[test].to_numpy(),
                  'subtype': subtype.loc[test].to_numpy(), 'raw_score': test_scores, 'probability': p_test,
                  'review': (p_test >= threshold).astype(int)}).to_csv(output / 'test_predictions.csv', index=False)
    test_result = {
        'auc': float(roc_auc_score(y.loc[test], test_scores)),
        'raw_calibration': calibration_metrics(y.loc[test], raw_test),
        'platt_calibration': calibration_metrics(y.loc[test], platt_test),
        'policies': test_policies.to_dict(orient='index'),
        'bootstrap_95': bootstrap_test(y.loc[test], test_scores, p_test, threshold),
    }
    package = {
        'audit': audit, 'splits': split_counts, 'features': list(x.columns),
        'single_feature_screen': screen.to_dict(),
        'models': comparison.to_dict(orient='records'), 'model_selected': name,
        'calibration_selected': 'Platt' if calibrated else 'Raw', 'threshold': threshold,
        'bayes_threshold': 1 / (COST_FN + 1), 'false_negative_weight': COST_FN,
        'validation_decisions': validation_policies.to_dict(orient='index'),
        'validation_sensitivity': sensitivity.to_dict(orient='records'),
        'validation_auc_without_plate_context': float(no_plate_auc),
        'shap': shap_result, 'test': test_result,
    }
    (output / 'summary.json').write_text(json.dumps(package, indent=2, allow_nan=False) + '\n')
    if verbose:
        print(f"Held-out AUC {test_result['auc']:.4f}\n{test_policies.round(4).to_string()}", flush=True)
    return package


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / 'faults.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    analyze(args.data, args.output)
