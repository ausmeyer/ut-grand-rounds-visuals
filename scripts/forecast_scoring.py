"""Raw-count WIS across the 50 states and DC, on matched forecast keys."""

from datetime import date, timedelta
import math

BASELINE = "FluSight-baseline"
LOCATIONS = frozenset("01 02 04 05 06 08 09 10 11 12 13 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 50 51 53 54 55 56".split())
LEVELS = (.01, .025, .05, .1, .15, .2, .25, .3, .35, .4, .45, .5,
          .55, .6, .65, .7, .75, .8, .85, .9, .95, .975, .99)


def distributions(rows, model_id, truth):
    grouped = {}
    for row in rows:
        horizon, quantile, value = int(row["horizon"]), float(row["output_type_id"]), float(row["value"])
        reference, target = date.fromisoformat(row["reference_date"]), date.fromisoformat(row["target_end_date"])
        if (row["model_id"] != model_id or row["location"] not in LOCATIONS or row["target"] != "wk inc flu hosp"
                or row["output_type"] != "quantile" or quantile not in LEVELS or horizon not in range(4)
                or not math.isfinite(value) or value < 0 or (row["location"], row["target_end_date"]) not in truth
                or target != reference + timedelta(weeks=horizon)):
            raise ValueError("Invalid state/DC scoring row")
        key = (horizon, row["reference_date"], row["target_end_date"], row["location"])
        values = grouped.setdefault(key, {})
        if quantile in values:
            raise ValueError("Duplicate scoring quantile")
        values[quantile] = value
    for values in grouped.values():
        if set(values) != set(LEVELS):
            raise ValueError("Scoring requires all 23 quantiles")
        ordered = [values[q] for q in LEVELS]
        if ordered != sorted(ordered):
            raise ValueError("Crossed scoring quantiles")
    return grouped


def wis(observed, quantiles):
    """WIS equals the mean quantile score on the symmetric 23-quantile grid."""
    return math.fsum(2 * (q if observed >= quantiles[q] else 1 - q) * abs(observed - quantiles[q])
                     for q in LEVELS) / len(LEVELS)


def horizon_scores(model, baseline, truth):
    scores = []
    if not baseline.keys() <= model.keys():
        raise ValueError("Baseline scoring keys must be present in the plotted model")
    for horizon in range(4):
        keys = sorted(key for key in baseline if key[0] == horizon)
        if not keys:
            raise ValueError("No matched baseline weeks for this horizon")
        if {key[3] for key in keys} != LOCATIONS:
            raise ValueError("Expected all 50 states and DC at each scoring horizon")
        model_wis = [wis(truth[(key[3], key[2])], model[key]) for key in keys]
        baseline_wis = [wis(truth[(key[3], key[2])], baseline[key]) for key in keys]
        denominator = math.fsum(baseline_wis)
        if denominator <= 0:
            raise ValueError("Relative WIS requires a positive baseline denominator")
        # With identical forecast keys for all comparators, baseline-scaled
        # pairwise geometric-mean skill reduces exactly to this sum-score ratio.
        scores.append({"horizon": horizon, "rwis": math.fsum(model_wis) / denominator,
                       "n": len(keys), "mean_wis": math.fsum(model_wis) / len(keys),
                       "baseline_mean_wis": denominator / len(keys),
                       "reference_dates": sorted({key[1] for key in keys}),
                       "locations": sorted({key[3] for key in keys})})
    return scores
