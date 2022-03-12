import json
from collections import defaultdict

with open("results_12_mar.json") as file_json:
    data = json.load(file_json)

success_rates = defaultdict(list)
nav_errors = defaultdict(list)
spls = defaultdict(list)
path_lengths = defaultdict(list)

for record in data:
  model = record['model']
  success_rates[model].append(int(record['success']))
  nav_errors[model].append(record['navigation_error'])
  spls[model].append(record['success_path_length'])
  path_lengths[model].append(record['path_length'])

models = list(success_rates.keys())
for model in models:
  print(model)
  records_of_model_length = len(path_lengths[model])

  print(f"N {records_of_model_length}")
  print(f"TL {round(sum(path_lengths[model]) / records_of_model_length, 2)}")
  print(f"SR {round(sum(success_rates[model]) / records_of_model_length, 2)}")
  print(f"NE {round(sum(nav_errors[model]) / records_of_model_length, 2)}")
  print(f"SPL {round(sum(spls[model]) / records_of_model_length, 2)}")
  print()
