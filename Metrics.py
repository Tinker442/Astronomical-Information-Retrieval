#metric functions
import math
def map_score(search_result_relevances: list[int], cut_off=10) -> float:
    """
    Calculates the mean average precision score given a list of labeled search results, where
    each item in the list corresponds to a document that was retrieved and is rated as 0 or 1
    for whether it was relevant.

    Args:
        search_results: A list of 0/1 values for whether each search result returned by your 
                        ranking function is relevant
        cut_off: The search result rank to stop calculating MAP. The default cut-off is 10;
                 calculate MAP@10 to score your ranking function.

    Returns:
        The MAP score
    """
    # TODO: Implement MAP
    score=0
    i=0
    correct=0
    precision = 1
    relavent = sum(search_result_relevances) #number of relavent docs
    if relavent ==0:
        return 0
    while i<min(cut_off,relavent):
        
        if search_result_relevances[i]==1:
            correct+=1
            precision = correct/(1+i)
            score += precision
        i+=1
        

    
    score = score/min(cut_off,relavent)
    

    return score
    


def ndcg_score(search_result_relevances: list[float], 
               ideal_relevance_score_ordering: list[float], cut_off=10):
    """
    Calculates the normalized discounted cumulative gain (NDCG) given a lists of relevance scores.
    Relevance scores can be ints or floats, depending on how the data was labeled for relevance.

    Args:
        search_result_relevances: 
            A list of relevance scores for the results returned by your ranking function in the
            order in which they were returned. These are the human-derived document relevance scores,
            *not* the model generated scores.
            
        ideal_relevance_score_ordering: The list of relevance scores for results for a query, sorted by relevance score in descending order.
            Use this list to calculate IDCG (Ideal DCG).

        cut_off: The default cut-off is 10.

    Returns:
        The NDCG score
    """
    # TODO: Implement NDCG

    dcg=search_result_relevances[0]
    idcg=ideal_relevance_score_ordering[0]
    number_of_results = min(len(search_result_relevances),cut_off)
    for i in range(number_of_results-1):
        dcg+= search_result_relevances[1+i]/math.log(i+2,2)
    for i in range(number_of_results-1):
        idcg+= ideal_relevance_score_ordering[1+i]/math.log(i+2,2)

    ndcg = dcg/idcg
    return ndcg