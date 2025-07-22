"""
Iteration 3: Evaluation Framework with DeepEval
Builds on m2_langgraph.py by adding systematic evaluation capabilities.
"""

import json
from pathlib import Path
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field
import pandas as pd
from deepeval import assert_test
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

# Import our detectors from previous iterations
from modules.m1_baseline import check_claim
from modules.m2_langgraph import check_claim_with_graph
from config.llm_factory import LLMFactory


# Data models for evaluation
@dataclass
class AviationClaim:
    """Represents a claim from our dataset"""
    id: str
    claim: str
    verdict: str  # Ground truth
    difficulty: str
    category: str
    explanation: str
    needs_evidence: bool
    expected_confidence: int


class EvaluationResult(BaseModel):
    """Results from evaluating a detector"""
    iteration: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_claims: int
    correct: int
    accuracy: float
    
    # Breakdown by difficulty
    easy_accuracy: float
    medium_accuracy: float
    hard_accuracy: float
    
    # Breakdown by category
    category_accuracy: Dict[str, float]
    
    # Confidence analysis
    avg_confidence: float
    avg_confidence_when_correct: float
    avg_confidence_when_wrong: float
    
    # Performance metrics
    avg_response_time: float
    
    # Detailed results
    claim_results: List[dict] = Field(default_factory=list)


# Custom DeepEval Metrics
class BSDetectionAccuracy(BaseMetric):
    """Custom metric for BS detection accuracy"""
    
    def __init__(self):
        self.threshold = 1.0  # Require exact match
    
    @property
    def name(self):
        return "BS Detection Accuracy"
    
    def measure(self, test_case: LLMTestCase):
        """Check if the verdict matches ground truth"""
        self.success = test_case.actual_output == test_case.expected_output
        self.score = 1.0 if self.success else 0.0
        return self.score
    
    def is_successful(self):
        return self.success
    
    @property
    def reason(self):
        if self.success:
            return "Verdict matches ground truth"
        return f"Incorrect verdict"


class ConfidenceCalibration(BaseMetric):
    """Measures how well confidence aligns with accuracy"""
    
    def __init__(self):
        self.threshold = 0.7
    
    @property
    def name(self):
        return "Confidence Calibration"
    
    def measure(self, test_case: LLMTestCase):
        """Check if confidence aligns with correctness"""
        # Extract confidence from the result
        if hasattr(test_case, 'metadata') and 'confidence' in test_case.metadata:
            confidence = test_case.metadata['confidence']
            is_correct = test_case.actual_output == test_case.expected_output
            
            # High confidence should mean correct, low confidence should mean uncertain
            if is_correct and confidence >= 70:
                self.score = 1.0
            elif not is_correct and confidence < 50:
                self.score = 1.0  # Good - low confidence when wrong
            else:
                # Penalize high confidence when wrong or low confidence when right
                self.score = 1.0 - abs(confidence - (100 if is_correct else 0)) / 100
        else:
            self.score = 0.0
            
        self.success = self.score >= self.threshold
        return self.score
    
    def is_successful(self):
        return self.success
    
    @property
    def reason(self):
        return f"Confidence calibration score: {self.score:.2f}"


class ReasoningQuality(BaseMetric):
    """Evaluates the quality of reasoning provided"""
    
    def __init__(self, llm=None):
        self.threshold = 0.7
        self.llm = llm or LLMFactory.create_llm()
    
    @property
    def name(self):
        return "Reasoning Quality"
    
    def measure(self, test_case: LLMTestCase):
        """Use LLM to evaluate reasoning quality"""
        if hasattr(test_case, 'metadata') and 'reasoning' in test_case.metadata:
            reasoning = test_case.metadata['reasoning']
            claim = test_case.input
            verdict = test_case.actual_output
            
            # Use LLM to score reasoning
            prompt = f"""
            Evaluate the quality of this reasoning for a BS detection task.
            
            Claim: {claim}
            Verdict: {verdict}
            Reasoning: {reasoning}
            
            Score from 0-1 based on:
            - Relevance to the claim
            - Logical consistency
            - Use of aviation knowledge
            - Clarity of explanation
            
            Return only a number between 0 and 1.
            """
            
            try:
                response = self.llm.invoke(prompt)
                self.score = float(response.content.strip())
            except:
                self.score = 0.5  # Default if evaluation fails
        else:
            self.score = 0.0
            
        self.success = self.score >= self.threshold
        return self.score
    
    def is_successful(self):
        return self.success
    
    @property
    def reason(self):
        return f"Reasoning quality score: {self.score:.2f}"


# Evaluation Framework
class BSDetectorEvaluator:
    """Evaluates BS detector performance across iterations"""
    
    def __init__(self, dataset_path: str = "data/aviation_claims_dataset.json"):
        self.dataset_path = Path(dataset_path)
        self.claims = self._load_dataset()
        self.results = {}
    
    def _load_dataset(self) -> List[AviationClaim]:
        """Load aviation claims dataset"""
        with open(self.dataset_path, 'r') as f:
            data = json.load(f)
        
        claims = []
        for claim_data in data['claims']:
            claims.append(AviationClaim(**claim_data))
        
        return claims
    
    def evaluate_detector(
        self, 
        detector_func: Callable, 
        iteration_name: str,
        subset: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate a detector function on the dataset"""
        import time
        
        # Filter claims if subset specified
        test_claims = self.claims
        if subset:
            test_claims = [c for c in self.claims if c.difficulty == subset]
        
        # Track results
        results = []
        total_time = 0
        
        print(f"\n🔬 Evaluating {iteration_name}...")
        print(f"Testing on {len(test_claims)} claims")
        
        for claim in test_claims:
            start_time = time.time()
            
            try:
                # Get detector result
                if "graph" in detector_func.__name__:
                    result = detector_func(claim.claim)
                else:
                    # Baseline needs LLM
                    llm = LLMFactory.create_llm()
                    result = detector_func(claim.claim, llm)
                
                # Record time
                elapsed = time.time() - start_time
                total_time += elapsed
                
                # Extract verdict and confidence
                verdict = result.get('verdict', 'ERROR')
                confidence = result.get('confidence', 0)
                reasoning = result.get('reasoning', '')
                
                # Check if correct
                is_correct = verdict == claim.verdict
                
                # Store result
                results.append({
                    'claim_id': claim.id,
                    'claim': claim.claim,
                    'expected': claim.verdict,
                    'predicted': verdict,
                    'correct': is_correct,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'difficulty': claim.difficulty,
                    'category': claim.category,
                    'response_time': elapsed
                })
                
                # Progress indicator
                if len(results) % 10 == 0:
                    print(f"  Processed {len(results)}/{len(test_claims)} claims...")
                    
            except Exception as e:
                print(f"  Error on claim {claim.id}: {e}")
                results.append({
                    'claim_id': claim.id,
                    'claim': claim.claim,
                    'expected': claim.verdict,
                    'predicted': 'ERROR',
                    'correct': False,
                    'confidence': 0,
                    'reasoning': str(e),
                    'difficulty': claim.difficulty,
                    'category': claim.category,
                    'response_time': 0
                })
        
        # Calculate metrics
        df = pd.DataFrame(results)
        
        # Overall accuracy
        accuracy = df['correct'].mean()
        
        # Accuracy by difficulty
        easy_acc = df[df['difficulty'] == 'easy']['correct'].mean()
        medium_acc = df[df['difficulty'] == 'medium']['correct'].mean()
        hard_acc = df[df['difficulty'] == 'hard']['correct'].mean()
        
        # Accuracy by category
        category_acc = {}
        for cat in df['category'].unique():
            category_acc[cat] = df[df['category'] == cat]['correct'].mean()
        
        # Confidence analysis
        avg_conf = df['confidence'].mean()
        correct_df = df[df['correct'] == True]
        wrong_df = df[df['correct'] == False]
        
        avg_conf_correct = correct_df['confidence'].mean() if len(correct_df) > 0 else 0
        avg_conf_wrong = wrong_df['confidence'].mean() if len(wrong_df) > 0 else 0
        
        # Create evaluation result
        eval_result = EvaluationResult(
            iteration=iteration_name,
            total_claims=len(results),
            correct=df['correct'].sum(),
            accuracy=accuracy,
            easy_accuracy=easy_acc,
            medium_accuracy=medium_acc,
            hard_accuracy=hard_acc,
            category_accuracy=category_acc,
            avg_confidence=avg_conf,
            avg_confidence_when_correct=avg_conf_correct,
            avg_confidence_when_wrong=avg_conf_wrong,
            avg_response_time=total_time / len(results),
            claim_results=results
        )
        
        # Store result
        self.results[iteration_name] = eval_result
        
        # Print summary
        print(f"\n✅ {iteration_name} Results:")
        print(f"  Overall Accuracy: {accuracy:.1%}")
        print(f"  Easy: {easy_acc:.1%}, Medium: {medium_acc:.1%}, Hard: {hard_acc:.1%}")
        print(f"  Avg Confidence: {avg_conf:.1f}% (Correct: {avg_conf_correct:.1f}%, Wrong: {avg_conf_wrong:.1f}%)")
        print(f"  Avg Response Time: {eval_result.avg_response_time:.2f}s")
        
        return eval_result
    
    def run_deepeval_tests(self, detector_func: Callable, iteration_name: str):
        """Run DeepEval test cases"""
        print(f"\n🧪 Running DeepEval tests for {iteration_name}...")
        
        # Create test cases
        test_cases = []
        
        # Sample subset for DeepEval (to save time/cost)
        sample_ids = ['easy_001', 'easy_002', 'medium_001', 'hard_001', 'misleading_001']
        sample_claims = [
            c for c in self.claims 
            if c.id in sample_ids
        ]
        
        # If no specific IDs found, take first 5 claims
        if not sample_claims:
            sample_claims = self.claims[:5]
        
        for claim in sample_claims:
            # Get detector result
            if "graph" in detector_func.__name__:
                result = detector_func(claim.claim)
            else:
                llm = LLMFactory.create_llm()
                result = detector_func(claim.claim, llm)
            
            # Create test case (store metadata separately)
            test_case = LLMTestCase(
                input=claim.claim,
                actual_output=result.get('verdict', 'ERROR'),
                expected_output=claim.verdict
            )
            # Add metadata as attributes
            test_case.metadata = {
                'confidence': result.get('confidence', 0),
                'reasoning': result.get('reasoning', ''),
                'difficulty': claim.difficulty
            }
            test_cases.append(test_case)
        
        # Run metrics
        metrics = [
            BSDetectionAccuracy(),
            ConfidenceCalibration(),
            ReasoningQuality()
        ]
        
        passed = 0
        for i, test_case in enumerate(test_cases):
            print(f"\nTest Case {i+1}: {test_case.input[:50]}...")
            
            for metric in metrics:
                score = metric.measure(test_case)
                print(f"  {metric.name}: {score:.2f} - {'✅ PASS' if metric.is_successful() else '❌ FAIL'}")
                if metric.is_successful():
                    passed += 1
        
        total_tests = len(test_cases) * len(metrics)
        if total_tests > 0:
            print(f"\n📊 DeepEval Summary: {passed}/{total_tests} tests passed ({passed/total_tests:.1%})")
        else:
            print("\n📊 DeepEval Summary: No tests to run")
    
    def compare_iterations(self):
        """Compare results across iterations"""
        if len(self.results) < 2:
            print("Need at least 2 iterations to compare")
            return
        
        print("\n📈 Iteration Comparison:")
        print("-" * 60)
        
        # Create comparison table
        rows = []
        for name, result in self.results.items():
            rows.append({
                'Iteration': name,
                'Accuracy': f"{result.accuracy:.1%}",
                'Easy': f"{result.easy_accuracy:.1%}",
                'Medium': f"{result.medium_accuracy:.1%}",
                'Hard': f"{result.hard_accuracy:.1%}",
                'Avg Confidence': f"{result.avg_confidence:.1f}%",
                'Response Time': f"{result.avg_response_time:.2f}s"
            })
        
        df = pd.DataFrame(rows)
        print(df.to_string(index=False))
        
        # Calculate improvements
        iterations = list(self.results.keys())
        if len(iterations) >= 2:
            base = self.results[iterations[0]]
            latest = self.results[iterations[-1]]
            
            improvement = latest.accuracy - base.accuracy
            print(f"\n🎯 Improvement: {improvement:.1%} "
                  f"({base.accuracy:.1%} → {latest.accuracy:.1%})")


# Convenience functions
def evaluate_baseline():
    """Evaluate the baseline detector"""
    # Try to find the dataset in common locations
    import os
    if os.path.exists("../data/aviation_claims_dataset.json"):
        dataset_path = "../data/aviation_claims_dataset.json"
    elif os.path.exists("data/aviation_claims_dataset.json"):
        dataset_path = "data/aviation_claims_dataset.json"
    else:
        dataset_path = str(Path(__file__).parent.parent / "data" / "aviation_claims_dataset.json")
    
    evaluator = BSDetectorEvaluator(dataset_path)
    return evaluator.evaluate_detector(check_claim, "Iteration 1: Baseline")


def evaluate_langgraph():
    """Evaluate the LangGraph detector"""
    # Try to find the dataset in common locations
    import os
    if os.path.exists("../data/aviation_claims_dataset.json"):
        dataset_path = "../data/aviation_claims_dataset.json"
    elif os.path.exists("data/aviation_claims_dataset.json"):
        dataset_path = "data/aviation_claims_dataset.json"
    else:
        dataset_path = str(Path(__file__).parent.parent / "data" / "aviation_claims_dataset.json")
    
    evaluator = BSDetectorEvaluator(dataset_path)
    return evaluator.evaluate_detector(check_claim_with_graph, "Iteration 2: LangGraph")


def compare_all_iterations():
    """Run full comparison"""
    # Try to find the dataset in common locations
    import os
    if os.path.exists("../data/aviation_claims_dataset.json"):
        dataset_path = "../data/aviation_claims_dataset.json"
    elif os.path.exists("data/aviation_claims_dataset.json"):
        dataset_path = "data/aviation_claims_dataset.json"
    else:
        dataset_path = str(Path(__file__).parent.parent / "data" / "aviation_claims_dataset.json")
    
    evaluator = BSDetectorEvaluator(dataset_path)
    
    # Evaluate each iteration
    evaluator.evaluate_detector(check_claim, "Iteration 1: Baseline")
    evaluator.evaluate_detector(check_claim_with_graph, "Iteration 2: LangGraph")
    
    # Compare results
    evaluator.compare_iterations()
    
    # Run DeepEval tests on latest
    evaluator.run_deepeval_tests(check_claim_with_graph, "Iteration 2: LangGraph")


# Demo and testing
if __name__ == "__main__":
    print("=" * 60)
    print("BS Detector Evaluation Framework")
    print("=" * 60)
    
    # Quick test on easy claims only
    evaluator = BSDetectorEvaluator()
    evaluator.evaluate_detector(check_claim, "Baseline (Easy)", subset="easy")
    evaluator.evaluate_detector(check_claim_with_graph, "LangGraph (Easy)", subset="easy")
    
    print("\n" + "=" * 60)
    print("Run compare_all_iterations() for full evaluation")