# Data folder

Place the IBM HR Analytics Employee Attrition & Performance CSV here as:

`WA_Fn-UseC_-HR-Employee-Attrition.csv`

The project can also run without this file. In that case `scripts/generate_data.py` creates a compatible 1,470-row seed internally and scales it with Faker.

Generated files are written to `data/generated/` and are ignored by Git because they can be large.
