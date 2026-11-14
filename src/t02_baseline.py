"""Required T02 baseline: one global Laplacian threshold, same review budget."""
from .pipeline import run_pipeline


def run(ctx):
    run_pipeline(ctx, baseline=True)
