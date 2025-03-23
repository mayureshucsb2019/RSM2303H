from trading_strategies.strategy.strategy_utility import get_env_variable
import numpy as np
from cvxopt import matrix, solvers
from scipy.stats import norm
from trading_strategies.logger_config import setup_logger

logger = setup_logger(__name__)

def parse_var_env_variables():
    """Parses and returns Var strategy-specific environment variables."""
    return {
        "auth": {
            "username": get_env_variable("USERNAME", str, True),
            "password": get_env_variable("PASSWORD", str, True),
            "server": get_env_variable("SERVER", str, True),
            "port": get_env_variable("VAR_PORT", str, True),
        }
    }

def variance_covariance_matrix(volatilities, correlation_matrix):
    """
    Computes the variance-covariance matrix from a given volatility vector and correlation matrix.
    
    Parameters:
    volatilities (np.array): A 1D array containing asset volatilities (standard deviations).
    correlation_matrix (np.array): A 2D array representing the correlation matrix.
    
    Returns:
    np.array: The variance-covariance matrix.
    """
    vol_matrix = np.diag(volatilities)
    return vol_matrix @ correlation_matrix @ vol_matrix

def calculate_var(volatilities, correlation_matrix, portfolio_weights, portfolio_value, confidence_level=0.95):
    """
    Calculates the Value at Risk (VaR) using the Variance-Covariance method.
    
    Parameters:
    volatilities (np.array): 1D array of asset volatilities (standard deviations).
    correlation_matrix (np.array): 2D correlation matrix.
    portfolio_weights (np.array): 1D array of asset weights in the portfolio.
    portfolio_value (float): Total value of the portfolio.
    confidence_level (float): Confidence level for VaR (default: 95%).
    
    Returns:
    float: Value at Risk (VaR) in monetary terms.
    """
    # Compute variance-covariance matrix
    var_cov_matrix = variance_covariance_matrix(volatilities, correlation_matrix)

    # Portfolio variance and standard deviation
    portfolio_variance = portfolio_weights.T @ var_cov_matrix @ portfolio_weights
    portfolio_std_dev = np.sqrt(portfolio_variance)

    # Compute Z-score dynamically for given confidence level
    z_score = norm.ppf(confidence_level)

    # Compute VaR
    var_value = z_score * portfolio_std_dev * portfolio_value
    return var_value

def calculate_units(price_per_unit:  float, volatility: float, VaR_limit: int = 20000, z_score=2.33):
    """
    Calculate the number of units of a given asset (US) to keep Value at Risk (VaR) under a specified limit.

    Parameters:
    - VaR_limit (float): The maximum allowed Value at Risk (VaR).
    - price_per_unit (float): The price per unit of the asset (US).
    - volatility (float): Volatility of the asset in decimal form (e.g., 1.31% as 0.0131).
    - z_score (float): The z-score corresponding to the desired confidence level (default is 2.33 for 99%).

    Returns:
    - number_of_units (float): The number of units to buy.
    """

    return int(VaR_limit / (volatility * z_score * price_per_unit))

def optimize_portfolio(current_prices, expected_prices, volatilities, correlation_matrix, total_capital=1000000):
    # Calculate expected returns (percentage change)
    expected_returns = np.array([
        (expected_prices['US'] - current_prices['US']) / current_prices['US'],
        (expected_prices['BRIC'] - current_prices['BRIC']) / current_prices['BRIC'],
        (expected_prices['BOND'] - current_prices['BOND']) / current_prices['BOND']
    ])
    print("###########################################")
    print("Expected returns:", expected_returns)
    
    # Covariance matrix based on volatilities and correlation
    cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix
    print("###########################################")
    print("Covariance Matrix:", cov_matrix)

    # Number of assets (excluding cash)
    n_assets = 3

    # Prepare matrices for the optimization
    P = matrix(cov_matrix)  # Covariance matrix
    q = matrix(np.zeros(n_assets))  # Linear term (no linear objective)
    print("Matrix P ###########################################")
    print(P)
    print("Matrix q ###########################################")
    print(q)

    # Constraints (weights must sum to 1)
    G = np.ones((1, n_assets))  # Row vector of ones
    G = matrix(G)  # Convert to matrix for solver
    h = matrix(np.array([1.0]))  # Ensure h is a column matrix (shape (1,1))

    print("Matrix G ###########################################")
    print(G)
    print("Matrix h ###########################################")
    print(h)

    # Solve the optimization problem with a KKT solver explicitly
    sol = solvers.qp(P, q, G, h, solver='cvxopt')
    print("sol ###########################################")
    print(sol)

    # Extract the optimal weights
    weights = np.array(sol['x'])
    print("weights ###########################################")
    print(weights)

    # Calculate portfolio value in each asset based on the weights
    asset_values = weights * total_capital  # Amounts to be invested in each asset
    print("asset values ###########################################")
    print(asset_values)

    # Prepare the result in dictionary format for easy readability
    asset_names = ['US', 'BRIC', 'BOND']
    result = {asset_names[i]: asset_values[i][0] for i in range(n_assets)}
    print("###########################################")
    print(result)
    print("###########################################")

    return result