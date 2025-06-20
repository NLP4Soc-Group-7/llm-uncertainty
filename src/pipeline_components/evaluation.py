import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss
import uncertainty_toolbox as uct

class UncertaintyEvaluator:
    """
    A class for evaluating uncertainty estimates in classification predictions.

    This class takes predictions, uncertainty estimates, and ground truth labels
    and computes various uncertainty evaluation metrics using uncertainty_toolbox
    and custom metrics like AUROC for uncertainty-error correlation.

    Attributes:
        predictions (np.ndarray): Model predictions
        uncertainties (np.ndarray): Uncertainty estimates for each prediction
        labels (np.ndarray): Ground truth labels
    """

    def __init__(self, predictions, uncertainties, labels):
        """
        Initialize the UncertaintyEvaluator.

        Args:
            predictions: Model predictions
            uncertainties: Uncertainty estimates for each prediction
            labels: Ground truth labels
        """
        self.predictions = predictions
        self.uncertainties = uncertainties
        self.labels = labels

    @classmethod
    def from_arrays(cls, predictions: np.ndarray, uncertainties: np.ndarray, labels: np.ndarray):
        """
        Initialize directly from numpy arrays.

        Args:
            predictions (np.ndarray): Model predictions
            uncertainties (np.ndarray): Uncertainty estimates
            labels (np.ndarray): Ground truth labels

        Returns:
            UncertaintyEvaluator: New evaluator instance
        """
        return cls(predictions=predictions,
                  uncertainties=uncertainties,
                  labels=labels)

    @classmethod
    def from_json(cls, json_path: str):
        """
        Initialize from a JSON file containing predictions, uncertainties and labels.

        Args:
            json_path (str): Path to JSON file containing the data

        Returns:
            UncertaintyEvaluator: New evaluator instance
        """
        with open(json_path, 'r') as f:
            data = json.load(f)
        # Ensure data from JSON is also converted to numpy arrays if they are expected to be
        return cls(
            predictions=np.array(data['predictions']),
            uncertainties=np.array(data['uncertainties']),
            labels=np.array(data['labels'])
        )

    def uncertainty_evaluation_of_std_deviation_prediction(self):
        """
        Calculate uncertainty metrics using uncertainty_toolbox.

        Returns:
            dict: Dictionary containing various uncertainty metrics
        """
        # Get metrics from uncertainty_toolbox
        # Setting verbose to False from uct.metrics.get_all_metrics
        # as the printing is extensive
        metrics = uct.metrics.get_all_metrics(
            self.predictions,
            self.uncertainties,
            self.labels,
            verbose=False  # Set to True if you want uct to print its detailed output
        )

        # Convert numpy types in metrics to JSON serializable types
        metrics_serializable = self._make_serializable_recursive(metrics)

        return metrics_serializable  # Return the serializable version

    def correctness_uncertainty_auroc(self, top_k: int = None, bottom_k: int = None):

        if top_k is not None and bottom_k is not None:
            print("You cannot set both top_k and bottom_k")
            return

        elif top_k is not None:
            top_k_indices = np.argsort(self.uncertainties)[-top_k:]
            is_incorrect = (self.predictions[top_k_indices] != self.labels[top_k_indices]).astype(int)
            uncertainties = self.uncertainties[top_k_indices]
        elif bottom_k is not None:
            bottom_k_indices = np.argsort(self.uncertainties)[:bottom_k]
            is_incorrect = (self.predictions[bottom_k_indices] != self.labels[bottom_k_indices]).astype(int)
            uncertainties = self.uncertainties[bottom_k_indices]
        else:
            is_incorrect = (self.predictions != self.labels).astype(int)
            uncertainties = self.uncertainties

        return roc_auc_score(is_incorrect, uncertainties)

    def brier_score(self, top_k: int = None, bottom_k: int = None):
        if top_k is not None and bottom_k is not None:
            print("You cannot set both top_k and bottom_k")
            return
        elif top_k is not None:
            top_k_indices = np.argsort(self.uncertainties)[-top_k:]
            labels = self.labels[top_k_indices]
            uncertainties = self.uncertainties[top_k_indices]
        elif bottom_k is not None:
            bottom_k_indices = np.argsort(self.uncertainties)[:bottom_k]
            labels = self.labels[bottom_k_indices]
            uncertainties = self.uncertainties[bottom_k_indices]
        else:
            labels = self.labels
            uncertainties = self.uncertainties

        return brier_score_loss(labels, uncertainties)

    def evaluate(self):
        """
        Run full evaluation.

        Computes all uncertainty metrics.

        Returns:
            dict: Dictionary containing all computed metrics
        """
        metrics = {}

        metrics['uncertainty_toolbox_metrics'] = self.uncertainty_evaluation_of_std_deviation_prediction()
        auroc = self.correctness_uncertainty_auroc()
        # Add auroc to metrics
        metrics['auroc'] = float(auroc)

        return metrics

    def _make_serializable_recursive(self, item):
        if isinstance(item, np.ndarray):
            return item.tolist()
        elif isinstance(item, (np.float16, np.float32, np.float64)):
            return float(item)
        elif isinstance(item, (np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(item)
        elif isinstance(item, dict):
            return {key: self._make_serializable_recursive(value) for key, value in item.items()}
        elif isinstance(item, (list, tuple)):
            return [self._make_serializable_recursive(element) for element in item]
        else:
            return item


if __name__ == "__main__":
    predictions = np.array([1, 0, 1, 0, 0])
    uncertainties = np.array([0.8, 0.1, 0.5, 0.2, 0.5])
    labels = np.array([1, 0, 1, 0, 1])

    evaluator = UncertaintyEvaluator.from_arrays(predictions, uncertainties, labels)
    metrics = evaluator.evaluate()
    print(metrics)