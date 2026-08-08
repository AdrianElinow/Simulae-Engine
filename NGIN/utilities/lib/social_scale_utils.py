

from pprint import pprint
import random
from .ngin_utils import logAll, logWarning

def generate_values_for_scales(
    scales: dict[str, list[str]] | None,
    scale_strength_range: list[int] | None = None, 
    std_dev: float | None = None, 
    std_dev_variance: float = 1, 
    use_rng: bool = False) -> dict:
    '''
    Generates random values for each scale in the given scales dict, using a bell curve distribution centered on the middle of each scale list.
    
    :param self: Description
    :param scales: Description
    :type scales: dict
    :param std_dev: Description
    :type std_dev: float | None
    :param std_dev_variance: Description
    :type std_dev_variance: float
    :param scale_strength_range: Description
    :type scale_strength_range: list[int]
    :param use_rng: Description
    :type use_rng: bool
    :return: Description
    :rtype: dict[Any, Any]
    '''
    
    logAll("generate_values_for_scales(",scales,")")

    if not scales:
        raise ValueError("Scales definition is required to generate values for scales")

    if not scale_strength_range:
        scale_strength_range = [0, 10] # default strength range if not provided

    values = {}
    rng = random.Random(random.getrandbits(64)) if use_rng else None

    # Random values along bell curve adjusted for given scale
    for key in scales.keys():
        selection_index = get_bellcurve_value_for_scale(scales[key], std_dev, std_dev_variance, rng)
        strength = random.randrange(scale_strength_range[0], scale_strength_range[1]) if not rng else rng.randrange(scale_strength_range[0], scale_strength_range[1])
        values[key] = selection_index, strength # belief & belief strength

    return values

def get_scale_diff( master_scale: dict[str, list[str]], 
               scale: dict[str, tuple[int, int]], 
               comparison_scale: dict[str, tuple[int, int]], 
               descriptors: list[str], 
               descriptors_buckets: list[int], 
               scale_center_index: int = 3):
    '''
    Calculate the difference between two scales, returning a total delta value and a summary of the differences for each factor.
    
    :param master_scale: Description
    :type master_scale: dict[str, list[str]]
    :param scale: Description
    :type scale: dict[str, tuple[int, int]]
    :param comparison_scale: Description
    :param descriptors: Description
    :type descriptors: list[str]
    :param descriptors_buckets: Description
    :type descriptors_buckets: list[int]
    :param scale_center_index: Description
    :type scale_center_index: int
    '''
    
    logAll("scale_diff(",master_scale, scale, comparison_scale, descriptors, descriptors_buckets, scale_center_index,")")

    diff_summary = {}
    diff = 0

    for factor in master_scale.keys():
        if factor not in scale or factor not in comparison_scale:
            logWarning("Unable to perform full comparison. Scale factor",factor,"not in both given scales.")
            continue

        scale_factor = scale[factor]
        comparison_scale_factor = comparison_scale[factor]

        delta = get_scale_factor_diff( scale_factor, comparison_scale_factor, scale_center_index)

        summary = ""
        if descriptors and factor in descriptors and delta is not None:
            bucket_index = bucket_delta(delta, descriptors_buckets)
            summary = descriptors[bucket_index]

        diff_summary[factor] = summary
        diff += delta

    return diff, diff_summary


def get_scale_factor(scales, scale, key: str) -> tuple[int, int] | None:
    logAll("get_scale_factor(",scale,", ",key,")")

    if scale not in scales:
        logWarning(f"Scale '{scale}' not found in node scales")
        return None

    if key not in scales[scale]:
        logWarning(f"Key '{key}' not found in scale '{scale}'")
        return None
    
    if scale not in scales or key not in scales[scale]:
        logWarning(f"Scale '{scale}' or key '{key}' not found in scales")
        return None

    return scales[scale][key] # returns tuple (index, strength)

def get_scale_index(scales, scale, key: str) -> int | None:
    logAll("get_scale_index(",scale,", ",key,")")

    factor = get_scale_factor(scales, scale, key)

    if not factor:
        logWarning(f"Scale factor for scale '{scale}' and key '{key}' is None or empty")
        return None

    return factor[0] # index is first element of tuple (index, strength)

def get_scale_factor_value(index: int, strength: int, center_index: int) -> int:
    '''
    Calculate a scale factor value based on the given index, strength, and center index. The value is determined by the distance of the index from the center index, multiplied by the strength. If the index is equal to the center index, the value is 0.
    
    :param index: Description
    :type index: int
    :param strength: Description
    :type strength: int
    :param center_index: Description
    :type center_index: int
    :return: Description
    :rtype: int
    '''

    sign = index - center_index

    if sign == 0:
        return 0
    
    return sign * strength
    
def get_scale_factor_diff( 
        scale_factor: tuple, 
        compare_scale_factor: tuple, 
        scale_center_index: int = 3):
    '''
    Determine the difference between two scale factors, returning a delta value and a descriptor of the difference.
    
    :param scale_factor: Description
    :type scale_factor: tuple
    :param compare_scale_factor: Description
    :type compare_scale_factor: tuple
    :param descriptors: Description
    :type descriptors: list[str]
    :param descriptors_buckets: Description
    :type descriptors_buckets: list[int]
    :param scale_center_index: Description
    :type scale_center_index: int
    '''
    
    logAll("get_scale_factor_diff(",scale_factor, compare_scale_factor,")")

    summary = {}
    diff = 0

    factor_index, factor_strength = scale_factor
    compare_factor_index, compare_factor_strength = compare_scale_factor

    factor_value            = get_scale_factor_value(factor_index, factor_strength, scale_center_index)
    compare_factor_value    = get_scale_factor_value(compare_factor_index, compare_factor_strength, scale_center_index)
    delta = abs(factor_value - compare_factor_value)

    return delta

def get_bellcurve_value_for_scale(  scale_list: list, 
                                    std_dev: float | None,
                                    std_deviation_frac: float = 1, 
                                    rng: random.Random | None = None) -> int:
    logAll("get_bellcurve_value_for_scale(",scale_list,")")
    ''' get_bellcurve_value_for_scale(scale_list) returns an index into the given scale_list
        using a bell curve distribution centered on the middle of the scale_list
    '''

    if (not scale_list) or (len(scale_list) == 0):
        raise ValueError("Scale list is empty")
    elif len(scale_list) == 1:
        return 0
    elif len(scale_list) % 2 == 0:
        raise ValueError("Scale list must have an odd number of elements to have a central average")

    min_index = 0
    max_index = len(scale_list) - 1
    average_index = (min_index + max_index) / 2

    value = random_bell_curve_value(min_index, max_index, average_index, std_dev, std_deviation_frac, rng)

    index = int(round(value, 0))

    return index

def random_bell_curve_value(min_val: float, max_val: float, average: float, std_dev: float | None, std_deviation_frac: float = 1, rng: random.Random | None = None) -> float:
    logAll("random_bell_curve_value(",min_val,", ",max_val,", ",average,", ",std_deviation_frac,")")
    """
    Generate a realistic random value along a bell curve (normal distribution),
    constrained within min and max, centered on average.

    Parameters:
    - min_val (float): The minimum allowed value.
    - max_val (float): The maximum allowed value.
    - average (float): The central mean value.
    - std_deviation_frac (float): Fraction of (max - min) to use as standard deviation.
                             Default is 15% for moderate variance.

    Returns:
    - float: Random value distributed normally, clipped to [min_val, max_val].
    """

    if rng is None:
        rng = random.Random()

    if std_dev is None:
        if std_deviation_frac is not None:
            std_dev = (max_val - min_val) * std_deviation_frac
        
        # std_dev is None
        logAll("std_dev is None, defaulting to 15% of range for moderate variance")
        std_dev = (max_val - min_val) * 0.15

    # Generate values until one falls within range (clipping is optional but can bias the curve)
    while True:
        value = rng.gauss(average, std_dev)
        if min_val <= value <= max_val:
            return round(value, 2)
        
def bucket_delta(value: int, buckets: list[int]) -> int:
    '''
    bucket_delta(value, buckets) returns the index of the bucket that given value falls into
    
    :param value: Description
    :type value: int
    :param buckets: Description
    :type buckets: list[int]
    :return: Description
    :rtype: int
    '''

    if value == None: 
        raise ValueError("'value' cannot be None")

    if not buckets:
        raise ValueError("'buckets' cannot be None or empty list")

    for i, b in enumerate(buckets):
        if value < b:
            return i
    return len(buckets)
