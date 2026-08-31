import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','src'))
from skills_lab import *
class SkillsLabTests(unittest.TestCase):
    def test_cleaning_deduplicates_and_imputes(self):
        rows,removed=load_clean(os.path.join(os.path.dirname(__file__),'..','data','customer_health.csv')); self.assertEqual((len(rows),removed),(23,1)); self.assertTrue(all(r['monthly_usage'] is not None for r in rows))
    def test_regression_and_metrics(self):
        self.assertEqual(linear_regression([1,2,3],[2,4,6]),(0.0,2.0)); self.assertEqual(regression_metrics([2,4],[2,5])['mae'],.5)
    def test_classification_counts(self):
        m=classification_metrics([0,0,1,1],[0,1,1,0]); self.assertEqual(m['confusion_matrix'],[[1,1],[1,1]]); self.assertEqual(m['accuracy'],.5)
    def test_kmeans_is_deterministic(self):
        p=[[0,0],[.1,.1],[10,10],[10.1,10.1]]; self.assertEqual(kmeans(p,seed=255),kmeans(p,seed=255))
if __name__=='__main__': unittest.main()
