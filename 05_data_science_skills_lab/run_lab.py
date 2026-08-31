import json,os,sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"src"))
from skills_lab import *
ROOT=os.path.dirname(__file__); data,duplicates=load_clean(os.path.join(ROOT,"data","customer_health.csv")); os.makedirs(os.path.join(ROOT,"artifacts"),exist_ok=True)
xs=[r["tenure_months"] for r in data]; usage=[r["monthly_usage"] for r in data]; tickets=[r["support_tickets"] for r in data]; y=[r["renewed"] for r in data]
split=16; a,b=linear_regression(xs[:split],usage[:split]); test_x=xs[split:]; test_y=usage[split:]; pred=[a+b*x for x in test_x]
threshold=45; cls=[int(r["monthly_usage"]>=threshold and r["support_tickets"]<=2) for r in data]; points=[[r["monthly_usage"],r["support_tickets"]] for r in data]; labels,centers=kmeans(points)
metrics={"data_quality":{"raw_rows":24,"clean_rows":len(data),"duplicates_removed":duplicates,"missing_values_imputed":1},"eda":{"usage_mean":mean(usage),"usage_renewal_correlation":correlation(usage,y),"usage_ticket_correlation":correlation(usage,tickets)},"regression":{"feature":"tenure_months","target":"monthly_usage","train_rows":split,"test_rows":len(test_x),**regression_metrics(test_y,pred)},"classification":{"rule":"usage >= 45 and support_tickets <= 2","threshold":threshold,**classification_metrics(y,cls)},"clustering":{"k":2,"features":["monthly_usage","support_tickets"],"cluster_sizes":[labels.count(i) for i in range(2)],"centers":centers}}
with open(os.path.join(ROOT,"artifacts","metrics.json"),"w") as f: json.dump(metrics,f,indent=2)
with open(os.path.join(ROOT,"artifacts","summary.json"),"w") as f: json.dump({"rows":data,"regression_predictions":[{"tenure_months":x,"actual_usage":actual,"predicted_usage":round(p,2)} for x,actual,p in zip(test_x,test_y,pred)]},f,indent=2)
svg_scatter(data,os.path.join(ROOT,"artifacts","tenure_usage.svg")); svg_clusters(points,labels,centers,os.path.join(ROOT,"artifacts","customer_clusters.svg")); print(json.dumps(metrics,indent=2))
