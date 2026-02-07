# Scikit-learn Integration & Model Selection Reference

## TransformerBasis

Convert NeMoS basis objects to scikit-learn-compatible transformers:

```python
basis = nmo.basis.MSplineEval(n_basis_funcs=10, label="position")

# Convert to transformer
transformer_basis = basis.to_transformer()

# Now has .transform() method (equivalent to .compute_features())
X = transformer_basis.transform(input_data)
```

### Input Shape for Transformers

Transformers only accept 2D inputs. For single features, ensure shape is `(n_samples, 1)`:

```python
# Single feature - stack into 2D
X_input = np.expand_dims(position.values, axis=1)
X = transformer_basis.transform(X_input)
```

### Multi-Component Transformers

For composed bases (additive), concatenate all inputs into one 2D array:

```python
position_basis = nmo.basis.MSplineEval(n_basis_funcs=10, label="position")
speed_basis = nmo.basis.MSplineEval(n_basis_funcs=15, label="speed")
basis = position_basis + speed_basis
basis = basis.to_transformer()

# Stack inputs into single 2D array
transformer_input = nap.TsdFrame(
    t=position.t,
    d=np.stack([position, speed]).T,
    time_support=position.time_support,
    columns=["position", "speed"],
)

X = basis.transform(transformer_input)
```

### Setting Input Shape for Non-Default Splits

If components process multiple columns, use `set_input_shape`:

```python
# Tell basis how many columns each component gets
basis.set_input_shape(2, 3)  # first component: 2 cols, second: 3 cols
# Or pass arrays directly
basis.set_input_shape(x_array, y_array)
```

## Pipelines

Combine basis transformation and GLM into a single estimator:

```python
from sklearn.pipeline import Pipeline

glm = nmo.glm.PopulationGLM(
    regularizer="Ridge",
    regularizer_strength=0.1,
    solver_name="LBFGS",
    solver_kwargs={"tol": 1e-12}
)

pipe = Pipeline([
    ("basis", basis.to_transformer()),
    ("glm", glm),
])

# Fit and predict in one step
pipe.fit(transformer_input, count)
predicted = pipe.predict(transformer_input)
```

## Cross-Validation for Regularization Strength

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "regularizer_strength": [1e-6, 1e-4, 1e-2, 1e-1, 1, 10],
}

glm = nmo.glm.PopulationGLM(
    regularizer="Ridge",
    solver_name="LBFGS",
    solver_kwargs={"tol": 1e-12}
)

cv = GridSearchCV(glm, param_grid, cv=5)
cv.fit(X, count)

# Results
import pandas as pd
print(pd.DataFrame(cv.cv_results_))
print(f"Best strength: {cv.best_params_}")
print(f"Best score: {cv.best_score_}")
```

## Cross-Validation for Basis Selection

Use pipelines to cross-validate over basis parameters:

```python
pipe = Pipeline([
    ("basis", basis.to_transformer()),
    ("glm", nmo.glm.PopulationGLM(
        regularizer="Ridge",
        regularizer_strength=0.1,
        solver_name="LBFGS"
    )),
])

# Cross-validate over number of basis functions
# Use __ to access nested parameters:
# "basis__position__n_basis_funcs" means pipe["basis"]["position"].n_basis_funcs
param_grid = {
    "basis__position__n_basis_funcs": [5, 10, 15, 20],
    "basis__speed": [
        nmo.basis.MSplineEval(n_basis_funcs=10, label="speed"),
        nmo.basis.BSplineEval(n_basis_funcs=10, label="speed"),
    ],
}

cv = GridSearchCV(pipe, param_grid, cv=5)
cv.fit(transformer_input, count)

# Access best estimator
best_model = cv.best_estimator_
predictions = best_model.predict(transformer_input)
```

### Pipeline Parameter Access

```python
# Access nested components
pipe["basis"]                           # the TransformerBasis
pipe["basis"]["position"]               # position sub-basis
pipe["basis"]["position"].n_basis_funcs # specific attribute

# In param_grid, use __ for nesting:
# pipe["basis"]["position"].n_basis_funcs -> "basis__position__n_basis_funcs"
```

## Feature Selection with Null Basis

Compare models with different feature subsets using a "null" basis that produces zero features:

```python
from nemos.basis import CustomBasis

# Create a null basis that outputs empty features
def zero_func(x):
    return np.zeros((x.shape[0], 0))

null_basis = CustomBasis(func=zero_func, n_output_features=0)
null_basis = null_basis.to_transformer()

# Define three models using the same input structure:
# Position + Speed
basis_all = position_basis + speed_basis
basis_all.label = "position + speed"

# Position only (null speed)
basis_pos_only = position_basis + null_basis
basis_pos_only.label = "position only"

# Speed only (null position)
basis_speed_only = null_basis + speed_basis
basis_speed_only.label = "speed only"

# Cross-validate to compare
param_grid = {
    "basis__basis": [basis_all, basis_pos_only, basis_speed_only],
}

# Note: "basis__basis" - first "basis" is the pipeline step name,
# second "basis" is the attribute of TransformerBasis

cv = GridSearchCV(pipe, param_grid, cv=5)
cv.fit(transformer_input, count)

# Compare results
cv_df = pd.DataFrame(cv.cv_results_)
print(cv_df[["param_basis__basis", "mean_test_score", "rank_test_score"]])
```

## Combined Cross-Validation

Search over regularization, basis type, and features simultaneously:

```python
param_grid = {
    "glm__regularizer_strength": [0.01, 0.1, 1.0],
    "basis__position__n_basis_funcs": [5, 10, 20],
    "basis__speed__n_basis_funcs": [5, 10],
}

cv = GridSearchCV(pipe, param_grid, cv=5)
cv.fit(transformer_input, count)

print(f"Best params: {cv.best_params_}")
best_model = cv.best_estimator_
```

## Practical Tips

1. **Start simple**: Fit without regularization first, then add Ridge
2. **Check for overfitting**: Compare train/test scores - large gap suggests overfitting
3. **Temporal CV**: For time series, don't shuffle folds (use `KFold(shuffle=False)`)
4. **Feature importance**: Use null basis feature selection to determine which predictors matter
5. **Pipeline convenience**: Pipelines ensure basis + GLM parameters are always consistent
