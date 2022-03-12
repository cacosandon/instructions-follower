import sys
import json
from flask import Flask, render_template, url_for, flash, request, redirect, make_response, session
from utils import select_options, load_nav_graph
import numpy as np

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
  return render_template("index.html")

@app.route("/experiment", methods=["GET"])
def experiment():
  if "username" in request.args:
    username = request.args["username"]
  else:
    flash('❌  Oops. Please enter an username for navigating')
    return redirect(url_for('index'))


  scan, path_id, viewpoints_sequence, viewpoints_information, \
  initial_heading, instruction_to_eval = run_human_follower()

  metadata = HouseSegmentationFile.load_mapping(scan)
  graph = load_nav_graph(scan)

  # ### Plot viewpoints and save the data
  curr_viewpoint_name = viewpoints_sequence[0]
  last_viewpoint_name = viewpoints_sequence[-1]
  curr_heading = initial_heading

  session['path'] = []

  session['distances'] = dict(nx.all_pairs_dijkstra_path_length(graph))

  session['information'] = {
    'owner': username,
    'instruction': instruction_to_eval['instruction'],
    'viewpoints_information': viewpoints_information,
    'last_viewpoint_name': last_viewpoint_name,
    'model': instruction_to_eval['model'],
    'scan': scan,
    'path': path_id
  }

  session['distance_traveled'] = 0

  session['path'].append({
    'name': curr_viewpoint_name,
    'heading': curr_heading
  })

  session['reachable_viewpoints_array'], image_data = get_info(
    scan, curr_viewpoint_name, curr_heading, metadata, viewpoints_information
  )

  instruction_string = instruction_to_eval['instruction'].capitalize().replace(' .', '.')

  return render_template(
    "experiment.html",
    username=username,
    instruction=instruction_string,
    image_data=image_data,
    options=select_options(len(session['reachable_viewpoints_array']))
  )

@app.route("/new_plot", methods=["GET"])
def new_plot():
  scan = session['information']['scan']
  metadata = HouseSegmentationFile.load_mapping(scan)
  viewpoints_information = session['information']['viewpoints_information']

  if "node" in request.args["action"]:
    next_node_index = int(request.args["action"].split("-")[1])
    next_viewpoint = session["reachable_viewpoints_array"][next_node_index - 1]

    from_point = session['path'][-1]['name']
    to_point = next_viewpoint[4]
    session['distance_traveled'] += session['distances'][from_point][to_point]

    curr_heading = next_viewpoint[3]
    curr_viewpoint_name = next_viewpoint[4]

  if "turn" in request.args["action"]:
    current_viewpoint = session['path'][-1]
    curr_viewpoint_name, curr_heading = current_viewpoint['name'], current_viewpoint['heading']
    curr_heading += { "left": -np.pi / 2, "right": np.pi/2, "around": np.pi }[request.args["action"].split("-")[1]]

  if "stop" in request.args["action"]:
    curr_heading = session['path'][-1]['heading']
    curr_viewpoint_name = session['path'][-1]['name']
    last_viewpoint_name = session['information']['last_viewpoint_name']

    success = curr_viewpoint_name == last_viewpoint_name
    navigation_error = session['distances'][curr_viewpoint_name][last_viewpoint_name]
    path_length = session['distance_traveled']

    distance_from_start_to_end = session['distances'][session['path'][0]['name']][last_viewpoint_name]
    spl = int(success) * distance_from_start_to_end / max(path_length, distance_from_start_to_end)

    def append_record(record):
      with open('/home/jiossandon/storage/instructions-follower/results/results.json', 'a') as f:
              json.dump(record, f)
              f.write(os.linesep)
    information = {
      'instruction': session['information']['instruction'],
      'scan': session['information']['scan'],
      'path_id': session['information']['path'],
      'owner': session['information']['owner'],
      'model': session['information']['model'],
      'path': session['path'],
      'success': success,
      'path_length': path_length,
      'navigation_error': navigation_error,
      'success_path_length': spl
    }

    append_record(information)

    _, image_data = get_info(
      scan, last_viewpoint_name, curr_heading, metadata, viewpoints_information
    )

    return render_template(
      "result.html",
      image_data=image_data,
      success=success,
      username=session['information']['owner']
    )

  session['path'].append({
      'name': curr_viewpoint_name,
      'heading': curr_heading,
      'action': request.args["action"],
      'distance_traveled': session['distance_traveled']
  })

  session['reachable_viewpoints_array'], image_data = get_info(
      scan, curr_viewpoint_name, curr_heading, metadata, viewpoints_information
  )

  return render_template(
      "reload.html",
      image_data=image_data,
      options=select_options(len(session['reachable_viewpoints_array']))
  )

@app.errorhandler(404)
def invalid_route(e):
  return "Invalid route."

if __name__ == "__main__":
  app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 4444)))

