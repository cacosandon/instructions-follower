from flask import Flask, render_template, url_for, flash, request, redirect, make_response, session
import sys

IALAB_USER = 'jiossandon'

matterport_build_path = f'/home/{IALAB_USER}/datasets/Matterport3DSimulator/build'
metadata_script_path = f'/home/{IALAB_USER}/repos/360-visualization/metadata_parser'
results_path = f'/home/{IALAB_USER}/storage/speaker_follower_with_objects/tasks/R2R/speaker/results/'

if matterport_build_path not in sys.path:
    sys.path.append(matterport_build_path)

if metadata_script_path not in sys.path:
    sys.path.append(metadata_script_path)

if results_path not in sys.path:
    sys.path.append(results_path)

from parse_house_segmentations import HouseSegmentationFile
from cualitative_collect import run_human_follower, get_info
import io
import os
import base64

app = Flask(__name__)
app.secret_key = "actually not a secret key"

@app.route("/", methods=["GET"])
def index():
  N = 50
  x = [0.5 for _ in range(4)]
  y = x
  colors = [0.3 for _ in range(4)]
  plt.scatter(x, y, c=colors, alpha=0.5)

  print("yess")

  f = io.BytesIO()
  plt.savefig(f, format="png", facecolor=(0.95, 0.95, 0.95))
  encoded_img = base64.b64encode(f.getvalue()).decode('utf-8').replace('\n', '')
  f.close()

  return render_template("index.html", encoded_img=encoded_img)

@app.route("/experiment", methods=["GET"])
def experiment():
  scan, path_id, viewpoints_sequence, viewpoints_information, initial_heading, instruction_to_eval, metadata = run_human_follower()

  # ### Plot viewpoints and save the data
  curr_viewpoint_name = viewpoints_sequence[0]
  last_viewpoint_name = viewpoints_sequence[-1]
  curr_heading = initial_heading

  session['information'] = {
      'instruction': instruction_to_eval['instruction'],
      'model': instruction_to_eval['model'],
      'scan': scan,
      'path': path_id
  }

  session['path'] = []
  session['path'].append({
      'name': curr_viewpoint_name,
      'heading': curr_heading
  })

  session['reachable_viewpoints_array'], img_data = get_info(
      scan, curr_viewpoint_name, curr_heading, metadata, viewpoints_information
  )

  instruction_string = instruction_to_eval['instruction'].capitalize().replace(' .', '.')

  return render_template("experiment.html", instruction=instruction_string, image_data=img_data)

  next_viewpoint_option = input(f"{instruction_string}\n\n >>> Where you want to go?\n")
  if next_viewpoint_option.lower() == 'stop':
      if curr_viewpoint_name == last_viewpoint_name:
          print("\n🎉 Congrats, you arrived correctly :)\n")
      else:
          print("\n☹️ You didn't reach the goal :(\n")
      print("Thank you for participating in my experiment ❤️")

      if input("\nDo you want to see the final viewpoint? yes/no\n") == 'yes':
          get_info(
              scan, last_viewpoint_name, curr_heading, metadata, viewpoints_information
          )

  next_viewpoint = reachable_viewpoints_array[int(next_viewpoint_option) - 1]

  curr_heading = next_viewpoint.heading
  curr_viewpoint_name = next_viewpoint.name



@app.route("/new_plot", methods=["GET"])
def new_plot():

  information['path'] = path
  information['success'] = result
  information['owner'] = EXPERIMENT_NAME


  def append_record(record):
      with open('/home/jiossandon/storage/speaker_follower_with_objects/cualitative/results.json', 'a') as f:
          json.dump(record, f)
          f.write(os.linesep)

  append_record(information)

  return render_template("index_2.html")

@app.errorhandler(404)
def invalid_route(e):
  return "Invalid route."

if __name__ == "__main__":
  app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 4444)), debug=True)

