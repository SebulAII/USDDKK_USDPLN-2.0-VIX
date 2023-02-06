import optuna
from Objective import objective

# ilość rund optymalizacji.
n_trials = 300
  
objective = objective
study = optuna.create_study()
study.optimize(objective, n_trials=n_trials)

# Drukuj najlepsze wartości parametru.
print(study.best_params)

# Alternatywnie możesz pobrać dataframe z wynikami wszystkich eksperymentów.
results_df = study.trials_dataframe()
results_df.sort_values("value")
print(results_df.iloc[:5])