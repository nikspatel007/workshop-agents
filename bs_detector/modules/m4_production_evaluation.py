"""
Production Evaluation Framework for Unknown Data
This is what you actually need in the real world!
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field

from config.llm_factory import LLMFactory


@dataclass
class EvaluationCase:
    """A claim to evaluate (no ground truth needed)"""
    id: str
    claim: str
    domain: Optional[str] = None  # aviation, medical, tech, etc.
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductionMetrics(BaseModel):
    """Metrics we can calculate without ground truth"""
    # Core quality metrics
    reasoning_quality: float = Field(ge=0, le=1)
    confidence_calibration: float = Field(ge=0, le=1)
    consistency_score: float = Field(ge=0, le=1)
    
    # LLM-as-judge metrics
    claim_plausibility: float = Field(ge=0, le=1)
    logical_coherence: float = Field(ge=0, le=1)
    evidence_quality: float = Field(ge=0, le=1)
    
    # Drift and anomaly metrics
    domain_confidence: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    
    # Behavioral metrics
    response_time: float
    token_efficiency: float = Field(ge=0, le=1)
    
    # Aggregate scores
    trust_score: float = Field(ge=0, le=1)
    requires_human_review: bool


class LLMJudge:
    """Uses an LLM to evaluate another LLM's output"""
    
    def __init__(self, judge_model=None):
        self.judge = judge_model or LLMFactory.create_llm()
    
    def evaluate_reasoning_quality(self, claim: str, verdict: str, reasoning: str) -> float:
        """Judge if reasoning supports the verdict"""
        prompt = f"""
        Evaluate the quality of this reasoning for a BS detection task.
        
        Claim: {claim}
        Verdict: {verdict}
        Reasoning: {reasoning}
        
        Score from 0-1 based on:
        1. Does the reasoning logically support the verdict?
        2. Are the arguments coherent and well-structured?
        3. Does it address the key aspects of the claim?
        4. Is it free from logical fallacies?
        
        Respond with ONLY a number between 0 and 1.
        """
        
        try:
            response = self.judge.invoke(prompt)
            return float(response.content.strip())
        except:
            return 0.5  # Default middle score if evaluation fails
    
    def evaluate_claim_plausibility(self, claim: str, verdict: str) -> float:
        """Judge if the verdict seems plausible for the claim"""
        prompt = f"""
        Given this claim and verdict, evaluate if the verdict seems plausible.
        
        Claim: {claim}
        Verdict: {verdict}
        
        Consider:
        1. Does the verdict (BS or LEGITIMATE) make intuitive sense?
        2. Are there obvious red flags that were missed?
        3. Does this match general knowledge and common sense?
        
        Score from 0-1 where:
        - 1.0 = Verdict seems very plausible
        - 0.5 = Uncertain
        - 0.0 = Verdict seems wrong
        
        Respond with ONLY a number between 0 and 1.
        """
        
        try:
            response = self.judge.invoke(prompt)
            return float(response.content.strip())
        except:
            return 0.5
    
    def evaluate_evidence_usage(self, claim: str, reasoning: str) -> float:
        """Judge how well evidence is used in reasoning"""
        prompt = f"""
        Evaluate how well evidence is used in this BS detection reasoning.
        
        Claim: {claim}
        Reasoning: {reasoning}
        
        Score from 0-1 based on:
        1. Are specific facts or examples cited?
        2. Is the evidence relevant to the claim?
        3. Is there appropriate skepticism where needed?
        4. Are sources or expertise referenced appropriately?
        
        Respond with ONLY a number between 0 and 1.
        """
        
        try:
            response = self.judge.invoke(prompt)
            return float(response.content.strip())
        except:
            return 0.5


class ConsistencyChecker:
    """Checks consistency across multiple evaluations"""
    
    def __init__(self):
        self.evaluation_history = []
    
    def add_evaluation(self, claim: str, result: dict):
        """Store evaluation for consistency checking"""
        self.evaluation_history.append({
            'claim': claim,
            'result': result,
            'timestamp': datetime.now()
        })
    
    def check_consistency(self, claim: str, result: dict) -> float:
        """Check if this evaluation is consistent with similar past evaluations"""
        if not self.evaluation_history:
            return 0.5  # No history to compare
        
        # Find similar claims
        similar_evaluations = self._find_similar_claims(claim)
        
        if not similar_evaluations:
            return 0.5  # No similar claims found
        
        # Check verdict consistency
        verdict_consistency = self._check_verdict_consistency(result, similar_evaluations)
        
        # Check confidence consistency
        confidence_consistency = self._check_confidence_consistency(result, similar_evaluations)
        
        return (verdict_consistency + confidence_consistency) / 2
    
    def _find_similar_claims(self, claim: str, threshold: float = 0.7) -> List[dict]:
        """Find semantically similar claims in history"""
        # In production, you'd use embeddings for similarity
        # For now, simple keyword matching
        similar = []
        claim_words = set(claim.lower().split())
        
        for eval_item in self.evaluation_history[-100:]:  # Last 100 evaluations
            hist_words = set(eval_item['claim'].lower().split())
            overlap = len(claim_words & hist_words) / len(claim_words | hist_words)
            
            if overlap > threshold:
                similar.append(eval_item)
        
        return similar
    
    def _check_verdict_consistency(self, result: dict, similar: List[dict]) -> float:
        """Check if verdicts are consistent for similar claims"""
        verdicts = [s['result']['verdict'] for s in similar]
        if not verdicts:
            return 0.5
        
        # Count how many match current verdict
        matching = sum(1 for v in verdicts if v == result['verdict'])
        return matching / len(verdicts)
    
    def _check_confidence_consistency(self, result: dict, similar: List[dict]) -> float:
        """Check if confidence levels are consistent"""
        confidences = [s['result']['confidence'] for s in similar]
        if not confidences:
            return 0.5
        
        avg_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)
        
        # Check if current confidence is within reasonable range
        if std_confidence == 0:
            return 1.0 if abs(result['confidence'] - avg_confidence) < 10 else 0.5
        
        z_score = abs(result['confidence'] - avg_confidence) / std_confidence
        return max(0, 1 - (z_score / 3))  # Normalize to 0-1


class DriftDetector:
    """Detects when inputs drift from expected distribution"""
    
    def __init__(self, known_domains: List[str] = None):
        self.known_domains = known_domains or ['aviation', 'technology', 'medical', 'finance', 'general']
        self.domain_examples = self._initialize_domain_examples()
    
    def _initialize_domain_examples(self) -> Dict[str, List[str]]:
        """Initialize example claims for each domain"""
        return {
            'aviation': ['aircraft', 'flight', 'pilot', 'airport', 'boeing', 'airbus'],
            'technology': ['software', 'algorithm', 'computer', 'AI', 'data', 'code'],
            'medical': ['patient', 'treatment', 'disease', 'doctor', 'medicine', 'symptoms'],
            'finance': ['investment', 'market', 'stock', 'trading', 'economy', 'bank'],
            'general': []
        }
    
    def detect_domain(self, claim: str) -> Tuple[str, float]:
        """Detect domain and confidence"""
        claim_lower = claim.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_examples.items():
            if domain == 'general':
                continue
            
            score = sum(1 for keyword in keywords if keyword in claim_lower)
            domain_scores[domain] = score
        
        if max(domain_scores.values()) == 0:
            return 'general', 0.5
        
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = min(domain_scores[best_domain] / 3, 1.0)  # Normalize
        
        return best_domain, confidence
    
    def calculate_anomaly_score(self, claim: str, domain: str) -> float:
        """Calculate how anomalous this claim is"""
        # Simple implementation - in production use embeddings
        domain, domain_confidence = self.detect_domain(claim)
        
        # High anomaly if low domain confidence
        anomaly = 1.0 - domain_confidence
        
        # Additional checks
        if len(claim) < 10 or len(claim) > 500:
            anomaly = max(anomaly, 0.7)
        
        return anomaly


class ProductionEvaluator:
    """Main evaluator for production use - works without ground truth"""
    
    def __init__(self):
        self.llm_judge = LLMJudge()
        self.consistency_checker = ConsistencyChecker()
        self.drift_detector = DriftDetector()
        self.evaluation_history = []
    
    def evaluate(self, claim: str, detector_result: dict) -> ProductionMetrics:
        """Evaluate a BS detection result without ground truth"""
        import time
        start_time = time.time()
        
        # Extract components
        verdict = detector_result.get('verdict', 'ERROR')
        confidence = detector_result.get('confidence', 0)
        reasoning = detector_result.get('reasoning', '')
        
        # 1. LLM-as-Judge evaluations
        reasoning_quality = self.llm_judge.evaluate_reasoning_quality(
            claim, verdict, reasoning
        )
        claim_plausibility = self.llm_judge.evaluate_claim_plausibility(
            claim, verdict
        )
        evidence_quality = self.llm_judge.evaluate_evidence_usage(
            claim, reasoning
        )
        
        # 2. Confidence calibration
        confidence_calibration = self._evaluate_confidence_calibration(
            confidence, reasoning, verdict
        )
        
        # 3. Consistency checking
        consistency_score = self.consistency_checker.check_consistency(
            claim, detector_result
        )
        
        # 4. Drift detection
        domain, domain_confidence = self.drift_detector.detect_domain(claim)
        anomaly_score = self.drift_detector.calculate_anomaly_score(claim, domain)
        
        # 5. Behavioral metrics
        response_time = time.time() - start_time
        token_efficiency = self._calculate_token_efficiency(claim, reasoning)
        
        # 6. Calculate trust score
        quality_scores = [
            reasoning_quality,
            claim_plausibility,
            evidence_quality,
            confidence_calibration,
            consistency_score,
            domain_confidence
        ]
        trust_score = np.mean(quality_scores)
        
        # 7. Determine if human review needed
        requires_human_review = (
            trust_score < 0.6 or
            confidence < 50 or
            anomaly_score > 0.7 or
            (confidence > 90 and claim_plausibility < 0.5)  # Very confident but implausible
        )
        
        # Store in history
        self.consistency_checker.add_evaluation(claim, detector_result)
        
        # Create metrics object
        metrics = ProductionMetrics(
            reasoning_quality=reasoning_quality,
            confidence_calibration=confidence_calibration,
            consistency_score=consistency_score,
            claim_plausibility=claim_plausibility,
            logical_coherence=reasoning_quality,  # Reuse for now
            evidence_quality=evidence_quality,
            domain_confidence=domain_confidence,
            anomaly_score=anomaly_score,
            response_time=response_time,
            token_efficiency=token_efficiency,
            trust_score=trust_score,
            requires_human_review=requires_human_review
        )
        
        # Store evaluation
        self.evaluation_history.append({
            'timestamp': datetime.now(),
            'claim': claim,
            'domain': domain,
            'result': detector_result,
            'metrics': metrics.model_dump()
        })
        
        return metrics
    
    def _evaluate_confidence_calibration(self, confidence: int, reasoning: str, verdict: str) -> float:
        """Evaluate if confidence matches the certainty in reasoning"""
        uncertain_phrases = [
            'might', 'possibly', 'could be', 'unclear', 'uncertain',
            'not sure', 'perhaps', 'maybe', 'appears to', 'seems'
        ]
        certain_phrases = [
            'definitely', 'certainly', 'clearly', 'obviously', 'proven',
            'confirmed', 'established', 'without doubt', 'factual'
        ]
        
        reasoning_lower = reasoning.lower()
        uncertain_count = sum(1 for phrase in uncertain_phrases if phrase in reasoning_lower)
        certain_count = sum(1 for phrase in certain_phrases if phrase in reasoning_lower)
        
        # Calculate linguistic certainty
        if uncertain_count + certain_count == 0:
            linguistic_certainty = 50  # Neutral
        else:
            linguistic_certainty = (certain_count / (uncertain_count + certain_count)) * 100
        
        # Compare with stated confidence
        calibration_error = abs(confidence - linguistic_certainty) / 100
        calibration_score = 1 - calibration_error
        
        # Penalize extreme confidence without strong language
        if confidence > 90 and certain_count == 0:
            calibration_score *= 0.7
        if confidence < 20 and uncertain_count == 0:
            calibration_score *= 0.7
        
        return max(0, min(1, calibration_score))
    
    def _calculate_token_efficiency(self, claim: str, reasoning: str) -> float:
        """Calculate how efficiently the reasoning addresses the claim"""
        if not reasoning:
            return 0.0
        
        claim_length = len(claim.split())
        reasoning_length = len(reasoning.split())
        
        # Ideal ratio: reasoning should be 3-10x the claim length
        ratio = reasoning_length / max(claim_length, 1)
        
        if ratio < 2:
            return 0.5  # Too brief
        elif ratio > 20:
            return 0.5  # Too verbose
        else:
            # Peak efficiency around 5x
            return 1.0 - abs(ratio - 5) / 15
    
    def get_evaluation_summary(self, last_n: int = 100) -> dict:
        """Get summary statistics of recent evaluations"""
        recent = self.evaluation_history[-last_n:]
        if not recent:
            return {"error": "No evaluations yet"}
        
        metrics_arrays = {
            'trust_scores': [e['metrics']['trust_score'] for e in recent],
            'anomaly_scores': [e['metrics']['anomaly_score'] for e in recent],
            'response_times': [e['metrics']['response_time'] for e in recent],
            'human_review_rate': sum(1 for e in recent if e['metrics']['requires_human_review']) / len(recent)
        }
        
        # Domain distribution
        domain_counts = {}
        for e in recent:
            domain = e.get('domain', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        return {
            'total_evaluations': len(recent),
            'avg_trust_score': np.mean(metrics_arrays['trust_scores']),
            'avg_anomaly_score': np.mean(metrics_arrays['anomaly_scores']),
            'avg_response_time': np.mean(metrics_arrays['response_times']),
            'human_review_rate': metrics_arrays['human_review_rate'],
            'domain_distribution': domain_counts,
            'trust_score_std': np.std(metrics_arrays['trust_scores']),
            'low_trust_claims': sum(1 for t in metrics_arrays['trust_scores'] if t < 0.6)
        }
    
    def export_for_human_review(self) -> List[dict]:
        """Export cases that need human review"""
        return [
            {
                'claim': e['claim'],
                'result': e['result'],
                'metrics': e['metrics'],
                'timestamp': e['timestamp'].isoformat() if hasattr(e['timestamp'], 'isoformat') else str(e['timestamp'])
            }
            for e in self.evaluation_history
            if e['metrics']['requires_human_review']
        ]


# Example usage
def evaluate_unknown_claim(claim: str, bs_detector):
    """Example of production evaluation"""
    # Get detector result
    detector_result = bs_detector(claim)
    
    # Evaluate without ground truth
    evaluator = ProductionEvaluator()
    metrics = evaluator.evaluate(claim, detector_result)
    
    # Make decision based on metrics
    if metrics.requires_human_review:
        print(f"⚠️  Low confidence - flagged for human review")
        print(f"   Trust score: {metrics.trust_score:.2f}")
        print(f"   Issues: ", end="")
        if metrics.anomaly_score > 0.7:
            print("Unusual claim, ", end="")
        if metrics.trust_score < 0.6:
            print("Low quality metrics, ", end="")
        if metrics.consistency_score < 0.5:
            print("Inconsistent with similar claims", end="")
        print()
    else:
        print(f"✅ Evaluation complete")
        print(f"   Verdict: {detector_result['verdict']}")
        print(f"   Trust score: {metrics.trust_score:.2f}")
        print(f"   Domain: {evaluator.drift_detector.detect_domain(claim)[0]}")
    
    return metrics


if __name__ == "__main__":
    # Demo the production evaluator
    from modules.m3_langgraph import check_claim_with_graph
    
    print("Production Evaluation Demo")
    print("=" * 50)
    
    # Test various claims
    test_claims = [
        "The Boeing 747 has four engines",  # Aviation - should be consistent
        "Python code can read your mind through the screen",  # Tech - obvious BS
        "The new COVID vaccine contains microchips",  # Medical - conspiracy theory
        "You should invest all your money in cryptocurrency",  # Finance - bad advice
        "The moon is made of green cheese",  # General - classic BS
    ]
    
    evaluator = ProductionEvaluator()
    
    for claim in test_claims:
        print(f"\nClaim: {claim}")
        result = check_claim_with_graph(claim)
        metrics = evaluator.evaluate(claim, result)
        
        print(f"Verdict: {result['verdict']} (confidence: {result['confidence']}%)")
        print(f"Trust Score: {metrics.trust_score:.2f}")
        print(f"Needs Review: {'Yes' if metrics.requires_human_review else 'No'}")
        print(f"Domain: {evaluator.drift_detector.detect_domain(claim)[0]}")
    
    # Show summary
    print("\n" + "=" * 50)
    print("Evaluation Summary:")
    summary = evaluator.get_evaluation_summary()
    print(f"Average trust score: {summary['avg_trust_score']:.2f}")
    print(f"Human review rate: {summary['human_review_rate']:.1%}")
    print(f"Domain distribution: {summary['domain_distribution']}")