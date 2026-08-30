# Manim Project - Making AI & Dev accessible for all
![Manim Animation Repository](assets/Manim.png)

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](http://choosealicense.com/licenses/mit/)
[![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=flat)](https://youtube.com/channel/UC_lqYWX_kD00D7yiZcrtBng/) 

## Overview

This project is dedicated to creating animations using Manim, a mathematical engine. The main objective is to visually illustrate algorithms, statistical and AI concepts. 
The animations are created in Python, leveraging Manim's extensive capabilities to produce high-quality visuals (https://github.com/3b1b/manim)

## Video Link
- [Manim Tutorial](https://youtu.be/ZsVbCt0uT0M)
- [DFS Video - FR](https://youtu.be/prcsjvhN_c8?si=x5BY5rC3O7wk8ZSK) 
- [DFS Video - ENG](https://youtu.be/gcrqye-KYvI?si=fzHtF3jvvSbl9dQV) 
- [French Executives Salaries Evolution (1996 to 2022)](https://youtu.be/rVqmQHxI0p4) 
- [Double Pendulum animation](https://youtu.be/k4zENntIkM0) 
- [Koch Snowflake ](https://youtu.be/5fwHVGms3Zw)
- [Linear Regression Animation](https://youtu.be/P-BVVLD41NM)
- [Statistic and parametric models](https://youtu.be/gGh_hHVSbD8)
- [Gaussian Distribution Visualisation](https://youtu.be/vMAus69cC74)
- [Taylor Series](https://youtu.be/qcLvkmPo7xo)
- [KMeans Clustering](https://youtu.be/HZLAqS1Dtg8?si=SpvLudKwOLQ3VeSP)
- [Galton Board](https://www.youtube.com/watch?v=c74jckgx80g)
- [Gaussiam Mixture Model (GMM)](https://www.youtube.com/watch?v=-RZWfmYhllQ)
- [Fourier Drawing](https://youtu.be/HBkDNkCT0UY)
- [Fractal Leaf Animation](https://youtu.be/-akETcacMAw)
- [Convolutional Neural Networks](https://youtu.be/vdqbAum4fuo)
- [Transformer](https://www.youtube.com/watch?v=g5r624CfeLE)
- [Cross Validation](https://www.youtube.com/watch?v=SF5qYhyY_9A)
- [Bias-Variance Tradeoff](https://www.youtube.com/watch?v=DZYCZg3mPtc)


## Repository structure

- `animations/` — all Manim scenes
  - `2024/` — 2024 series (DFS, pendulum, Galton board, Taylor series, KMeans, GMM, …)
  - `Quant/` — quant-interview notebooks
  - `CNN/` — Convolutional Neural Network series (Parts 1–6, with voiceover)
  - `Fourier/` — Fourier-series ("epicycle") portrait drawing + theory (self-contained, see its `README.md`)
  - `conv.py` — standalone convolution scene
- `projects/` — non-Manim side projects (`RL/` pygame simulation, `Sport Tracker/`)
- `images/` — input images used by some scenes
- `assets/` — repository assets (banner)
- `docs/` — documentation

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
manim -pqh animations/2024/galton.py GaltonBoard
```

See **[docs/README.md](docs/README.md)** for the full guide: prerequisites, rendering
scenes, running the notebooks and the RL project, and the dev tooling.

## Development

```bash
pip install -r requirements-dev.txt
pre-commit install
```

Linting and formatting run automatically on every commit via **pre-commit**
(`ruff` + `isort`). Run them across the whole repo with `pre-commit run --all-files`.
