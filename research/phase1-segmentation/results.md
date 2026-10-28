Model: `facebook/sam2.1-hiera-tiny`

| House | Surface | Prompt | IoU vs rendered mask | IoU vs outline | Model confidence | Seconds |
|---|---|---|---|---|---|---|
| Brick house | Walls | 1 point | 0.413 | 0.409 | 0.003 | 1.7 |
| Brick house | Walls | 3 points | 0.479 | 0.457 | 0.645 | 1.8 |
| Brick house | Walls | box | 0.510 | 0.485 | 0.859 | 1.8 |
| Brick house | Path | 1 point | 0.878 | 0.876 | 0.975 | 2.0 |
| Brick house | Path | 3 points | 0.898 | 0.888 | 0.912 | 1.9 |
| Brick house | Path | box | 0.887 | 0.887 | 0.968 | 1.9 |
| Old rectory | Walls | 1 point | 0.329 | 0.298 | 0.836 | 1.8 |
| Old rectory | Walls | 3 points | 0.321 | 0.307 | 0.875 | 1.8 |
| Old rectory | Walls | box | 0.395 | 0.412 | 0.839 | 1.8 |
| New cottage | Walls | 1 point | 0.395 | 0.373 | 0.888 | 1.9 |
| New cottage | Walls | 3 points | 0.645 | 0.583 | 0.584 | 1.9 |
| New cottage | Walls | box | 0.465 | 0.423 | 0.867 | 1.9 |
| New cottage | Path | 1 point | 0.904 | 0.894 | 0.874 | 2.0 |
| New cottage | Path | 3 points | 0.907 | 0.897 | 0.922 | 1.9 |
| New cottage | Path | box | 0.916 | 0.906 | 0.981 | 1.9 |
| Prairie house | Lower walls | 1 point | 0.295 | 0.295 | 0.348 | 1.8 |
| Prairie house | Lower walls | 3 points | 0.374 | 0.374 | 0.626 | 1.9 |
| Prairie house | Lower walls | box | 0.423 | 0.423 | 0.764 | 2.0 |
| **mean** | | **1 point** | **0.536** | **0.524** | | **1.9** |
| **mean** | | **3 points** | **0.604** | **0.584** | | **1.9** |
| **mean** | | **box** | **0.599** | **0.589** | | **1.9** |
