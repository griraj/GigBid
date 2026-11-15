from evals.runners.evaluate_gold import grade

class StaticIndex:
    def search(self,query,k,variant,persona,requirements):
        return [{'id':'gold'},{'id':'wrong'}]

def test_known_ranking_metrics():
    data=[{'query':'Python','persona':'ai','relevant_evidence_ids':['gold'],'job_type':'ml'}]
    result=grade(StaticIndex(),data,['v0'])['v0']
    assert result['recall_at_5']==1
    assert result['mrr']==1
    assert result['ndcg_at_10']==1
    assert result['by_job_type']['ml']==1
