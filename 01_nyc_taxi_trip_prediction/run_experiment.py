"""Reproducible NYC taxi trip-duration experiment using only the Python standard library."""
from __future__ import annotations
import argparse, csv, json, math, random, statistics
from datetime import datetime, timedelta
from pathlib import Path

SEED = 255
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
FEATURE_NAMES = ["vendor_id", "passenger_count", "pickup_longitude", "pickup_latitude", "dropoff_longitude", "dropoff_latitude", "hour", "weekday", "month", "is_weekend", "is_rush_hour", "distance_miles", "delta_longitude", "delta_latitude"]

def make_sample(n):
    rng = random.Random(SEED); start = datetime(2016, 1, 1); rows = []
    for i in range(n):
        pickup = start + timedelta(minutes=rng.randrange(90 * 24 * 60))
        plon, plat = rng.gauss(-73.975, .035), rng.gauss(40.755, .030)
        dlon, dlat = plon + rng.gauss(0, .035), plat + rng.gauss(0, .030)
        passenger = rng.randint(1, 4); hour = pickup.hour; rush = int(7 <= hour <= 9 or 16 <= hour <= 19)
        dist = 69 * math.sqrt(((plon-dlon)*math.cos(math.radians(plat)))**2 + (plat-dlat)**2)
        duration = max(60, round(240 + 115*dist + 90*rush + 25*(passenger-1) + rng.gauss(0, 100)))
        rows.append({"id": i, "vendor_id": rng.randint(1, 2), "pickup_datetime": pickup.isoformat(sep=" "), "passenger_count": passenger, "pickup_longitude": plon, "pickup_latitude": plat, "dropoff_longitude": dlon, "dropoff_latitude": dlat, "trip_duration": duration})
    return sorted(rows, key=lambda r: r["pickup_datetime"])

def read_csv(path):
    with open(path, newline="") as f: return list(csv.DictReader(f))

def featurize(rows):
    result = []
    for r in rows:
        try:
            dt = datetime.fromisoformat(str(r["pickup_datetime"]).replace("Z", "+00:00"))
            keys = ["vendor_id", "passenger_count", "pickup_longitude", "pickup_latitude", "dropoff_longitude", "dropoff_latitude"]
            v = {k: float(r[k]) for k in keys}; dlat = math.radians(v["dropoff_latitude"]-v["pickup_latitude"]); dlon = math.radians(v["dropoff_longitude"]-v["pickup_longitude"])
            a = math.sin(dlat/2)**2 + math.cos(math.radians(v["pickup_latitude"])) * math.cos(math.radians(v["dropoff_latitude"])) * math.sin(dlon/2)**2
            dist = 3958.8 * 2 * math.asin(min(1, math.sqrt(max(0, a)))); hour, weekday, month = dt.hour, dt.weekday(), dt.month
            x = [v["vendor_id"], v["passenger_count"], v["pickup_longitude"], v["pickup_latitude"], v["dropoff_longitude"], v["dropoff_latitude"], hour, weekday, month, int(weekday >= 5), int(hour in [7,8,9,16,17,18,19]), dist, v["dropoff_longitude"]-v["pickup_longitude"], v["dropoff_latitude"]-v["pickup_latitude"]]
            y = float(r["trip_duration"])
            if y > 0 and dist < 100: result.append((x, y))
        except (KeyError, ValueError, TypeError): pass
    return result

def fit_predict(train_x, train_y, test_x):
    means = [statistics.mean(c) for c in zip(*train_x)]; scales = [statistics.pstdev(c) or 1 for c in zip(*train_x)]
    z = [[(v-m)/s for v,m,s in zip(row, means, scales)] for row in train_x]; tz = [[(v-m)/s for v,m,s in zip(row, means, scales)] for row in test_x]
    target = [math.log1p(y) for y in train_y]; w = [0.0] * len(FEATURE_NAMES); b = statistics.mean(target)
    for _ in range(1800):
        errors = [b + sum(a*q for a,q in zip(w,row)) - t for row,t in zip(z,target)]
        b -= .04 * statistics.mean(errors)
        for j in range(len(w)): w[j] -= .04 * (sum(e*row[j] for e,row in zip(errors,z))/len(z) + .002*w[j])
    return [max(1, math.expm1(b + sum(a*q for a,q in zip(w,row)))) for row in tz], [abs(a/s) for a,s in zip(w, scales)]

def score(actual, pred):
    mae = sum(abs(a-p) for a,p in zip(actual,pred))/len(actual); rmse = math.sqrt(sum((a-p)**2 for a,p in zip(actual,pred))/len(actual)); mean = statistics.mean(actual); ss = sum((a-mean)**2 for a in actual)
    return {"mae_seconds": round(mae, 3), "rmse_seconds": round(rmse, 3), "r2": round(1-sum((a-p)**2 for a,p in zip(actual,pred))/ss, 4) if ss else 0}

def svg_hist(values, path):
    lo, hi = min(values), max(values); bins = [0]*30
    for v in values: bins[min(29, int((v-lo)/(hi-lo+1e-9)*30))] += 1
    peak = max(bins) or 1; bars = ''.join(f'<rect x="{20+i*15}" y="{180-c/peak*150:.1f}" width="12" height="{c/peak*150:.1f}" fill="#2c7fb8"/>' for i,c in enumerate(bins))
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="220"><text x="20" y="15">Trip duration distribution</text>{bars}<line x1="20" y1="180" x2="470" y2="180" stroke="black"/></svg>')

def svg_scatter(actual, pred, path):
    hi=max(max(actual),max(pred)); pts=''.join(f'<circle cx="{20+440*a/hi:.1f}" cy="{200-180*p/hi:.1f}" r="1.5" fill="#2c7fb8" opacity=".35"/>' for a,p in zip(actual,pred))
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="220"><text x="20" y="15">Predicted vs actual duration</text><line x1="20" y1="200" x2="460" y2="20" stroke="red" stroke-dasharray="4"/>{pts}</svg>')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--input"); ap.add_argument("--sample-size", type=int, default=6000); args=ap.parse_args(); OUT.mkdir(exist_ok=True)
    rows = read_csv(args.input) if args.input else make_sample(args.sample_size); data=featurize(rows); cut=max(1,int(len(data)*.8)); train,test=data[:cut],data[cut:]
    train_x=[a for a,_ in train]; train_y=[b for _,b in train]; test_x=[a for a,_ in test]; test_y=[b for _,b in test]; pred,importance=fit_predict(train_x,train_y,test_x); baseline=[statistics.median(train_y)]*len(test_y)
    metrics={"source": "csv:"+args.input if args.input else "deterministic synthetic NYC-like fallback", "rows_after_cleaning":len(data), "train_rows":len(train), "test_rows":len(test), "baseline_median_seconds":statistics.median(train_y), "baseline":score(test_y,baseline), "linear_log_target":score(test_y,pred)}
    (OUT/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
    with open(OUT/"predictions.csv","w",newline="") as f: w=csv.writer(f); w.writerow(["actual_seconds","predicted_seconds"]); w.writerows(zip(test_y,pred))
    with open(OUT/"feature_importance.csv","w",newline="") as f: w=csv.writer(f); w.writerow(["feature","importance"]); w.writerows(sorted(zip(FEATURE_NAMES,importance),key=lambda z:z[1],reverse=True))
    svg_hist([y for _,y in data],OUT/"duration_distribution.svg"); svg_scatter(test_y,pred,OUT/"predicted_vs_actual.svg"); print(json.dumps(metrics,indent=2))

if __name__ == "__main__": main()
