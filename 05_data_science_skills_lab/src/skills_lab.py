"""Dependency-free data-science skills for Project 05."""
import math, random, csv
NUMERIC=("tenure_months","monthly_usage","support_tickets")
def load_clean(path):
    with open(path,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    seen=set(); clean=[]
    for row in rows:
        if row["customer_id"] in seen: continue
        seen.add(row["customer_id"])
        for col in NUMERIC: row[col]=None if row[col]=="" else float(row[col])
        row["renewed"]=int(row["renewed"]); clean.append(row)
    for col in NUMERIC:
        vals=sorted(r[col] for r in clean if r[col] is not None)
        med=vals[len(vals)//2] if len(vals)%2 else (vals[len(vals)//2-1]+vals[len(vals)//2])/2
        for r in clean:
            if r[col] is None: r[col]=med
    return clean,len(rows)-len(clean)
def mean(xs):
    xs=list(xs); return sum(xs)/len(xs)
def correlation(xs,ys):
    mx,my=mean(xs),mean(ys); num=sum((x-mx)*(y-my) for x,y in zip(xs,ys)); den=math.sqrt(sum((x-mx)**2 for x in xs)*sum((y-my)**2 for y in ys)); return num/den if den else 0.0
def linear_regression(xs,ys):
    mx,my=mean(xs),mean(ys); slope=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs); return my-slope*mx,slope
def regression_metrics(actual,predicted):
    mse=mean((a-p)**2 for a,p in zip(actual,predicted)); return {"mae":mean(abs(a-p) for a,p in zip(actual,predicted)),"rmse":math.sqrt(mse)}
def classification_metrics(actual,predicted):
    tp=sum(a==p==1 for a,p in zip(actual,predicted)); tn=sum(a==p==0 for a,p in zip(actual,predicted)); fp=sum(a==0 and p==1 for a,p in zip(actual,predicted)); fn=sum(a==1 and p==0 for a,p in zip(actual,predicted)); return {"accuracy":(tp+tn)/len(actual),"precision":tp/(tp+fp) if tp+fp else 0,"recall":tp/(tp+fn) if tp+fn else 0,"confusion_matrix":[[tn,fp],[fn,tp]]}
def kmeans(points,k=2,seed=255,iterations=30):
    rng=random.Random(seed); centers=[list(p) for p in rng.sample(points,k)]
    for _ in range(iterations):
        labels=[min(range(k),key=lambda j:sum((p[d]-centers[j][d])**2 for d in range(len(p)))) for p in points]; new=[]
        for j in range(k):
            group=[p for p,l in zip(points,labels) if l==j]; new.append([mean([p[d] for p in group]) for d in range(len(points[0]))] if group else centers[j])
        if new==centers: break
        centers=new
    return labels,centers
def svg_scatter(rows,path):
    w,h,pad=640,400,55; xs=[r["tenure_months"] for r in rows]; ys=[r["monthly_usage"] for r in rows]; sx=lambda x:pad+(x-min(xs))/(max(xs)-min(xs))*(w-2*pad); sy=lambda y:h-pad-(y-min(ys))/(max(ys)-min(ys))*(h-2*pad)
    circles=''.join(f'<circle cx="{sx(r["tenure_months"]):.1f}" cy="{sy(r["monthly_usage"]):.1f}" r="5" fill="{("#2563eb" if r["renewed"] else "#dc2626")}"/>' for r in rows)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="{w/2}" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Tenure vs monthly usage</text><line x1="55" y1="345" x2="585" y2="345" stroke="black"/><line x1="55" y1="55" x2="55" y2="345" stroke="black"/>{circles}<text x="320" y="385" text-anchor="middle" font-family="sans-serif">tenure (months)</text><text transform="translate(15 210) rotate(-90)" text-anchor="middle" font-family="sans-serif">usage</text></svg>'
    with open(path,"w",encoding="utf-8") as f: f.write(s)

def svg_clusters(points,labels,centers,path):
    w,h,pad=640,400,55; xs=[p[0] for p in points]; ys=[p[1] for p in points]; sx=lambda x:pad+(x-min(xs))/(max(xs)-min(xs))*(w-2*pad); sy=lambda y:h-pad-(y-min(ys))/(max(ys)-min(ys))*(h-2*pad); colors=("#2563eb","#dc2626")
    circles=''.join(f'<circle cx="{sx(p[0]):.1f}" cy="{sy(p[1]):.1f}" r="5" fill="{colors[l]}"/>' for p,l in zip(points,labels))
    marks=''.join(f'<path d="M {sx(c[0])-7:.1f} {sy(c[1])-7:.1f} L {sx(c[0])+7:.1f} {sy(c[1])+7:.1f} M {sx(c[0])+7:.1f} {sy(c[1])-7:.1f} L {sx(c[0])-7:.1f} {sy(c[1])+7:.1f}" stroke="black" stroke-width="2"/>' for c in centers)
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="{w/2}" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Customer health clusters</text><line x1="55" y1="345" x2="585" y2="345" stroke="black"/><line x1="55" y1="55" x2="55" y2="345" stroke="black"/>{circles}{marks}<text x="320" y="385" text-anchor="middle" font-family="sans-serif">monthly usage</text><text transform="translate(15 210) rotate(-90)" text-anchor="middle" font-family="sans-serif">support tickets</text></svg>'
    with open(path,"w",encoding="utf-8") as f: f.write(s)
